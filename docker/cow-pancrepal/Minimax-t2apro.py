import requests
import json
import os
import datetime
import random
import subprocess
import io
import threading
import time

group_id = "1747965168630894850"
api_key = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJHcm91cE5hbWUiOiJxaW54aWFvcWlhbmciLCJVc2VyTmFtZSI6InFpbnhpYW9xaWFuZyIsIkFjY291bnQiOiIiLCJTdWJqZWN0SUQiOiIxNzQ3OTY1MTY4NjM1MDg5MTU0IiwiUGhvbmUiOiIxODUxNjU2OTEzOCIsIkdyb3VwSUQiOiIxNzQ3OTY1MTY4NjMwODk0ODUwIiwiUGFnZU5hbWUiOiIiLCJNYWlsIjoiIiwiQ3JlYXRlVGltZSI6IjIwMjQtMDUtMTcgMTA6MDk6NDYiLCJpc3MiOiJtaW5pbWF4In0.tWsjSvb3FPiDkMXzkvyClzMBhFj0E3qiVBv3ZvD8yQJnAManOtMTdAtKZg4Ze5-vS5cUJx9JxR2dbI3Qg4RDIYqexel1f0Pk5yyoySJxRoY2eZjiR7OVhja_aAJfyk4QzAQ8BwIgYJUowbszbk2b-xeDJumRmz8AVPb9jAVHAvetxKBC9B526c3KBgdJOfQjdAFOXtaSjszREm2P21L542aVUDW-Wz0HGhlvwy4IQEuV1FLX17MkruGn3kBjA_OavfDy_WJZVlstBKSmc2aiNlsSWAFwT8gbHuz_BU4EcZ52vZzjVbQ2ZNnhq1yqD3eBHn8vfj-lxY6zqmbHzupJTQ"
url = f"https://api.minimax.chat/v1/t2a_pro?GroupId={group_id}"

with open('/Users/qinxiaoqiang/Downloads/test.txt', 'r') as file_object:
    content = file_object.read()
    
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
}
data = {
    "voice_id": "male-qn-qingse",
    # "voice_id": "female-shaonv-jingpin",
    # "voice_id": "female-yujie-jingpin"
    # "voice_id": "female-chengshu-jingpin"
    # "voice_id": "female-tianmei-jingpin"
  	# 如同时传入voice_id和timber_weights时，则会自动忽略voice_id，以timber_weights传递的参数为准
    "text": content, #"零一万物 API 开放平台提供一系列具有不同功能和定价的 Yi 系列大模型。Yi 系列大模型是由零一万物开发的大语言模型家族。Yi 系列大模型在语言理解、文本生成、逻辑推理、数学运算、编写代码等多种任务上表现出色。Yi 系列大模型功能强大，使用简便，您可以根据您的实际使用需求选择体验更好、成本更优的模型或服务。",
  	# 如需要控制停顿时长，则增加输入<#X#>，X取值0.01-99.99，单位为秒，如：你<#5#>好（你与好中间停顿5秒）需要注意的是文本间隔时间需设置在两个可以语音发音的文本之间，且不能设置多个连续的时间间隔。
    "model": "speech-01",
    "speed": 1.0,
    "vol": 1.0,
    "pitch": 0,
    "audio_sample_rate": 24000,
    "bitrate": 128000,
    "timber_weights": [
        {
            "voice_id": "male-qn-qingse",
            "weight": 1
        },
        {
            "voice_id": "presenter_female",
            "weight": 1
        },
        {
            "voice_id": "presenter_male",
            "weight": 100
        },
        # {
        #     "voice_id": "female-shaonv-jingpin",
        #     "weight": 1
        # },
        # {
        #     "voice_id": "female-yujie-jingpin",
        #     "weight": 1
        # }, 
        {
            "voice_id": "audiobook_male_2",
            "weight": 1
        }
    ],
    "char_to_pitch": ["你/(ni1)"]
}
response = requests.post(url, headers=headers, json=data)
print(response.status_code)
print(response.json())

#获得audio_url地址
data = response.json() #json.loads(response)
audio_url=data["audio_file"]


# 下载并保存MP3文件d
mp3_response = requests.get(audio_url, stream=True)
if mp3_response.status_code == 200:
    file_name = "tmp/" + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + str(random.randint(0, 1000)) + ".mp3"
    with open(file_name, 'wb') as f:
        for chunk in mp3_response.iter_content(1024):
            f.write(chunk)
    output_file_path = os.path.abspath(file_name)
    print(f"文件路径: {output_file_path} \n复制并粘贴到文件管理器或浏览器中打开:")
    # subprocess.run(["open", "-W", output_file_path])
else:
    print("下载失败，状态码：", mp3_response.status_code)

#         logger.debug(f"[OPENAI] text_to_Voice file_name={file_name}")
#         logger.info(f"[OPENAI] text_to_Voice success")

#         # 创建Reply对象
#         reply = Reply(ReplyType.VOICE, file_name)
#     else:
#         logger.error(f"[OPENAI] text_to_Voice failed, status code: {mp3_response.status_code}")
# else:
#     logger.error(f"[OPENAI] GET request failed, status code: {response.status_code}")

# # response = requests.post(url, headers=headers, json=data)
# data = response.json() #json.loads(response)
# audio_url=data["audio_file"]
# mp3_response = requests.get(audio_url, stream=True)
# if mp3_response.status_code== 200:
#     file_name = "tmp/" + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + str(random.randint(0, 1000)) + ".mp3"
#     logger.debug(f"[OPENAI] text_to_Voice file_name={file_name}, input={text}") 
#     # print(file_name)
    # output_file_path = os.path.abspath("filename")
    # print("保存成功",output_file_path)
#     with open(file_name, 'wb') as f:
#         f.write(response.content)
#     logger.info(f"[OPENAI] text_to_Voice success")
    