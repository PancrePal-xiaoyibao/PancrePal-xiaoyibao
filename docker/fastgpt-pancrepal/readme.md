### 部署说明 

下载docker-compose.yml文件后，可以直接利用docker快速部署

### 关于docker-compose.yml和部署提醒：
1. 建议先部署oneapi或者newapi，建立LLM api池，方便后续模型对比测试和上线；
2. 部署后的oneapi地址和令牌请在docker-compose.yml文件中对应修改；
3. 建议定期备份数据库mongo

### 关于config.json配置文件
1. 格式请保持一致；
2. 模型可以扩展：配置文件中已经有了样例，根据你要加入的模型，复制修改添加最好；
3. 建议embedding使用国内大模型，如qwen的embedding-02/async-01都可以有免费的token资源；
   <img width="592" alt="image" src="https://github.com/PancrePal-xiaoyibao/PancrePal-xiaoyibao/assets/103937568/348cc4d2-02cb-4619-9e4a-4e6aee0c1413">

5. 模型配置中，注意至少要有一个模型配置“datasetProcess”为true，用于fastgpt知识库前端“文件处理”配置选项，建议多个；
<img width="768" alt="image" src="https://github.com/PancrePal-xiaoyibao/PancrePal-xiaoyibao/assets/103937568/5c8b11f2-213a-42bc-a96a-9e06b614c8e9">



   
感谢fastgpt提供项目，请使用中遵守fastgpt项目的协议。
