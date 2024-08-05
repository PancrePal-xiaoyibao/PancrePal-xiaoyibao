# encoding:utf-8

"""
wechat channel
"""

import io
import json
import os
import threading
import time
import datetime
import random

import requests

from bridge.context import *
from bridge.reply import *
from channel.chat_channel import ChatChannel
from channel import chat_channel
from channel.wechat.wechat_message import *
from common.expired_dict import ExpiredDict
from common.log import logger
from common.singleton import singleton
from common.time_check import time_checker
from config import conf, get_appdata_dir
from lib import itchat
from lib.itchat.content import *

import openai
import re
# import os #sam修改

group_id ="填写在minimax账号的group_id"
api_key="填写minimax申请的apikey"
openai.api_key = "" #可以不填写
openai.api_base = "" #可以不填写

def replace_markdown_urls(text, replacement):
    # 正则表达式匹配Markdown中的URL
    # 这个正则表达式会匹配形如 [text](url) 的Markdown链接
    # url_pattern = r'\!\[([^\]]+)\]\(([^)]+)\)\n*'
    url_pattern = r'\[bot\]'
    # 使用re.sub函数来替换所有匹配的URL
    replaced_text = re.sub(url_pattern, replacement, text)
    return replaced_text

def text_to_voice(text):
    try:
        # lines = text.split('\n')
        # lines.pop(0)
        # text = '\n'.join(lines)
        # text= replace_markdown_urls(text, "") #sam添加，没有什么用
        url = f"https://api.minimax.chat/v1/t2a_pro?GroupId={group_id}"
        headers = {
            "Authorization": f"Bearer {api_key}",
            'Content-Type': 'application/json'
        }
        data = {
            "voice_id": "male-qn-qingse",
            "text": text,
            # 如同时传入voice_id和timber_weights时，则会自动忽略voice_id，以timber_weights传递的参数为准
            # "text":"您好，根据您提供的信息，您正在寻找乳腺癌的指南。乳腺癌是一种常见的癌症类型，通常有专门的指南和治疗建议。对于乳腺癌的相关信息，您可以访问国家综合癌症网络（NCCN）的网站，那里提供了多种癌症类型的指南，包括乳腺癌。NCCN的指南是为医疗专业人员和患者提供的，包含了关于诊断、治疗和患者支持的详细信息。此外，您也可以咨询专业的医疗人员，如肿瘤科医生，以获取针对您具体情况的专业意见和治疗建议。请注意，本回答仅供参考，具体的医疗建议和治疗方案应由专业医疗人员根据您的个人情况制定。**【风险提示：本公益项目使用 AI 技术提供信息，可能存在偏差。一切治疗和判断应以主治医生和患者及其家属意见为准。如果您认为信息偏差会影响您的治疗，请勿使用本工具和内容。本项目已事先告知，不承担任何使用风险。】**",
            "model": "speech-01",
            "speed": 1.0,
            "vol": 1.0,
            "pitch": 0,
            # "model": "speech-02", #备用
            "speed": 1.0, #2.0用参数
            "vol": 1.0,
            "pitch": 0,
            "audio_sample_rate": 24000,
            # The above code is a Python comment that includes a key-value pair related to audio
            # sample rate. The key is "audio_sample_rate" and the value is 24000. Comments in Python
            # are used to provide explanations or annotations within the code and are not executed by
            # the Python interpreter.
            "bitrate": 128000
            # "timber_weights": [
            #     {
            #         "voice_id": "male-qn-qingse",
            #         "weight": 1
                # }
                # {
                #     "voice_id": "female-shaonv",
                #     "weight": 1
                # },
                # {
                #     "voice_id": "female-yujie",
                #     "weight": 1
                # },
                # {
                #     "voice_id": "audiobook_male_2",
                #     "weight": 1
            #    ]
            }    
