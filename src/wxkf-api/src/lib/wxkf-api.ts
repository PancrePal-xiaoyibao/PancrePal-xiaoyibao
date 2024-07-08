import path from "path";
import fs from "fs-extra";
import _ from "lodash";
import mime from "mime";
import assert from "assert";
import yaml from 'yaml';
import FormData from "form-data";
import axios, { AxiosResponse } from "axios";
import { getSignature, decrypt } from "@wecom/crypto";

import type IMessage from "@/lib/interfaces/IMessage.ts";
import environment from "@/lib/environment.ts";
import EX from "@/api/consts/exceptions.ts";
import APIException from "@/lib/exceptions/APIException.ts";
import AsyncLock from "async-lock";
import logger from "@/lib/logger.ts";
import util from "@/lib/util.ts";
import IAgentConfig from "./interfaces/IAgentConfig.ts";

const WXKF_API_CORP_ID = environment.envVars["WXKF_API_CORP_ID"];
const WXKF_API_CORP_SECRET = environment.envVars["WXKF_API_CORP_SECRET"];
const WXKF_API_TOKEN = environment.envVars["WXKF_API_TOKEN"];
const WXKF_API_ENCODING_AES_KEY =
    environment.envVars["WXKF_API_ENCODING_AES_KEY"];
// 文件最大大小
const FILE_MAX_SIZE = 100 * 1024 * 1024;

const lock = new AsyncLock();
const kfAgentMap: Record<string, IAgentConfig> = {};
let accessTokenData: any = null;
let nextCursor: string = fs.existsSync('tmp/message-cursor') ? fs.readFileSync('tmp/message-cursor').toString() : undefined;

function checkSignature(params: any, encryptedData: string) {
    assert(WXKF_API_TOKEN, 'Please set the environment variable WXKF_API_TOKEN');
    const signature = getSignature(
        WXKF_API_TOKEN,
        params.timestamp,
        params.nonce,
        encryptedData
    );
    if (params.msg_signature != signature)
        throw new APIException(EX.API_WECHAT_SIGNATURE_INVALID);
}

function decryptData(encryptedData: string): { message: string, id: string, random: Buffer } {
    assert(WXKF_API_ENCODING_AES_KEY, 'Please set the environment variable WXKF_API_ENCODING_AES_KEY');
    return decrypt(WXKF_API_ENCODING_AES_KEY, encryptedData);
}

function parseMessage(msg: string) {
    const { xml } = util.parseXML(msg);
    if (!xml) throw new Error("消息不完整");
    const {
        ToUserName: toUserName,
        MsgType: msgType,
        Event: event,
        Token: token,
        OpenKfId: openKfId,
        CreateTime: createTime,
    } = xml;
    return {
        toUserName,
        msgType,
        event,
        token,
        openKfId,
        createTime,
    };
}

async function getAccessToken() {
    assert(WXKF_API_CORP_ID, 'Please set the environment variable WXKF_API_CORP_ID');
    assert(WXKF_API_CORP_SECRET, 'Please set the environment variable WXKF_API_CORP_SECRET');
    return await lock.acquire('getAccessToken', async () => {
        const filePath = 'tmp/access-token.json';
        if (!accessTokenData && await fs.exists(filePath))
            accessTokenData = await fs.readJSON(filePath);
        if (accessTokenData && util.unixTimestamp() < accessTokenData.expireTime)
            return accessTokenData.accessToken;
        const result = await axios.get(`https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=${WXKF_API_CORP_ID}&corpsecret=${WXKF_API_CORP_SECRET}`, {
            validateStatus: () => true,
        });
        const {
            access_token: accessToken,
            expires_in: expires
        } = checkResult(result);
        accessTokenData = {
            accessToken,
            expireTime: util.unixTimestamp() + expires - 300
        };
        await fs.writeJSON(filePath, accessTokenData);
        return accessToken;
    });
}

