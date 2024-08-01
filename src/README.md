一键部署
=========

## 简介

便捷部署,有两中方式可选，第一是下载编译好的[可执行文件](https://github.com/PancrePal-xiaoyibao/PancrePal-xiaoyibao/releases/download/v1.2/launch.tgz)，第二从源代码编译。

## 源码编译

### 1. 系统版本

使用 ubuntu 22.04

```bash
$ cat /etc/issue
Ubuntu 22.04 LTS
```

安装依赖软件包

```bash
$ sudo apt install -y git golang-go unzip docker.io docker-compose
```

### 2. 克隆源代码

```bash
$ git clone https://github.com/PancrePal-xiaoyibao/PancrePal-xiaoyibao.git
```

### 3. 代码下载完毕后，进入src/auto-deploy文件夹进行编译

编译命令
```bash
$ cd src/auto-deploy
$ sudo go mod tidy
$ sudo make
```

如果看到生成了launch文件，即编译成功。
```bash
ls -l launch
```

### 4. Configure

配置文件默认值 (deploy.json)

| Syntax    |                   Description                    |                  default value |
| :---      | :----------------------------------------------: |                --------------: |
| WorkDir   |   The deployment main directory of the project   |                          ./run |
| TmplDir   |          Deployment template directory           |                         ./tmpl |
| ManiFests |               Deployment Manifests               |            "api", "gpt", "ngx" |
| ImageAPI  |              one-api container name              |        justsong/one-api:latest |
| ImageGPT  |              fastGPT container name              | ghcr.io/labring/fastgpt:v4.6.4 |
| BaseURL   |            one-api interface base url            |       http://localhost:3600/v1 |
| ApiKey    |             one-api ai interface key             |                     1234567890 |
| RootKey   |               one-api root api key               |                     0987654321 |
| DbUser    |                database username                 |                       username |
| DbPass    |                 databse password                 |                       password |
| DataDir   |              System Data directory               |                         ./data |

配置例子
```bash
cat deploy.json
```
```json
{
  "WorkDir":    "./run",
  "TmplDir":    "./tmpl",
  "ManiFests":  ["api", "gpt", "ngx"],
  "ImageAPI":   "justsong/one-api:latest",
  "ImageGPT":   "ghcr.io/labring/fastgpt:v4.6.4",
  "BaseURL":    "http://localhost:3600/v1",
  "ApiKey":     "1234567890",
  "RootKey":    "0987654321",
  "DbUser":     "username",
  "DbPass":     "password",
  "DataDir":    "./data"
}
```

### 5. 运行自动部署

```bash
$ sudo chmod +x launch
# 启动部署
$ sudo ./launch -o start
# 关闭服务 
$ sudo ./launch -o stop
# 重启服务
$ sudo ./launch -o restart
```

### 6. 关于fastgpt 部署提醒：
1. 建议先部署oneapi或者newapi，建立LLM api池，方便后续模型对比测试和上线；
2. 建议定期备份数据库mongo

### 7. 关于config.json配置文件
1. 格式请保持一致；
2. 模型可以扩展：配置文件中已经有了样例，根据你要加入的模型，复制修改添加最好；
3. 建议embedding使用国内大模型，如qwen的embedding-02/async-01都可以有免费的token资源；
   <img width="592" alt="image" src="https://github.com/PancrePal-xiaoyibao/PancrePal-xiaoyibao/assets/103937568/348cc4d2-02cb-4619-9e4a-4e6aee0c1413">

5. 模型配置中，注意至少要有一个模型配置“datasetProcess”为true，用于fastgpt知识库前端“文件处理”配置选项，建议多个；
<img width="768" alt="image" src="https://github.com/PancrePal-xiaoyibao/PancrePal-xiaoyibao/assets/103937568/5c8b11f2-213a-42bc-a96a-9e06b614c8e9">


## License

This project is licensed under the terms of the MIT license