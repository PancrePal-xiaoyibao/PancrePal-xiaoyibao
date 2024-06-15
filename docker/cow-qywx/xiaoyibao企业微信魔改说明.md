
## 修改说明：
这个版本是把小胰宝接入到企业微信三方应用中。

## 魔改文件有3个：文件中有标注：gpt4修改
1.session_manger.py ：修复token提示报错，但是没完全解决，已经提了PR，请cow/linkai同学完善。执行中找不到get_token_from_session_file函数，但不影响使用。
2.chat_gpt_bot.py：修复str和list不兼容的报错。
3. chat_channel.py: 修复str和list不兼容的报错。