async function downloadMedia(mediaId: string) {
    const result = await axios.get('https://qyapi.weixin.qq.com/cgi-bin/media/get', {
        params: {
            access_token: await getAccessToken(),
            media_id: mediaId
        },
        // 100M限制
        maxContentLength: FILE_MAX_SIZE,
        // 60秒超时
        timeout: 60000,
        responseType: 'arraybuffer'
    });
    return {
        contentType: result.headers['content-type'],
        data: result.data as Buffer
    };
}

async function transferMedia(type: 'image' | 'voice' | 'video' | 'file', fileUrl: string) {
    // 预检查远程文件URL可用性
    await checkFileUrl(fileUrl);

    let filename, fileData, mimeType;
    // 如果是BASE64数据则直接转换为Buffer
    if (util.isBASE64Data(fileUrl)) {
        mimeType = util.extractBASE64DataFormat(fileUrl);
        const ext = mime.getExtension(mimeType);
        filename = `${util.uuid()}.${ext}`;
        fileData = Buffer.from(util.removeBASE64DataHeader(fileUrl), "base64");
    }
    // 下载文件到内存，如果您的服务器内存很小，建议考虑改造为流直传到下一个接口上，避免停留占用内存
    else {
        filename = path.basename(fileUrl);
        ({ data: fileData } = await axios.get(fileUrl, {
            responseType: "arraybuffer",
            // 100M限制
            maxContentLength: FILE_MAX_SIZE,
            // 60秒超时
            timeout: 60000,
        }));
    }
    return await uploadMedia(type, filename, fileData);
}

async function uploadMedia(type: 'image' | 'voice' | 'video' | 'file', filename: string, fileData: Buffer): Promise<string> {
    // 获取文件的MIME类型
    const mimeType = mime.getType(filename);
    const formData = new FormData();
    formData.append("file", fileData, {
        filename,
        contentType: mimeType,
    });
    const result = await axios.post('https://qyapi.weixin.qq.com/cgi-bin/media/upload', formData, {
        params: {
            access_token: await getAccessToken(),
            type
        },
        // 100M限制
        maxBodyLength: FILE_MAX_SIZE,
        // 120秒超时
        timeout: 120000,
        headers: formData.getHeaders(),
        validateStatus: () => true
    });
    const { media_id: mediaId } = checkResult(result);
    return mediaId;
}

async function initAccountList() {
    !WXKF_API_CORP_ID && logger.warn('Please set the environment variable WXKF_API_CORP_ID');
    !WXKF_API_CORP_SECRET && logger.warn('Please set the environment variable WXKF_API_CORP_SECRET');
    !WXKF_API_TOKEN && logger.warn('Please set the environment variable WXKF_API_TOKEN');
    !WXKF_API_ENCODING_AES_KEY && logger.warn('Please set the environment variable WXKF_API_ENCODING_AES_KEY');
    if(!WXKF_API_CORP_ID || !WXKF_API_CORP_SECRET || !WXKF_API_TOKEN || !WXKF_API_ENCODING_AES_KEY) {
        logger.warn('【服务尚未工作，请按照以下流程配置】');
        logger.warn('请先前往 https://kf.weixin.qq.com/kf 登录并启用企业内部接入配置');
        logger.warn('回调地址：https://example.com/message/notify (example.com请改为您的域名)');
        logger.warn('完成配置后，你会获得Token、EncodingAESKey、企业ID(CorpId)、Secret');
        logger.warn('将它们分别设置到环境变量 WXKF_API_TOKEN、WXKF_API_ENCODING_AES_KEY、WXKF_API_CORP_ID、WXKF_API_CORP_SECRET 后重启服务即可');
        return;
    }
    logger.info('Init account list');
    const agentConfigs: IAgentConfig[] = yaml.parse((await fs.readFile('agents.yml')).toString());
    let agentConfigCache: Record<string, IAgentConfig> = {};
    if(await fs.exists('tmp/accounts.json'))
        agentConfigCache = await fs.readJSON('tmp/accounts.json');
    const accountList = await getAccountList();
    for(let agentConfig of agentConfigs) {
        const account = accountList.find(item => item.name == agentConfig.name);
        if(!account) {
            const avatarMediaId = await transferMedia('image', agentConfig.avatarUrl)
            const openKfId = await createAccount(agentConfig.name, avatarMediaId);
            agentConfigCache[agentConfig.id] = {
                ...agentConfig,
                openKfId
            };
            logger.success(`Create account ${agentConfig.name} success`);
            continue;
        }
        else if(!agentConfigCache[agentConfig.id]) {
            agentConfigCache[agentConfig.id] = agentConfig;
            agentConfigCache[agentConfig.id].openKfId = account.open_kfid;
        }
        agentConfigCache[agentConfig.id].welcome = agentConfig.welcome;
        agentConfigCache[agentConfig.id].api = agentConfig.api;
        agentConfigCache[agentConfig.id].apiKey = agentConfig.apiKey;
        agentConfigCache[agentConfig.id].maxRounds = agentConfig.maxRounds;
        if(account.name == agentConfig.name && agentConfig.name == agentConfigCache[agentConfig.id].name && agentConfig.avatarUrl == agentConfigCache[agentConfig.id].avatarUrl) {
            logger.info(`Account ${agentConfig.name} loaded`);
            continue;
        }
        const avatarMediaId = await transferMedia('image', agentConfig.avatarUrl);
        await updateAccount(account.open_kfid, agentConfig.name, avatarMediaId);
        agentConfigCache[agentConfig.id].name = agentConfig.name;
        agentConfigCache[agentConfig.id].avatarUrl = agentConfig.avatarUrl;
        logger.success(`Account ${agentConfig.name} upaded`);
    }
    await fs.writeJSON('tmp/accounts.json', agentConfigCache);
    for(let key in agentConfigCache)
        kfAgentMap[agentConfigCache[key].openKfId] = agentConfigCache[key];
}

