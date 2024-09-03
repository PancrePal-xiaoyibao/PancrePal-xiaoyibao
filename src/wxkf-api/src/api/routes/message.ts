import _ from 'lodash';

import Request from '@/lib/request/Request.ts';
import message from '@/api/controllers/message.ts';
import wxkfApi from '@/lib/wxkf-api.ts';

export default {

    prefix: '/message',

    get: {

        '/notify': async (request: Request) => {
            request
                .validate('query.msg_signature')
                .validate('query.timestamp')
                .validate('query.nonce')
                .validate('query.echostr');
            const query = request.query;
            wxkfApi.checkSignature(query, query.echostr);
            const { message: msg } = wxkfApi.decryptData(query.echostr);
            return msg;
        }

    },

    post: {

        '/notify': async (request: Request) => {
            request
                .validate('query.msg_signature')
                .validate('query.timestamp')
                .validate('query.nonce')
                .validate('body.xml');
            const query = request.query;
            const params = request.body.xml;
            const {
                ToUserName: toUserName,
                Encrypt: encryptedData,
                AgentID: agentId
            } = params;
            wxkfApi.checkSignature(query, encryptedData);
            const {
                message: msg
            } = wxkfApi.decryptData(encryptedData);
            const { token } = wxkfApi.parseMessage(msg);
            const handlePromises = [];
            for(let msg of await message.getMessageList(token))
                handlePromises.push(message.handleMessge(msg));
            await Promise.all(handlePromises);
            return {}
        }

    }

}