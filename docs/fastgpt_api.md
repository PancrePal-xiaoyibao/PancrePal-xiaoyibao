# FastGPT对话请求接口（全部Agent的标准接入接口）


## 请求接口

```
curl --location --request POST 'http://localhost:3000/api/v1/chat/completions' \
--header 'Authorization: Bearer fastgpt-xxxxxx' \
--header 'Content-Type: application/json' \
--data-raw '{
"chatId": "my_chatId",
"stream": false,
"detail": false,
"responseChatItemId": "my_responseChatItemId",
"variables": {
    "uid": "asdfadsfasfd2323",
    "name": "张三"
},
"messages": [
    {
        "role": "user",
        "content": "导演是谁"
    }
]
}'
```


## detail=true,stream=false 响应

```
{
  "responseData": [
    // 不同模块的响应值, 不同版本具体值可能有差异，可先 log 自行查看最新值。
    {
      "moduleName": "Dataset Search",
      "price": 1.2000000000000002,
      "model": "Embedding-2",
      "tokens": 6,
      "similarity": 0.61,
      "limit": 3
    },
    {
      "moduleName": "AI Chat",
      "price": 454.5,
      "model": "FastAI-4k",
      "tokens": 303,
      "question": "导演是谁",
      "answer": "电影《铃芽之旅》的导演是新海诚。",
      "maxToken": 2050,
      "quoteList": [
        {
          "dataset_id": "646627f4f7b896cfd8910e38",
          "id": "8099",
          "q": "本作的主人公是谁？",
          "a": "本作的主人公是名叫铃芽的少女。",
          "source": "手动修改"
        },
        {
          "dataset_id": "646627f4f7b896cfd8910e38",
          "id": "8686",
          "q": "电影《铃芽之旅》男主角是谁？",
          "a": "电影《铃芽之旅》男主角是宗像草太，由松村北斗配音。",
          "source": ""
        },
        {
          "dataset_id": "646627f4f7b896cfd8910e38",
          "id": "19339",
          "q": "电影《铃芽之旅》的导演是谁？22",
          "a": "电影《铃芽之旅》的导演是新海诚。",
          "source": "手动修改"
        }
      ],
      "completeMessages": [
        {
          "obj": "System",
          "value": "下面是知识库内容:\n1. [本作的主人公是谁？\n本作的主人公是名叫铃芽的少女。]\n2. [电影《铃芽之旅》男主角是谁？\n电影《铃芽之旅》男主角是宗像草太，由松村北斗配音。]\n3. [电影《铃芽之旅》的导演是谁？22\n电影《铃芽之旅》的导演是新海诚。]\n"
        },
        {
          "obj": "System",
          "value": "1.请记住，你的身份是百度的下一代知识增强语言模型，能够完全根据知识库提供的内容回答问题。\n\n2. 你忘记了关于电影《铃芽之旅》以外的内容。"
        },
        {
          "obj": "System",
          "value": "你仅回答关于电影《玲芽之旅》的问题，其余问题直接回复: 我不清楚。"
        },
        {
          "obj": "Human",
          "value": "导演是谁"
        },
        {
          "obj": "AI",
          "value": "电影《铃芽之旅》的导演是新海诚。"
        }
      ]
    }
  ],
  "id": "",
  "model": "",
  "usage": {
    "prompt_tokens": 1,
    "completion_tokens": 1,
    "total_tokens": 1
  },
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "电影《铃芽之旅》的导演是新海诚。"
      },
      "finish_reason": "stop",
      "index": 0
    }
  ]
}
```

## detail=false,stream=true 响应

```
data: {"id":"","object":"","created":0,"choices":[{"delta":{"content":""},"index":0,"finish_reason":null}]}

data: {"id":"","object":"","created":0,"choices":[{"delta":{"content":"电"},"index":0,"finish_reason":null}]}

data: {"id":"","object":"","created":0,"choices":[{"delta":{"content":"影"},"index":0,"finish_reason":null}]}

data: {"id":"","object":"","created":0,"choices":[{"delta":{"content":"《"},"index":0,"finish_reason":null}]}
```

# FastGPT文件上传

FastGPT原生并不支持文件上传，需要上传到自定义的对象存储桶中，定义的接口为 `/api/v1/upload`，该接口需使用 multipart/form-data 进行请求

最终的响应体为：

```json
{
  "id": "72fa9618-8f89-4a37-9b33-7e1178a24a67",
  "name": "example.png",
  "size": 1024,
  "extension": "png",
  "mime_type": "image/png",
  "created_by": 123, //user name
  "created_at": 1577836800,
}

```