function getAgentConfig(openKfId: string) {
    const agentConfig = kfAgentMap[openKfId];
    if(!agentConfig)
        throw new Error(`Agent ${openKfId} not found`);
    return agentConfig;
}

async function getAccountList(pageNumber = 1, pageSize = 100) {
    const result = await axios.post('https://qyapi.weixin.qq.com/cgi-bin/kf/account/list', {
        offset: (pageNumber - 1) * pageSize,
        limit: pageSize
    }, {
        params: {
            access_token: await getAccessToken()
        }
    });
    const { account_list: accountList } = checkResult(result);
    return accountList;
}

async function createAccount(name: string, avatarMediaId: string): Promise<string> {
    const result = await axios.post('https://qyapi.weixin.qq.com/cgi-bin/kf/account/add', {
        name,
        media_id: avatarMediaId
    }, {
        params: {
            access_token: await getAccessToken()
        }
    });
    const { open_kfid: openKfId } = checkResult(result);
    return openKfId;
}

async function updateAccount(openKfId: string, name: string, avatarMediaId?: string) {
    const result = await axios.post('https://qyapi.weixin.qq.com/cgi-bin/kf/account/update', {
        open_kfid: openKfId,
        name,
        media_id: avatarMediaId
    }, {
        params: {
            access_token: await getAccessToken()
        }
    });
    checkResult(result);
}

async function deleteAccount(openKfId: string) {
    const result = await axios.post('https://qyapi.weixin.qq.com/cgi-bin/kf/account/del', {
        open_kfid: openKfId
    }, {
        params: {
            access_token: await getAccessToken()
        }
    });
    checkResult(result);
}

async function sendTextMessage(content: string, userId: string, openKfId: string) {
    content = content.replace(/\!?\[.+\]\(.+[jpg|jpeg|png|gif]\)/g, "").trim();
    if (!content)
        return;
    const result = await axios.post('https://qyapi.weixin.qq.com/cgi-bin/kf/send_msg', {
        touser: userId,
        open_kfid: openKfId,
        msgid: util.uuid(false),
        msgtype: 'text',
        text: {
            content
        }
    }, {
        params: {
            access_token: await getAccessToken()
        }
    });
    checkResult(result);
}

