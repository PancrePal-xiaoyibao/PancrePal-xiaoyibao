import _ from "lodash";
import { fileTypeFromBuffer } from 'file-type';

import type IMessage from "./interfaces/IMessage.ts";
import type ICompletionMessage from "./interfaces/ICompletionMessage.ts";
import type IMedia from "./interfaces/IMedia.ts";
import EX from "@/api/consts/exceptions.ts";
import wxkfApi from "@/lib/wxkf-api.ts";
import qingyanGlmsFreeApi from '@/lib/qingyan-glms-free-api.ts';
import qingyanGlmsApi from "@/lib/qingyan-glms-api.ts";
import APIException from "@/lib/exceptions/APIException.ts";
import logger from "@/lib/logger.ts";
import util from "@/lib/util.ts";

const API_MAP = {
    'qingyan-glms-api': qingyanGlmsApi,
    'qingyan-glms-free-api': qingyanGlmsFreeApi,
};

const msgStore = {};
const userConvIdStore = {};
const userMediaStore = {};

async function generateAssistantReply(messages: ICompletionMessage[], userId: string, openKfId: string) {
    const agentConfig = wxkfApi.getAgentConfig(openKfId);
    if (!agentConfig.enabled)
        throw new APIException(EX.API_AGENT_IS_DISABLED);
    if (!API_MAP[agentConfig.api])
        throw new Error(`Agent API ${agentConfig.api} not found`);
    const apiKeys = agentConfig.apiKey.split(",");
    const latestConvId = getUserLatestConvId(userId, openKfId, agentConfig.maxRounds);
    const result = await API_MAP[agentConfig.api].createCompletion(agentConfig.id, messages, _.sample(apiKeys), latestConvId);
    setUserLatestConvId(result.id, userId, openKfId);
    const reply = result.choices[0].message.content || '';
    addMessageToUserMessageList({
        msgtype: 'text',
        msgid: '',
        send_role: 'assistant',
        open_kfid: openKfId,
        external_userid: userId,
        send_time: util.unixTimestamp(),
        origin: 3,
        text: {
            content: reply
        }
    }, userId, openKfId);
    return reply;
}

function setUserLatestConvId(convId: string, userId: string, openKfId: string) {
    if (!userConvIdStore[openKfId])
        userConvIdStore[openKfId] = {};
    if (!userConvIdStore[openKfId][userId])
        userConvIdStore[openKfId][userId] = {};
    userConvIdStore[openKfId][userId].convId = convId;
    if (!_.isFinite(userConvIdStore[openKfId][userId].rounds))
        userConvIdStore[openKfId][userId].rounds = 0;
    userConvIdStore[openKfId][userId].rounds++;
}

function getUserLatestConvId(userId: string, openKfId: string, maxRounds = 8) {
    if (!userConvIdStore[openKfId] || !userConvIdStore[openKfId][userId])
        return null;
    const { convId, rounds } = userConvIdStore[openKfId][userId];
    if (rounds > maxRounds)
        return null;
    return convId;
}

function addUserMedia(media: IMedia, userId: string, openKfId: string) {
    if (!userMediaStore[openKfId])
        userMediaStore[openKfId] = {};
    if (!userMediaStore[openKfId][userId])
        userMediaStore[openKfId][userId] = [];
    if (userMediaStore[openKfId][userId].length >= 10)
        userMediaStore[openKfId][userId].shift();
    userMediaStore[openKfId][userId].push(media);
}

function getUserMediaList(userId: string, openKfId: string): IMedia[] {
    if (!userMediaStore[openKfId] || !userMediaStore[openKfId][userId])
        return [];
    return userMediaStore[openKfId][userId];
}

function clearUserMediaList(userId: string, openKfId: string) {
    if (!userMediaStore[openKfId] || !userMediaStore[openKfId][userId])
        return;
    delete userMediaStore[openKfId][userId];
}

async function getMessageList(token: string) {
    const msgList = await wxkfApi.pullMessageList(token);
    for (let msg of msgList) {
        if (!msgStore[msg.external_userid])
            msgStore[msg.external_userid] = {};
        if (!msgStore[msg.external_userid][msg.open_kfid])
            msgStore[msg.external_userid][msg.open_kfid] = [];
        if (msgStore[msg.external_userid][msg.open_kfid].length > 50)
            msgStore[msg.external_userid][msg.open_kfid].shift();
        msg.send_role = 'user';
        msgStore[msg.external_userid][msg.open_kfid].push(msg);
    }
    return msgList;
}

function getUserMessageList(userId: string, openKfId: string, count = 8): IMessage[] {
    if (!msgStore[userId] || !msgStore[userId][openKfId])
        return [];
    const messageList = msgStore[userId][openKfId] || [];
    return messageList.slice(messageList.length - count, messageList.length);
}

function addMessageToUserMessageList(message: IMessage, userId: string, openKfId: string) {
    if (!msgStore[userId])
        msgStore[userId] = {};
    if (!msgStore[userId][openKfId])
        msgStore[userId][openKfId] = [];
    msgStore[userId][openKfId].push(message);
}

async function handleEventMessage(event: IMessage['event']) {
    const agentConfig = wxkfApi.getAgentConfig(event.open_kfid);
    if (event.event_type == 'enter_session') {
        if (!agentConfig.welcome || !event.welcome_code)
            return;
        await wxkfApi.sendWelcomeMessage(agentConfig.welcome, event.welcome_code);
    }
    else if (event.event_type == 'msg_send_fail') {
        await wxkfApi.sendTextMessage('咱们换个话题聊聊吧！', event.external_userid, event.open_kfid);
    }
}

