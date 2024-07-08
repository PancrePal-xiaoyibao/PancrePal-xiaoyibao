# 微信客服接入智谱清言智能体API服务

## 准备流程

1. 前往微信客服（[https://kf.weixin.qq.com/](https://kf.weixin.qq.com/)）扫码登录（首先你得是企业微信管理员）。
2. 进入开发配置，点击企业内部接入，开始填写回调地址。
3. 回调地址请填写[https://example.com/message/notify](https://example.com/message/notify)（域名请替换为你的，地址是指向本服务部署地址）。
3. Token和EncodingAESKey可以自行填写或随机生成，然后先记录下来。
4. 验证回调通过后在开发配置可以拿到企业ID和Secret，记录下来。
5. 前往智谱清言[https://chatglm.cn/](https://chatglm.cn/)注册账号并登录，前往智能体中心->创作者中心->API Key管理，新建一个API Key，记录下来。
6. 在智谱清言智能体中心选择想要接入的智能体（使用智能体API则只能使用自己已发布的智能体，要使用其它智能体需要使用网页版本智能体接口，后续会提到两者区别）

## 安装

Docker安装方法待补充。

首先，您需要安装Node.js 18+。然后，您可以使用以下命令在项目根目录安装依赖和构建：

```bash
npm install
npm run build
```

## 设置环境变量

```bash
# 企业ID
export WXKF_API_CORP_ID="ww72************01"
# Secret
export WXKF_API_CORP_SECRET="****************"
# Token
export WXKF_API_TOKEN="****************"
# EncodingAESKey
export WXKF_API_ENCODING_AES_KEY="****************"
```

## 配置智能体

打开项目目录中的agent.yml文件，配置智能体即可，启动后服务会自动帮您配置好客服

## 运行

使用以下命令启动服务，服务监听8001端口：

```bash
npm start
```

## 验证效果

打开微信客服的客服账号，可以看到自动创建好的智能体列表，点击进去，复制账号ID，填入以下链接即可在微信打开。

`https://work.weixin.qq.com/kfid/账号ID`