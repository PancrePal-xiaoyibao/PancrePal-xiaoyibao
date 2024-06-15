import requests
from sseclient import SSEClient #需要安装：pip install requests sseclient-py
import json

url = 'https://xiaoyibao.samqin.online/api/v1/chat/completions'  #填写fastgpt api地址
headers = {
    'Authorization': 'Bearer fastgpt-', #填写fastgpt api key
    'Content-Type': 'application/json'
}
# 依照文档填写请求体，注意stream为True，文档说明：https://doc.fastgpt.in/docs/development/openapi/chat/
data = {
    "chatId": "abcd",
    "stream": True,
    "detail": False,
    "variables": {
        "uid": "asdfadsfasfd2323",
        "name": "张三"
    },
    "messages": [
        {
            "content": "介绍下腹水的治疗方法",
            "role": "user"
        }
    ]
}

#流式输出
response = requests.post(url, headers=headers, json=data, stream=True)
client = SSEClient(response)

full_content = ""
for event in client.events():
    if event.data:
        try:
            data = json.loads(event.data)
            if 'choices' in data and len(data['choices']) > 0:
                content = data['choices'][0].get('delta', {}).get('content', '')
                if content:
                    full_content += content
                    print(content, end='', flush=True)
        except json.JSONDecodeError:
            pass

print("\nFull content:", full_content)