async function handleTextMessage(text: IMessage['text'], userId: string, openKfId: string) {
    // const agentConfig = wxkfApi.getAgentConfig(openKfId);
    // const messageList = getUserMessageList(userId, openKfId, agentConfig.maxRounds || 8);
    // const messages: ICompletionMessage[] = messageList.filter(msg => msg.msgtype == 'text').map(msg => ({
    //     role: msg.send_role,
    //     content: msg.text.content
    // }));
    // const reply = await generateAssistantReply(messages, userId, openKfId);
    if (text.content.indexOf('#清空') != -1) {
        if (msgStore[openKfId] && msgStore[openKfId][userId])
            msgStore[openKfId][userId] = [];
        if (userConvIdStore[openKfId] && userConvIdStore[openKfId][userId])
            delete userConvIdStore[openKfId][userId];
        clearUserMediaList(userId, openKfId);
        await wxkfApi.sendTextMessage('已经清空对话~', userId, openKfId)
        return;
    }
    const mediaList = getUserMediaList(userId, openKfId);
    let messages = [];
    if(mediaList.length > 0) {
        const files = [];
        for(let media of mediaList) {
            const {
                contentType,
                data
            } = await media.promise;
            files.push({
                type: 'file',
                file_url: {
                    url: `data:${contentType};base64,${data.toString('base64')}`
                }
            });
        }
        messages.push({
            role: 'user',
            content: [
                ...files,
                {
                    type: 'text',
                    text: text
                }
            ]
        });
    }
    else {
        messages.push({
            role: 'user',
            content: text.content
        });
    }
    clearUserMediaList(userId, openKfId);
    logger.info(`[User] ${messages[messages.length - 1].content}`);
    const reply = await generateAssistantReply(messages, userId, openKfId);
    logger.info(`[Assistant] ${reply}`);
    const imageUrls = [];
    const urlPattern = /\((https?:\/\/\S+)\)/g;
    let match;
    while ((match = urlPattern.exec(reply)) !== null) {
        const url = match[1];
        if (imageUrls.indexOf(url) == -1)
            imageUrls.push(url);
    }
    const promises = [wxkfApi.sendTextMessage(reply, userId, openKfId)];
    for (let imageUrl of _.uniq(imageUrls)) {
        promises.push((async (url: string) => {
            const mediaId = await wxkfApi.transferMedia('image', url);
            await wxkfApi.sendImageMessage(mediaId, userId, openKfId);
        })(imageUrl));
    }
    await Promise.all(promises);
}

async function handleImageMessage(image: IMessage['image'], userId: string, openKfId: string) {
    // const agentConfig = wxkfApi.getAgentConfig(openKfId);
    // const messageList = getUserMessageList(userId, openKfId, agentConfig.maxRounds || 8);
    // const messages: ICompletionMessage[] = [];
    addUserMedia({
        type: 'image',
        promise: wxkfApi.downloadMedia(image.media_id)
    }, userId, openKfId);
    await wxkfApi.sendTextMessage(`收到！需要我做些什么呢？`, userId, openKfId);
    // const reply = await generateAssistantReply([
    //     {
    //         role: 'user',
    //         content: [
    //             {
    //                 "type": "file",
    //                 "file_url": {
    //                     "url": `data:${contentType};base64,${data.toString('base64')}`
    //                 }
    //             },
    //             {
    //                 "type": "text",
    //                 "text": "请描述图像的内容"
    //             }
    //         ]
    //     }
    // ], userId, openKfId);
    // console.log(reply);
    // const imageUrls = [];
    // const urlPattern = /\((https?:\/\/\S+)\)/g;
    // let match;
    // while ((match = urlPattern.exec(reply)) !== null) {
    //     const url = match[1];
    //     if (imageUrls.indexOf(url) == -1)
    //     imageUrls.push(url);
    // }
    // const promises = [wxkfApi.sendTextMessage(reply, userId, openKfId)];
    // for(let imageUrl of _.uniq(imageUrls)) {
    //     promises.push((async (url: string) => {
    //         const mediaId = await wxkfApi.transferMedia('image', url);
    //         await wxkfApi.sendImageMessage(mediaId, userId, openKfId);
    //     })(imageUrl));
    // }
    // await Promise.all(promises);
    
}

async function handleFileMessage(file: IMessage['file'], userId: string, openKfId: string) {
    addUserMedia({
        type: 'file',
        promise: (async () => {
            const { data } = await wxkfApi.downloadMedia(file.media_id);
            const { mime } = await fileTypeFromBuffer(data);
            return { contentType: mime, data }
        })()
    }, userId, openKfId);
}

async function handleMessge(msg: IMessage) {
    const {
        external_userid: userId,
        open_kfid: openKfId
    } = msg;
    await (async () => {
        switch (msg.msgtype) {
            case 'event':
                await handleEventMessage(msg.event);
                break;
            case 'text':
                await handleTextMessage(msg.text, userId, openKfId);
                break;
            case 'image':
                await handleImageMessage(msg.image, userId, openKfId);
                break;
            case 'file':
                await handleFileMessage(msg.file, userId, openKfId);
                break;
        }
    })()
        .catch(err => {
            logger.error(err);
            let message = '哎呀，发生了点意外，请稍候重试T^T';
            if((err instanceof APIException) && err.compare(EX.API_AGENT_IS_DISABLED))
                message = '抱歉，智能体当前已下线，暂时无法为您提供服务T^T';
            wxkfApi.sendTextMessage(message, userId, openKfId)
                .catch(err => logger.error(err));
        });
}

export default {
    getMessageList,
    getUserMessageList,
    generateAssistantReply,
    handleMessge
};
