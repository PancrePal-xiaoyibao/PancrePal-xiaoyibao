import path from "path";
import fs from "fs-extra";
import _ from "lodash";
import mime from "mime";
import assert from "assert";
import FormData from "form-data";
import axios, { AxiosResponse } from "axios";
import { getSignature, decrypt } from "@wecom/crypto";

import type IMessage from "@/lib/interfaces/IMessage.ts";
import EX from "@/api/consts/exceptions.ts";
import APIException from "@/lib/exceptions/APIException.ts";
import AsyncLock from "async-lock";
import logger from "@/lib/logger.ts";
import agents from "./agents.ts";
import secret from "./secret.ts";
import util from "@/lib/util.ts";
import IAgentConfig from "./interfaces/IAgentConfig.ts";

const {
    WXKF_API_CORP_ID,
    WXKF_API_CORP_SECRET,
    WXKF_API_TOKEN,
    WXKF_API_ENCODING_AES_KEY
} = secret;

// 文件最大大小
const FILE_MAX_SIZE = 100 * 1024 * 1024;

const lock = new AsyncLock();
const kfAgentMap: Record<string, IAgentConfig> = {};
let accessTokenData: any = null;
let nextCursor: string = fs.existsSync('tmp/message-cursor') ? fs.readFileSync('tmp/message-cursor').toString() : undefined;

function checkSignature(params: any, encryptedData: string) {
    assert(WXKF_API_TOKEN, 'Please set the WXKF_API_TOKEN in secret.yml');
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
    assert(WXKF_API_ENCODING_AES_KEY, 'Please set the WXKF_API_ENCODING_AES_KEY in secret.yml');
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
    assert(WXKF_API_CORP_ID, 'Please set the WXKF_API_CORP_ID in secret.yml');
    assert(WXKF_API_CORP_SECRET, 'Please set the WXKF_API_CORP_SECRET in secret.yml');
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
    })
        .catch(() => logger.warn('获取access_token失败，可能是WXKF_API_CORP_ID或WXKF_API_CORP_SECRET配置错误'));
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
    if(WXKF_API_CORP_ID == 'default' || WXKF_API_CORP_SECRET == 'default') {
        if(WXKF_API_TOKEN == 'default' || WXKF_API_ENCODING_AES_KEY == 'default')
            logger.warn('【STEP1】Token或EncodingAESKey未配置，请从微信客服企业内部接入处生成Token和EncodingAESKey');
        else {
            logger.success('【STEP1】Token或EncodingAESKey已配置');
            logger.warn('【STEP2】微信客服还未完成接入，请从微信客服平台发起回调验证获取企业ID和Secret');
        }
        return;
    }
    else if(WXKF_API_TOKEN == 'default' || WXKF_API_ENCODING_AES_KEY == 'default')
        logger.warn('【STEP1】Token和EncodingAESKey未配置，微信客服还未接入完成，请填写微信客服企业内部接入处的Token和EncodingAESKey');
    logger.info('【初始化微信客服列表】');
    let agentConfigCache: Record<string, IAgentConfig> = {};
    if(await fs.exists('tmp/accounts.json'))
        agentConfigCache = await fs.readJSON('tmp/accounts.json');
    const accountList = await getAccountList();
    for(let agentConfig of agents) {
        if(!agentConfig.avatarUrl)
            agentConfig.avatarUrl = 'https://sfile.chatglm.cn/chatglm4/81a30afa-d5d9-4c9e-9854-dabc64ab2574.png';
        const account = accountList.find(item => item.name == agentConfig.name);
        if(!account) {
            logger.info(` - 创建客服 ${agentConfig.name} 中...`);
            const avatarMediaId = await transferMedia('image', agentConfig.avatarUrl)
            const openKfId = await createAccount(agentConfig.name, avatarMediaId);
            agentConfigCache[agentConfig.id] = {
                ...agentConfig,
                openKfId
            };
            logger.success(` - 创建客服 ${agentConfig.name} 成功，链接：${agentConfigCache[agentConfig.id].contactUrl}`);
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
        agentConfigCache[agentConfig.id].enabled = agentConfig.enabled;
        if(!agentConfigCache[agentConfig.id].contactUrl)
            agentConfigCache[agentConfig.id].contactUrl = await createAccountContactUrl(agentConfigCache[agentConfig.id].openKfId);
        if(account.name == agentConfig.name && agentConfig.name == agentConfigCache[agentConfig.id].name && agentConfig.avatarUrl == agentConfigCache[agentConfig.id].avatarUrl) {
            const supported_api = ['qingyan-glms-api', 'qingyan-glms-free-api', 'openai-api'];
            if(supported_api.includes(agentConfig.api)) {
                if(agentConfig.enabled)
                    logger.info(` - 客服 ${agentConfig.name} 已加载，链接：${agentConfigCache[agentConfig.id].contactUrl}`);
                else
                    logger.warn(` - 客服 ${agentConfig.name} 已禁用`);
            }
            else {
                agentConfigCache[agentConfig.id].enabled = false;
                logger.warn(` - 客服 ${agentConfig.name} 似乎使用了不受支持的API【${agentConfig.api}】而被禁用，支持列表：${supported_api.join(' | ')}。`);
            }
            continue;
        }
        logger.info(` - 更新客服 ${agentConfig.name} 中...`);
        const avatarMediaId = await transferMedia('image', agentConfig.avatarUrl);
        await updateAccount(account.open_kfid, agentConfig.name, avatarMediaId);
        agentConfigCache[agentConfig.id].name = agentConfig.name;
        agentConfigCache[agentConfig.id].avatarUrl = agentConfig.avatarUrl;
        logger.success(` - 客服 ${agentConfig.name} 已更新，链接：${agentConfigCache[agentConfig.id].contactUrl}`);
    }
    await fs.writeJSON('tmp/accounts.json', agentConfigCache);
    for(let key in agentConfigCache)
        kfAgentMap[agentConfigCache[key].openKfId] = agentConfigCache[key];
    logger.info('【微信客服列表初始化完成】');
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

async function createAccountContactUrl(openKfId: string, scene?: string) {
    const result = await axios.post('https://qyapi.weixin.qq.com/cgi-bin/kf/add_contact_way', {
        open_kfid: openKfId,
        scene
    }, {
        params: {
            access_token: await getAccessToken()
        }
    });
    const { url } = checkResult(result);
    return url;
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
    createAccountContactUrl,
    createAccount,
    updateAccount,
    deleteAccount
};