#sam尝试T2A pro提取url修改的部分
        response = requests.post(url, headers=headers, json=data)
        data = response.json()
        audio_url=data["audio_file"]
        mp3_response = requests.get(audio_url, stream=True)
        if mp3_response.status_code== 200:
            file_name = "tmp/" + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + str(random.randint(0, 1000)) + ".mp3"
            logger.debug(f"[OPENAI] text_to_Voice file_name={file_name}, input={text}") 
            with open(file_name, 'wb') as f:
               for chunk in mp3_response.iter_content(1024):
                   f.write(chunk) 
            # output_file_path = os.path.abspath(file_name)
            # print(f"文件路径: {output_file_path} \n复制并粘贴到文件管理器或浏览器中打开:")
            # subprocess.run(["open", "-W", output_file_path])
            reply = Reply(ReplyType.VOICE, file_name) 
        else:
            print(f"Failed to download audio, status code: {response.status_code}")
#可以配合T2A的接口代码        
        # response = requests.post(url, headers=headers, json=data)
        # file_name = "tmp/" + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + str(random.randint(0, 1000)) + ".mp3"
        # logger.debug(f"[OPENAI] text_to_Voice file_name={file_name}, input={text}")
        # with open(file_name, 'wb') as f:
        #     f.write(response.content)
        # logger.info(f"[OPENAI] text_to_Voice success")
        # reply = Reply(ReplyType.VOICE, file_name)

    except Exception as e:
        logger.error(e)
        reply = Reply(ReplyType.ERROR, "遇到了一点小问题，请稍后再问我吧")
    return reply

@itchat.msg_register([TEXT, VOICE, PICTURE, NOTE, ATTACHMENT, SHARING])
def handler_single_msg(msg):
    try:
        cmsg = WechatMessage(msg, False)
    except NotImplementedError as e:
        logger.debug("[WX]single message {} skipped: {}".format(msg["MsgId"], e))
        return None
    WechatChannel().handle_single(cmsg)
    return None


@itchat.msg_register([TEXT, VOICE, PICTURE, NOTE, ATTACHMENT, SHARING], isGroupChat=True)
def handler_group_msg(msg):
    try:
        cmsg = WechatMessage(msg, True)
    except NotImplementedError as e:
        logger.debug("[WX]group message {} skipped: {}".format(msg["MsgId"], e))
        return None
    WechatChannel().handle_group(cmsg)
    return None


def _check(func):
    def wrapper(self, cmsg: ChatMessage):
        msgId = cmsg.msg_id
        if msgId in self.receivedMsgs:
            logger.info("Wechat message {} already received, ignore".format(msgId))
            return
        self.receivedMsgs[msgId] = True
        create_time = cmsg.create_time  # 消息时间戳
        if conf().get("hot_reload") == True and int(create_time) < int(time.time()) - 60:  # 跳过1分钟前的历史消息
            logger.debug("[WX]history message {} skipped".format(msgId))
            return
        if cmsg.my_msg and not cmsg.is_group:
            logger.debug("[WX]my message {} skipped".format(msgId))
            return
        return func(self, cmsg)

    return wrapper


# 可用的二维码生成接口
# https://api.qrserver.com/v1/create-qr-code/?size=400×400&data=https://www.abc.com
# https://api.isoyu.com/qr/?m=1&e=L&p=20&url=https://www.abc.com
def qrCallback(uuid, status, qrcode):
    # logger.debug("qrCallback: {} {}".format(uuid,status))
    if status == "0":
        try:
            from PIL import Image

            img = Image.open(io.BytesIO(qrcode))
            _thread = threading.Thread(target=img.show, args=("QRCode",))
            _thread.setDaemon(True)
            _thread.start()
        except Exception as e:
            pass

        import qrcode

        url = f"https://login.weixin.qq.com/l/{uuid}"

        qr_api1 = "https://api.isoyu.com/qr/?m=1&e=L&p=20&url={}".format(url)
        qr_api2 = "https://api.qrserver.com/v1/create-qr-code/?size=400×400&data={}".format(url)
        qr_api3 = "https://api.pwmqr.com/qrcode/create/?url={}".format(url)
        qr_api4 = "https://my.tv.sohu.com/user/a/wvideo/getQRCode.do?text={}".format(url)
        print("You can also scan QRCode in any website below:")
        print(qr_api3)
        print(qr_api4)
        print(qr_api2)
        print(qr_api1)
        _send_qr_code([qr_api1, qr_api2, qr_api3, qr_api4])
        qr = qrcode.QRCode(border=1)
        qr.add_data(url)
        qr.make(fit=True)
        qr.print_ascii(invert=True)


