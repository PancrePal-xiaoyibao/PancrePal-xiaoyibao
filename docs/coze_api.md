# 扣子空间对话API

其中的 `COZE_CN_BASE_URL` 和 `coze_api_token` 是需要从环境变量中读取的

## 流式传输

```py
"""
This example is about how to use the streaming interface to start a chat request
and handle chat events
"""

import os
# Our official coze sdk for Python [cozepy](https://github.com/coze-dev/coze-py)
from cozepy import COZE_CN_BASE_URL

# Get an access_token through personal access token or oauth.
coze_api_token = 'cztei_lvkC35KFVV5jtDkqDPhmXPAWv7RYvqPgHNgFmjVzwbEY1hvdH5LXXCyrOlXzAIKO6'
# The default access is api.coze.com, but if you need to access api.coze.cn,
# please use base_url to configure the api endpoint to access
coze_api_base = COZE_CN_BASE_URL

from cozepy import Coze, TokenAuth, Message, ChatStatus, MessageContentType, ChatEventType  # noqa

# Init the Coze client through the access_token.
coze = Coze(auth=TokenAuth(token=coze_api_token), base_url=coze_api_base)

# Create a bot instance in Coze, copy the last number from the web link as the bot's ID.
bot_id = '7530484662339436596'
# The user id identifies the identity of a user. Developers can use a custom business ID
# or a random string.
user_id = '123456789'

# Call the coze.chat.stream method to create a chat. The create method is a streaming
# chat and will return a Chat Iterator. Developers should iterate the iterator to get
# chat event and handle them.
for event in coze.chat.stream(
    bot_id=bot_id,
    user_id=user_id,
    additional_messages=[
        Message.build_user_question_text("Tell a 500-word story."),
    ],
):
    if event.event == ChatEventType.CONVERSATION_MESSAGE_DELTA:
        print(event.message.content, end="", flush=True)

    if event.event == ChatEventType.CONVERSATION_CHAT_COMPLETED:
        print()
        print("token usage:", event.chat.usage.token_count)
```

## 阻塞模式

```py
"""
This example describes how to use the chat interface to initiate conversations,
poll the status of the conversation, and obtain the messages after the conversation is completed.
"""

import os
import time
# Our official coze sdk for Python [cozepy](https://github.com/coze-dev/coze-py)
from cozepy import COZE_CN_BASE_URL

# Get an access_token through personal access token or oauth.
coze_api_token = 'cztei_lvkC35KFVV5jtDkqDPhmXPAWv7RYvqPgHNgFmjVzwbEY1hvdH5LXXCyrOlXzAIKO6'
# The default access is api.coze.com, but if you need to access api.coze.cn,
# please use base_url to configure the api endpoint to access
coze_api_base = COZE_CN_BASE_URL

from cozepy import Coze, TokenAuth, Message, ChatStatus, MessageContentType  # noqa

# Init the Coze client through the access_token.
coze = Coze(auth=TokenAuth(token=coze_api_token), base_url=coze_api_base)

# Create a bot instance in Coze, copy the last number from the web link as the bot's ID.
bot_id = '7530484662339436596'
# The user id identifies the identity of a user. Developers can use a custom business ID
# or a random string.
user_id = '123456789'

# To simplify the call, the SDK provides a wrapped function to complete non-streaming chat,
# polling, and obtaining the messages of the chat. Developers can use create_and_poll to
# simplify the process.
chat_poll = coze.chat.create_and_poll(
    bot_id=bot_id,
    user_id=user_id,
    additional_messages=[
        Message.build_user_question_text("Who are you?"),
        Message.build_assistant_answer("I am Bot by Coze."),
        Message.build_user_question_text("What about you?"),
    ],
)
for message in chat_poll.messages:
    print(message.content, end="", flush=True)

if chat_poll.chat.status == ChatStatus.COMPLETED:
    print()
    print("token usage:", chat_poll.chat.usage.token_count)
```

## 文件上传

```cURL
curl -X POST 'https://api.coze.cn/v1/files/upload' \
-H "Authorization: Bearer cztei_lvkC35KFVV5jtDkqDPhmXPAWv7RYvqPgHNgFmjVzwbEY1hvdH5LXXCyrOlXzAIKO6" \
-H "Content-Type: multipart/form-data"
```