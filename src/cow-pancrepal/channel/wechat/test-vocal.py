import io
import json
import os
import threading
import time
import datetime
import random

import requests

import os

import os

# 获取当前Python文件的绝对路径
current_file_path = os.path.abspath(__file__)

# 提取当前文件的目录
current_directory = os.path.dirname(current_file_path)

# 构建 'tmp' 目录的完整路径
target_dir = os.path.join(current_directory, 'tmp')

# 检查并创建目标目录
if not os.path.exists(target_dir):
    os.makedirs(target_dir)

# 现在你可以使用 target_dir 来保存文件
# file_name = os.path.join(target_dir, '20240517092257801.mp3')

# ... 其他代码 ...

text="你好，我是小明，请问你有什么问题吗？"
group_id = "1747965168630894850"
api_key = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJHcm91cE5hbWUiOiJxaW54aWFvcWlhbmciLCJVc2VyTmFtZSI6InFpbnhpYW9xaWFuZyIsIkFjY291bnQiOiIiLCJTdWJqZWN0SUQiOiIxNzQ3OTY1MTY4NjM1MDg5MTU0IiwiUGhvbmUiOiIxODUxNjU2OTEzOCIsIkdyb3VwSUQiOiIxNzQ3OTY1MTY4NjMwODk0ODUwIiwiUGFnZU5hbWUiOiIiLCJNYWlsIjoiIiwiQ3JlYXRlVGltZSI6IjIwMjQtMDUtMTQgMDg6MjU6MTAiLCJpc3MiOiJtaW5pbWF4In0.lG9wFKTCVWqROzLMX3cBrhtPmQ0LppEhDpAmgbApJfF-o3IXoMsfLk0Oty7FZmjyDltY5xDdJVh2w8BaKY5p5Skwukh8MjT6E_pi8mkP0qjCVKyfZ-kJhlOX7VE0cO2yFDvBoy8iqqN3NA_QObKq8iwdc1ko60Ot9KBnC0MezYipRxNmsztjFCHssRUvnvR1pfmGtb7dFpXJwtDa14WQV9Z0DIyTYlXYGiazqAK7H-zja7iMTvLp7jveK36FJgXI9fqjdOyaCKsmnFiNgmgasxhXpq_Uh-o_7kfcDjMkSVdXzSAjnC1dqH0RDzN_zl2Y8iIUhoLSfonKyLGMVV5Xlgls"

url = f"https://api.minimax.chat/v1/t2a_pro?GroupId={group_id}"
headers = {
    "Authorization": f"Bearer {api_key}",
    'Content-Type': 'application/json'
}
data = {
    'model': 'speech-01',
    'input': text,
    # 'voice': 'YaeMiko_hailuo'
    # 'voice_id': 'male-qn-qingse',
    "speed": 1.0,
    "vol": 1.0,
    "pitch": 0,
    "audio_sample_rate": 24000,
    "bitrate": 128000,
    "timber_weights": [
        {
            "voice_id": "male-qn-qingse",
            "weight": 1
        }]
}
response = requests.post(url, headers=headers, json=data)
# file_name =  datetime.datetime.now().strftime('%Y%m%d%H%M%S') + str(random.randint(0, 1000)) + ".mp3"
file_name = os.path.join(target_dir, datetime.datetime.now().strftime('%Y%m%d%H%M%S') + str(random.randint(0, 1000)) + ".mp3")
# logger.debug(f"[OPENAI] text_to_Voice file_name={file_name}, input={text}")
with open(file_name, 'wb') as f:
    f.write(response.content)
# logger.info(f"[OPENAI] text_to_Voice success")
# reply = Reply(ReplyType.VOICE, file_name)

print("file sent ok",target_dir, file_name)