async function sendImageMessage(mediaId: string, userId: string, openKfId: string) {
    const result = await axios.post('https://qyapi.weixin.qq.com/cgi-bin/kf/send_msg', {
        touser: userId,
        open_kfid: openKfId,
        msgid: util.uuid(false),
        msgtype: 'image',
        image: {
            media_id: mediaId
        }
    }, {
        params: {
            access_token: await getAccessToken()
        }
    });
    checkResult(result);
}

async function sendWelcomeMessage(content: string, code: string) {
    content = content.replace(/\!?\[.+\]\(.+[jpg|jpeg|png|gif]\)/g, "").trim();
    if (!content)
        return;
    const result = await axios.post('https://qyapi.weixin.qq.com/cgi-bin/kf/send_msg_on_event', {
        code,
        msgid: util.uuid(false),
        msgtype: 'text',
        text: {
            content
        }
    }, {
        params: {
            access_token: await getAccessToken()
        }
    });
    checkResult(result);
}

async function sendMenuMessage(content: string, code: string, title: string, options: any[]) {
    content = content.replace(/\!?\[.+\]\(.+[jpg|jpeg|png|gif]\)/g, "").trim();
    if (!content)
        return;
    const result = await axios.post('https://qyapi.weixin.qq.com/cgi-bin/kf/send_msg_on_event', {
        code,
        msgid: util.uuid(false),
        msgtype: 'msgmenu',
        msgmenu: {
            head_content: title,
            list: options
        }
    }, {
        params: {
            access_token: await getAccessToken()
        }
    });
    checkResult(result);
}

async function pullMessageList(token: string) {
    const pull = async (cursor?: string): Promise<IMessage[]> => {
        const result = await axios.post('https://qyapi.weixin.qq.com/cgi-bin/kf/sync_msg', {
            cursor,
            token
        }, {
            params: {
                access_token: await getAccessToken()
            }
        });
        const {
            next_cursor,
            has_more,
            msg_list
        } = checkResult(result);
        let msgList = cursor ? msg_list : msg_list.slice(msg_list.length - 1, msg_list.length);
        nextCursor = next_cursor;
        await fs.writeFile('tmp/message-cursor', nextCursor);
        if (has_more)
            msgList = msgList.concat(await pull(next_cursor));
        return msgList;
    }
    return await pull(nextCursor);
}

function checkResult(result: AxiosResponse) {
    if (!result.data) return null;
    const { errcode, errmsg, ..._result } = result.data;
    if (!_.isFinite(errcode)) return result.data;
    if (errcode === 0) return _result;
    if (errcode === 40014) {
        fs.removeSync('tmp/access-token.json');
        accessTokenData = null;
    }
    throw new APIException(EX.API_REQUEST_FAILED, `[请求失败]: ${errcode} - ${errmsg}`);
}

/**
 * 预检查文件URL有效性
 *
 * @param fileUrl 文件URL
 */
async function checkFileUrl(fileUrl: string) {
    if (util.isBASE64Data(fileUrl)) return;
    const result = await axios.head(fileUrl, {
        timeout: 15000,
        validateStatus: () => true,
    });
    if (result.status >= 400)
        throw new APIException(
            EX.API_FILE_URL_INVALID,
            `File ${fileUrl} is not valid: [${result.status}] ${result.statusText}`
        );
    // 检查文件大小
    if (result.headers && result.headers["content-length"]) {
        const fileSize = parseInt(result.headers["content-length"], 10);
        if (fileSize > FILE_MAX_SIZE)
            throw new APIException(
                EX.API_FILE_EXECEEDS_SIZE,
                `File ${fileUrl} is not valid`
            );
    }
}

export default {
    initAccountList,
    getAgentConfig,
    checkSignature,
    decryptData,
    parseMessage,
    transferMedia,
    uploadMedia,
    downloadMedia,
    sendTextMessage,
    sendImageMessage,
    sendWelcomeMessage,
    sendMenuMessage,
    pullMessageList,
    getAccessToken,
    getAccountList,
    createAccount,
    updateAccount,
    deleteAccount
};