@singleton
class WechatChannel(ChatChannel):
    NOT_SUPPORT_REPLYTYPE = []

    def __init__(self):
        super().__init__()
        self.receivedMsgs = ExpiredDict(60 * 60)
        self.auto_login_times = 0

    def startup(self):
        try:
            itchat.instance.receivingRetryCount = 600  # 修改断线超时时间
            # login by scan QRCode
            hotReload = conf().get("hot_reload", False)
            status_path = os.path.join(get_appdata_dir(), "itchat.pkl")
            itchat.auto_login(
                enableCmdQR=2,
                hotReload=hotReload,
                statusStorageDir=status_path,
                qrCallback=qrCallback,
                exitCallback=self.exitCallback,
                loginCallback=self.loginCallback
            )
            self.user_id = itchat.instance.storageClass.userName
            self.name = itchat.instance.storageClass.nickName
            logger.info("Wechat login success, user_id: {}, nickname: {}".format(self.user_id, self.name))
            # start message listener
            itchat.run()
        except Exception as e:
            logger.error(e)

    def exitCallback(self):
        try:
            from common.linkai_client import chat_client
            if chat_client.client_id and conf().get("use_linkai"):
                _send_logout()
                time.sleep(2)
                self.auto_login_times += 1
                if self.auto_login_times < 100:
                    chat_channel.handler_pool._shutdown = False
                    self.startup()
        except Exception as e:
            pass

    def loginCallback(self):
        logger.debug("Login success")
        _send_login_success()

    # handle_* 系列函数处理收到的消息后构造Context，然后传入produce函数中处理Context和发送回复
    # Context包含了消息的所有信息，包括以下属性
    #   type 消息类型, 包括TEXT、VOICE、IMAGE_CREATE
    #   content 消息内容，如果是TEXT类型，content就是文本内容，如果是VOICE类型，content就是语音文件名，如果是IMAGE_CREATE类型，content就是图片生成命令
    #   kwargs 附加参数字典，包含以下的key：
    #        session_id: 会话id
    #        isgroup: 是否是群聊
    #        receiver: 需要回复的对象
    #        msg: ChatMessage消息对象
    #        origin_ctype: 原始消息类型，语音转文字后，私聊时如果匹配前缀失败，会根据初始消息是否是语音来放宽触发规则
    #        desire_rtype: 希望回复类型，默认是文本回复，设置为ReplyType.VOICE是语音回复
    @time_checker
    @_check
    def handle_single(self, cmsg: ChatMessage):
        # filter system message
        if cmsg.other_user_id in ["weixin"]:
            return
        if cmsg.ctype == ContextType.VOICE:
            if conf().get("speech_recognition") != True:
                return
            logger.debug("[WX]receive voice msg: {}".format(cmsg.content))
        elif cmsg.ctype == ContextType.IMAGE:
            logger.debug("[WX]receive image msg: {}".format(cmsg.content))
        elif cmsg.ctype == ContextType.PATPAT:
            logger.debug("[WX]receive patpat msg: {}".format(cmsg.content))
        elif cmsg.ctype == ContextType.TEXT:
            logger.debug("[WX]receive text msg: {}, cmsg={}".format(json.dumps(cmsg._rawmsg, ensure_ascii=False), cmsg))
        else:
            logger.debug("[WX]receive msg: {}, cmsg={}".format(cmsg.content, cmsg))
        context = self._compose_context(cmsg.ctype, cmsg.content, isgroup=False, msg=cmsg)
        if context:
            self.produce(context)

    @time_checker
    @_check
    def handle_group(self, cmsg: ChatMessage):
        if cmsg.ctype == ContextType.VOICE:
            if conf().get("group_speech_recognition") != True:
                return
            logger.debug("[WX]receive voice for group msg: {}".format(cmsg.content))
        elif cmsg.ctype == ContextType.IMAGE:
            logger.debug("[WX]receive image for group msg: {}".format(cmsg.content))
        elif cmsg.ctype in [ContextType.JOIN_GROUP, ContextType.PATPAT, ContextType.ACCEPT_FRIEND, ContextType.EXIT_GROUP]:
            logger.debug("[WX]receive note msg: {}".format(cmsg.content))
        elif cmsg.ctype == ContextType.TEXT:
            # logger.debug("[WX]receive group msg: {}, cmsg={}".format(json.dumps(cmsg._rawmsg, ensure_ascii=False), cmsg))
            pass
        elif cmsg.ctype == ContextType.FILE:
            logger.debug(f"[WX]receive attachment msg, file_name={cmsg.content}")
        else:
            logger.debug("[WX]receive group msg: {}".format(cmsg.content))
        context = self._compose_context(cmsg.ctype, cmsg.content, isgroup=True, msg=cmsg)
        if context:
            self.produce(context)

    # 统一的发送函数，每个Channel自行实现，根据reply的type字段发送不同类型的消息
    def send(self, reply: Reply, context: Context):
        receiver = context["receiver"]
        if reply.type == ReplyType.TEXT:
            content = replace_markdown_urls(reply.content, '') #v佬原版
            # content=reply.content #sam修改，定义了content
            voice_reply = text_to_voice(content)
            if voice_reply.type == ReplyType.VOICE:
                itchat.send_file(voice_reply.content, toUserName=receiver)
                itchat.send(content, toUserName=receiver)          
            else:
                itchat.send(content, toUserName=receiver)
            logger.info("[WX] sendMsg={}, receiver={}".format(reply, receiver))
        elif reply.type == ReplyType.ERROR or reply.type == ReplyType.INFO:
            itchat.send(reply.content, toUserName=receiver)
            logger.info("[WX] sendMsg={}, receiver={}".format(reply, receiver))
        # elif reply.type == ReplyType.VOICE:
        #     try:
        #     itchat.send_file(reply.content, toUserName=receiver)
        #     logger.info("[WX] sendFile={}, receiver={}".format(reply.content, receiver))
        elif reply.type == ReplyType.IMAGE_URL:  # 从网络下载图片
            img_url = reply.content
            logger.debug(f"[WX] start download image, img_url={img_url}")
            pic_res = requests.get(img_url, stream=True)
            image_storage = io.BytesIO()
            size = 0
            for block in pic_res.iter_content(1024):
                size += len(block)
                image_storage.write(block)
            logger.info(f"[WX] download image success, size={size}, img_url={img_url}")
            image_storage.seek(0)
            itchat.send_image(image_storage, toUserName=receiver)
            logger.info("[WX] sendImage url={}, receiver={}".format(img_url, receiver))
        elif reply.type == ReplyType.IMAGE:  # 从文件读取图片
            image_storage = reply.content
            itchat.send_image(image_storage, toUserName=receiver)
            logger.info("[WX] sendImage, receiver={}".format(receiver))
        elif reply.type == ReplyType.FILE:  # 新增文件回复类型
            file_storage = reply.content
            itchat.send_file(file_storage, toUserName=receiver)
            logger.info("[WX] sendFile, receiver={}".format(receiver))
        elif reply.type == ReplyType.VIDEO:  # 新增视频回复类型
            video_storage = reply.content
            itchat.send_video(video_storage, toUserName=receiver)
            logger.info("[WX] sendFile, receiver={}".format(receiver))
        elif reply.type == ReplyType.VIDEO_URL:  # 新增视频URL回复类型
            video_url = reply.content
            logger.debug(f"[WX] start download video, video_url={video_url}")
            video_res = requests.get(video_url, stream=True)
            video_storage = io.BytesIO()
            size = 0
            for block in video_res.iter_content(1024):
                size += len(block)
                video_storage.write(block)
            logger.info(f"[WX] download video success, size={size}, video_url={video_url}")
            video_storage.seek(0)
            itchat.send_video(video_storage, toUserName=receiver)
            logger.info("[WX] sendVideo url={}, receiver={}".format(video_url, receiver))

def _send_login_success():
    try:
        from common.linkai_client import chat_client
        if chat_client.client_id:
            chat_client.send_login_success()
    except Exception as e:
        pass

def _send_logout():
    try:
        from common.linkai_client import chat_client
        if chat_client.client_id:
            chat_client.send_logout()
    except Exception as e:
        pass

def _send_qr_code(qrcode_list: list):
    try:
        from common.linkai_client import chat_client
        if chat_client.client_id:
            chat_client.send_qrcode(qrcode_list)
    except Exception as e:
        pass
