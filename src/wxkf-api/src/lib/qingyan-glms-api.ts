import { PassThrough } from "stream";
import path from "path";
import _ from "lodash";
import mime from "mime";
import FormData from "form-data";
import axios, { AxiosResponse } from "axios";

import APIException from "@/lib/exceptions/APIException.ts";
import EX from "@/api/consts/exceptions.ts";
import { createParser } from "eventsource-parser";
import environment from "./environment.ts";
import logger from "@/lib/logger.ts";
import util from "@/lib/util.ts";

const QINGYAN_GLMS_API_KEY = environment.envVars["QINGYAN_GLMS_API_KEY"];
// 最大重试次数
const MAX_RETRY_COUNT = 0;
// 重试延迟
const RETRY_DELAY = 5000;
// 文件最大大小
const FILE_MAX_SIZE = 100 * 1024 * 1024;
// access_token映射
const accessTokenMap = new Map();
// access_token请求队列映射
const accessTokenRequestQueueMap: Record<string, Function[]> = {};

/**
 * 请求access_token
 *
 * 使用refresh_token去刷新获得access_token
 *
 * @param apiKey API密钥
 */
async function requestToken(apiKey: string) {
  if (accessTokenRequestQueueMap[apiKey])
    return new Promise((resolve) =>
      accessTokenRequestQueueMap[apiKey].push(resolve)
    );
  accessTokenRequestQueueMap[apiKey] = [];
  const result = await (async () => {
    const [_apiKey, apiSecret] = apiKey.split('.');
    const result = await axios.post(
      "https://chatglm.cn/chatglm/assistant-api/v1/get_token",
      {
        api_key: _apiKey,
        api_secret: apiSecret
      },
      {
        timeout: 15000,
        validateStatus: () => true,
      }
    );
    const { access_token, expires_in } = checkResult(result, apiKey);
    return {
      accessToken: access_token,
      refreshTime: util.unixTimestamp() + expires_in,
    };
  })()
    .then((result) => {
      if (accessTokenRequestQueueMap[apiKey]) {
        accessTokenRequestQueueMap[apiKey].forEach((resolve) =>
          resolve(result)
        );
        delete accessTokenRequestQueueMap[apiKey];
      }
      logger.success(`Refresh successful`);
      return result;
    })
    .catch((err) => {
      if (accessTokenRequestQueueMap[apiKey]) {
        accessTokenRequestQueueMap[apiKey].forEach((resolve) =>
          resolve(err)
        );
        delete accessTokenRequestQueueMap[apiKey];
      }
      return err;
    });
  if (_.isError(result)) throw result;
  return result;
}

/**
 * 获取缓存中的access_token
 *
 * 避免短时间大量刷新token，未加锁，如果有并发要求还需加锁
 *
 * @param apiKey API密钥
 */
async function acquireToken(apiKey: string): Promise<string> {
  let result = accessTokenMap.get(apiKey);
  if (!result) {
    result = await requestToken(apiKey);
    accessTokenMap.set(apiKey, result);
  }
  if (util.unixTimestamp() > result.refreshTime) {
    result = await requestToken(apiKey);
    accessTokenMap.set(apiKey, result);
  }
  return result.accessToken;
}

/**
 * 同步对话补全
*
 * @param assistantId 智能体ID
 * @param messages 参考gpt系列消息格式，多轮对话请完整提供上下文
 * @param apiKey API密钥
 * @param retryCount 重试次数
 */
async function createCompletion(
  assistantId: string,
  messages: any[],
  apiKey = QINGYAN_GLMS_API_KEY,
  refConvId = '',
  retryCount = 0
) {
  return (async () => {
    logger.info(messages);

    // 提取引用文件URL并上传获得引用的文件ID列表
    const refFileUrls = extractRefFileUrls(messages);
    const refs = refFileUrls.length
      ? await Promise.all(
        refFileUrls.map((fileUrl) => uploadFile(fileUrl, apiKey))
      )
      : [];

    // 如果引用对话ID不正确则重置引用
    if (!/[0-9a-zA-Z]{24}/.test(refConvId))
      refConvId = '';

    // 请求流
    const token = await acquireToken(apiKey);
    const result = await axios.post(
      "https://chatglm.cn/chatglm/assistant-api/v1/stream",
      {
        assistant_id: assistantId,
        conversation_id: refConvId || undefined,
        prompt: messagesPrepare(messages, !!refConvId),
        file_list: refs
      },
      {
        headers: {
          Authorization: `Bearer ${token}`
        },
        // 120秒超时
        timeout: 120000,
        validateStatus: () => true,
        responseType: "stream",
      }
    );
    if (result.headers["content-type"].indexOf("text/event-stream") == -1) {
      result.data.on("data", buffer => logger.error(buffer.toString()));
      throw new APIException(
        EX.API_REQUEST_FAILED,
        `Stream response Content-Type invalid: ${result.headers["content-type"]}`
      );
    }

    const streamStartTime = util.timestamp();
    // 接收流为输出文本
    const answer = await receiveStream(assistantId, result.data);
    logger.success(
      `Stream has completed transfer ${util.timestamp() - streamStartTime}ms`
    );

    return answer;
  })().catch((err) => {
    if (retryCount < MAX_RETRY_COUNT) {
      logger.error(`Stream response error: ${err.stack}`);
      logger.warn(`Try again after ${RETRY_DELAY / 1000}s...`);
      return (async () => {
        await new Promise((resolve) => setTimeout(resolve, RETRY_DELAY));
        return createCompletion(
          assistantId,
          messages,
          apiKey,
          refConvId,
          retryCount + 1
        );
      })();
    }
    throw err;
  });
}

/**
 * 流式对话补全
 *
 * @param assistantId 智能体ID
 * @param messages 参考gpt系列消息格式，多轮对话请完整提供上下文
 * @param apiKey API密钥
 * @param retryCount 重试次数
 */
async function createCompletionStream(
  assistantId: string,
  messages: any[],
  apiKey = QINGYAN_GLMS_API_KEY,
  refConvId = '',
  retryCount = 0
) {
  return (async () => {
    logger.info(messages);

    // 提取引用文件URL并上传获得引用的文件ID列表
    const refFileUrls = extractRefFileUrls(messages);
    const refs = refFileUrls.length
      ? await Promise.all(
        refFileUrls.map((fileUrl) => uploadFile(fileUrl, apiKey))
      )
      : [];

    // 如果引用对话ID不正确则重置引用
    if (!/[0-9a-zA-Z]{24}/.test(refConvId))
      refConvId = '';

    // 请求流
    const token = await acquireToken(apiKey);
    const result = await axios.post(
      "https://chatglm.cn/chatglm/assistant-api/v1/stream",
      {
        assistant_id: assistantId,
        conversation_id: refConvId || undefined,
        prompt: messagesPrepare(messages, !!refConvId),
        file_list: refs
      },
      {
        headers: {
          Authorization: `Bearer ${token}`
        },
        // 120秒超时
        timeout: 120000,
        validateStatus: () => true,
        responseType: "stream",
      }
    );

    if (result.headers["content-type"].indexOf("text/event-stream") == -1) {
      logger.error(
        `Invalid response Content-Type:`,
        result.headers["content-type"]
      );
      result.data.on("data", buffer => logger.error(buffer.toString()));
      const transStream = new PassThrough();
      transStream.end(
        `data: ${JSON.stringify({
          id: "",
          model: assistantId,
          object: "chat.completion.chunk",
          choices: [
            {
              index: 0,
              delta: {
                role: "assistant",
                content: "服务暂时不可用，第三方响应错误",
              },
              finish_reason: "stop",
            },
          ],
          usage: { prompt_tokens: 1, completion_tokens: 1, total_tokens: 2 },
          created: util.unixTimestamp(),
        })}\n\n`
      );
      return transStream;
    }

    const streamStartTime = util.timestamp();
    // 创建转换流将消息格式转换为gpt兼容格式
    return createTransStream(assistantId, result.data, (convId: string) => {
      logger.success(
        `Stream has completed transfer ${util.timestamp() - streamStartTime}ms`
      );
    });
  })().catch((err) => {
    if (retryCount < MAX_RETRY_COUNT) {
      logger.error(`Stream response error: ${err.stack}`);
      logger.warn(`Try again after ${RETRY_DELAY / 1000}s...`);
      return (async () => {
        await new Promise((resolve) => setTimeout(resolve, RETRY_DELAY));
        return createCompletionStream(
          assistantId,
          messages,
          apiKey,
          refConvId,
          retryCount + 1
        );
      })();
    }
    throw err;
  });
}

async function generateImages(
  assistantId: string,
  prompt: string,
  apiKey = QINGYAN_GLMS_API_KEY,
  retryCount = 0
) {
  return (async () => {
    logger.info(prompt);
    const messages = [
      { role: "user", content: prompt.indexOf('画') == -1 ? `请画：${prompt}` : prompt },
    ];
    // 请求流
    const token = await acquireToken(apiKey);
    const result = await axios.post(
      "https://chatglm.cn/chatglm/assistant-api/v1/stream",
      {
        assistant_id: assistantId,
        prompt: messagesPrepare(messages)
      },
      {
        headers: {
          Authorization: `Bearer ${token}`
        },
        // 120秒超时
        timeout: 120000,
        validateStatus: () => true,
        responseType: "stream",
      }
    );

    if (result.headers["content-type"].indexOf("text/event-stream") == -1) {
      logger.error(
        `Invalid response Content-Type:`,
        result.headers["content-type"]
      );
      result.data.on("data", buffer => logger.error(buffer.toString()));
      throw new APIException(
        EX.API_REQUEST_FAILED,
        `Stream response Content-Type invalid: ${result.headers["content-type"]}`
      );
    }

    const streamStartTime = util.timestamp();
    // 接收流为输出文本
    const { convId, imageUrls } = await receiveImages(result.data);
    logger.success(
      `Stream has completed transfer ${util.timestamp() - streamStartTime}ms`
    );

    if (imageUrls.length == 0)
      throw new APIException(EX.API_IMAGE_GENERATION_FAILED);

    return imageUrls;
  })().catch((err) => {
    if (retryCount < MAX_RETRY_COUNT) {
      logger.error(`Stream response error: ${err.message}`);
      logger.warn(`Try again after ${RETRY_DELAY / 1000}s...`);
      return (async () => {
        await new Promise((resolve) => setTimeout(resolve, RETRY_DELAY));
        return generateImages(assistantId, prompt, apiKey, retryCount + 1);
      })();
    }
    throw err;
  });
}

/**
 * 提取消息中引用的文件URL
 *
 * @param messages 参考gpt系列消息格式，多轮对话请完整提供上下文
 */
function extractRefFileUrls(messages: any[]) {
  const urls = [];
  // 如果没有消息，则返回[]
  if (!messages.length) {
    return urls;
  }
  // 只获取最新的消息
  const lastMessage = messages[messages.length - 1];
  if (_.isArray(lastMessage.content)) {
    lastMessage.content.forEach((v) => {
      if (!_.isObject(v) || !["file", "image_url"].includes(v["type"])) return;
      // wxkf-api支持格式
      if (
        v["type"] == "file" &&
        _.isObject(v["file_url"]) &&
        _.isString(v["file_url"]["url"])
      )
        urls.push(v["file_url"]["url"]);
      // 兼容gpt-4-vision-preview API格式
      else if (
        v["type"] == "image_url" &&
        _.isObject(v["image_url"]) &&
        _.isString(v["image_url"]["url"])
      )
        urls.push(v["image_url"]["url"]);
    });
  }
  logger.info("本次请求上传：" + urls.length + "个文件");
  return urls;
}

/**
 * 消息预处理
 *
 * 由于接口只取第一条消息，此处会将多条消息合并为一条，实现多轮对话效果
 *
 * @param messages 参考gpt系列消息格式，多轮对话请完整提供上下文
 * @param refs 参考文件列表
 * @param isRefConv 是否为引用会话
 */
function messagesPrepare(messages: any[], isRefConv = false) {
  let content;
  if (isRefConv || messages.length < 2) {
    content = messages.reduce((content, message) => {
      if (_.isArray(message.content)) {
        return (
          message.content.reduce((_content, v) => {
            if (!_.isObject(v) || v["type"] != "text") return _content;
            return _content + (v["text"] || "") + "\n";
          }, content)
        );
      }
      return content + `${message.content}\n`;
    }, "");
    logger.info("\n透传内容：\n" + content);
  }
  else {
    // 检查最新消息是否含有"type": "image_url"或"type": "file",如果有则注入消息
    let latestMessage = messages[messages.length - 1];
    let hasFileOrImage =
      Array.isArray(latestMessage.content) &&
      latestMessage.content.some(
        (v) => typeof v === "object" && ["file", "image_url"].includes(v["type"])
      );
    if (hasFileOrImage) {
      let newFileMessage = {
        content: "关注用户最新发送文件和消息",
        role: "system",
      };
      messages.splice(messages.length - 1, 0, newFileMessage);
      logger.info("注入提升尾部文件注意力system prompt");
    } else {
      // 由于注入会导致设定污染，暂时注释
      // let newTextMessage = {
      //   content: "关注用户最新的消息",
      //   role: "system",
      // };
      // messages.splice(messages.length - 1, 0, newTextMessage);
      // logger.info("注入提升尾部消息注意力system prompt");
    }
    content = (
      messages.reduce((content, message) => {
        const role = message.role
          .replace("system", "<|sytstem|>")
          .replace("assistant", "<|assistant|>")
          .replace("user", "<|user|>");
        if (_.isArray(message.content)) {
          return (
            message.content.reduce((_content, v) => {
              if (!_.isObject(v) || v["type"] != "text") return _content;
              return _content + (`${role}\n` + v["text"] || "") + "\n";
            }, content)
          );
        }
        return (content += `${role}\n${message.content}\n`);
      }, "") + "<|assistant|>\n"
    )
      // 移除MD图像URL避免幻觉
      .replace(/\!\[.+\]\(.+\)/g, "")
      // 移除临时路径避免在新会话引发幻觉
      .replace(/\/mnt\/data\/.+/g, "");
    logger.info("\n对话合并：\n" + content);
  }
  return content;
}

/**
 * 预检查文件URL有效性
 *
 * @param fileUrl 文件URL
 */
async function checkFileUrl(fileUrl: string) {
  if (util.isBASE64Data(fileUrl)) return;
  const result = await axios.head(fileUrl, {
    timeout: 15000,
    validateStatus: () => true,
  });
  if (result.status >= 400)
    throw new APIException(
      EX.API_FILE_URL_INVALID,
      `File ${fileUrl} is not valid: [${result.status}] ${result.statusText}`
    );
  // 检查文件大小
  if (result.headers && result.headers["content-length"]) {
    const fileSize = parseInt(result.headers["content-length"], 10);
    if (fileSize > FILE_MAX_SIZE)
      throw new APIException(
        EX.API_FILE_EXECEEDS_SIZE,
        `File ${fileUrl} is not valid`
      );
  }
}

/**
 * 上传文件
 *
 * @param fileUrl 文件URL
 * @param apiKey API密钥
 */
async function uploadFile(fileUrl: string, apiKey: string) {
  // 预检查远程文件URL可用性
  await checkFileUrl(fileUrl);

  let filename, fileData, mimeType;
  // 如果是BASE64数据则直接转换为Buffer
  if (util.isBASE64Data(fileUrl)) {
    mimeType = util.extractBASE64DataFormat(fileUrl);
    const ext = mime.getExtension(mimeType);
    filename = `${util.uuid()}.${ext}`;
    fileData = Buffer.from(util.removeBASE64DataHeader(fileUrl), "base64");
  }
  // 下载文件到内存，如果您的服务器内存很小，建议考虑改造为流直传到下一个接口上，避免停留占用内存
  else {
    filename = path.basename(fileUrl);
    ({ data: fileData } = await axios.get(fileUrl, {
      responseType: "arraybuffer",
      // 100M限制
      maxContentLength: FILE_MAX_SIZE,
      // 60秒超时
      timeout: 60000,
    }));
  }

  // 获取文件的MIME类型
  mimeType = mimeType || mime.getType(filename);

  const formData = new FormData();
  formData.append("file", fileData, {
    filename,
    contentType: mimeType,
  });

  // 上传文件到目标OSS
  const token = await acquireToken(apiKey);
  let result = await axios.request({
    method: "POST",
    url: "https://chatglm.cn/chatglm/assistant-api/v1/file_upload",
    data: formData,
    // 100M限制
    maxBodyLength: FILE_MAX_SIZE,
    // 120秒超时
    timeout: 120000,
    headers: {
      Authorization: `Bearer ${token}`,
      ...formData.getHeaders(),
    },
    validateStatus: () => true,
  });
  return checkResult(result, apiKey);
}

/**
 * 检查请求结果
 *
 * @param result 结果
 */
function checkResult(result: AxiosResponse, apiKey: string) {
  if (!result.data) return null;
  const { status, message, result: _result } = result.data;
  if (!_.isFinite(status)) return result.data;
  if (status === 0) return _result;
  throw new APIException(EX.API_REQUEST_FAILED, `[请求失败]: ${message}`);
}

/**
 * 从流接收完整的消息内容
 *
 * @param stream 消息流
 */
async function receiveStream(assistantId: string, stream: any): Promise<any> {
  return new Promise((resolve, reject) => {
    // 消息初始化
    const data = {
      id: "",
      model: assistantId,
      object: "chat.completion",
      choices: [
        {
          index: 0,
          message: { role: "assistant", content: "" },
          finish_reason: "stop",
        },
      ],
      usage: { prompt_tokens: 1, completion_tokens: 1, total_tokens: 2 },
      created: util.unixTimestamp(),
    };
    let toolCall = false;
    let codeGenerating = false;
    let codeTemp = "";
    let lastExecutionOutput = "";
    let textOffset = 0;
    let refContent = '';
    const parser = createParser((event) => {
      try {
        if (event.type !== "event") return;
        // 解析JSON
        const result = _.attempt(() => JSON.parse(event.data));
        if (_.isError(result))
          throw new Error(`Stream response invalid: ${event.data}`);
        if (!data.id && result.conversation_id)
          data.id = result.conversation_id;
        if (result.status == "intervene")
          throw new APIException(EX.API_CONTENT_FILTERED);
        if (result.status != "finish") {
          const { status, content, meta_data } = result.message;
          if(!content)
            return;
          const {
            type,
            text,
            image,
            code,
            content: innerCcontent
          } = content;
          let innerStr = '';
          if (type == "text") {
            if (toolCall) {
              innerStr += "\n";
              textOffset++;
              toolCall = false;
            }
            innerStr += text;
          } else if (
            type == "quote_result" &&
            status == "finish" &&
            meta_data &&
            _.isArray(meta_data.metadata_list)
          ) {
            refContent = meta_data.metadata_list.reduce((meta, v) => {
              return meta + `${v.title} - ${v.url}\n`;
            }, refContent);
          } else if (
            type == "image" &&
            _.isArray(image) &&
            status == "finish"
          ) {
            const imageText =
              image.reduce(
                (imgs, v) =>
                  imgs +
                  (/^(http|https):\/\//.test(v.image_url)
                    ? `![图像](${v.image_url || ""})`
                    : ""),
                ""
              ) + "\n";
            textOffset += imageText.length;
            toolCall = true;
            innerStr += imageText;
          } else if (
            type == "code" &&
            status == "finish" &&
            codeGenerating
          ) {
            const codeFooter = "\n```\n";
            codeGenerating = false;
            codeTemp = "";
            textOffset += codeFooter.length;
            innerStr += codeFooter;
          } else if (type == "code") {
            let codeHead = "";
            if (!codeGenerating) {
              codeGenerating = true;
              codeHead = "```python\n";
            }
            const chunk = code.substring(codeTemp.length, code.length);
            codeTemp += chunk;
            textOffset += codeHead.length + chunk.length;
            innerStr += codeHead + chunk;
          } else if (
            type == "execution_output" &&
            _.isString(innerCcontent) &&
            status == "finish" &&
            lastExecutionOutput != innerCcontent
          ) {
            lastExecutionOutput = innerCcontent;
            const _content = innerCcontent.replace(/^\n/, "");
            textOffset += _content.length + 1;
            innerStr += _content + "\n";
          }
          const chunk = innerStr.substring(
            data.choices[0].message.content.length - textOffset,
            innerStr.length
          );
          data.choices[0].message.content += chunk;
        } else {
          data.choices[0].message.content =
            data.choices[0].message.content.replace(/【\d+†(来源|source)】/g, "") + (refContent ? `\n\n搜索结果来自：\n${refContent.replace(/\n$/, '')}` : '');
          resolve(data);
        }
      } catch (err) {
        logger.error(err);
        reject(err);
      }
    });
    // 将流数据喂给SSE转换器
    stream.on("data", (buffer) => parser.feed(buffer.toString()));
    stream.once("error", (err) => reject(err));
    stream.once("close", () => resolve(data));
  });
}

/**
 * 创建转换流
 *
 * 将流格式转换为gpt兼容流格式
 *
 * @param assistantId 智能体ID
 * @param stream 消息流
 * @param endCallback 传输结束回调
 */
function createTransStream(assistantId: string, stream: any, endCallback?: Function) {
  // 消息创建时间
  const created = util.unixTimestamp();
  // 创建转换流
  const transStream = new PassThrough();
  let textContent = "";
  let toolCall = false;
  let codeGenerating = false;
  let codeTemp = "";
  let lastExecutionOutput = "";
  let textOffset = 0;
  !transStream.closed &&
    transStream.write(
      `data: ${JSON.stringify({
        id: "",
        model: assistantId,
        object: "chat.completion.chunk",
        choices: [
          {
            index: 0,
            delta: { role: "assistant", content: "" },
            finish_reason: null,
          },
        ],
        created,
      })}\n\n`
    );
  const parser = createParser((event) => {
    try {
      if (event.type !== "event") return;
      // 解析JSON
      const result = _.attempt(() => JSON.parse(event.data));
      if (_.isError(result))
        throw new Error(`Stream response invalid: ${event.data}`);
      if (result.status != "finish" && result.status != "intervene") {
        const { status, content, meta_data } = result.message;
        if(!content)
          return;
        const {
          type,
          text,
          image,
          code,
          content: innerCcontent
        } = content;
        let innerStr = '';
        if (type == "text") {
          if (toolCall) {
            innerStr += "\n";
            textOffset++;
            toolCall = false;
          }
          innerStr += text;
        } else if (
          type == "quote_result" &&
          status == "finish" &&
          meta_data &&
          _.isArray(meta_data.metadata_list)
        ) {
          const searchText =
          meta_data.metadata_list.reduce(
            (meta, v) => meta + `检索 ${v.title}(${v.url}) ...`,
            ""
          ) + "\n";
          textOffset += searchText.length;
          toolCall = true;
          innerStr += searchText;
        } else if (
          type == "image" &&
          _.isArray(image) &&
          status == "finish"
        ) {
          const imageText =
            image.reduce(
              (imgs, v) =>
                imgs +
                (/^(http|https):\/\//.test(v.image_url)
                  ? `![图像](${v.image_url || ""})`
                  : ""),
              ""
            ) + "\n";
          textOffset += imageText.length;
          toolCall = true;
          innerStr += imageText;
        } else if (
          type == "code" &&
          status == "finish" &&
          codeGenerating
        ) {
          const codeFooter = "\n```\n";
          codeGenerating = false;
          codeTemp = "";
          textOffset += codeFooter.length;
          innerStr += codeFooter;
        } else if (type == "code") {
          let codeHead = "";
          if (!codeGenerating) {
            codeGenerating = true;
            codeHead = "```python\n";
          }
          const chunk = code.substring(codeTemp.length, code.length);
          codeTemp += chunk;
          textOffset += codeHead.length + chunk.length;
          innerStr += codeHead + chunk;
        } else if (
          type == "execution_output" &&
          _.isString(innerCcontent) &&
          status == "finish" &&
          lastExecutionOutput != innerCcontent
        ) {
          lastExecutionOutput = innerCcontent;
          const _content = innerCcontent.replace(/^\n/, "");
          textOffset += _content.length + 1;
          innerStr += _content + "\n";
        }
        const chunk = innerStr.substring(textContent.length - textOffset, innerStr.length);
        if (chunk) {
          textContent += chunk;
          const data = `data: ${JSON.stringify({
            id: result.conversation_id,
            model: assistantId,
            object: "chat.completion.chunk",
            choices: [
              { index: 0, delta: { content: chunk }, finish_reason: null },
            ],
            created,
          })}\n\n`;
          !transStream.closed && transStream.write(data);
        }
      } else {
        const data = `data: ${JSON.stringify({
          id: result.conversation_id,
          model: assistantId,
          object: "chat.completion.chunk",
          choices: [
            {
              index: 0,
              delta:
                result.status == "intervene" &&
                  result.last_error &&
                  result.last_error.intervene_text
                  ? { content: `\n\n${result.last_error.intervene_text}` }
                  : {},
              finish_reason: "stop",
            },
          ],
          usage: { prompt_tokens: 1, completion_tokens: 1, total_tokens: 2 },
          created,
        })}\n\n`;
        !transStream.closed && transStream.write(data);
        !transStream.closed && transStream.end("data: [DONE]\n\n");
        textContent = "";
        endCallback && endCallback(result.conversation_id);
      }
    } catch (err) {
      logger.error(err);
      !transStream.closed && transStream.end("\n\n");
    }
  });
  // 将流数据喂给SSE转换器
  stream.on("data", (buffer) => parser.feed(buffer.toString()));
  stream.once(
    "error",
    () => !transStream.closed && transStream.end("data: [DONE]\n\n")
  );
  stream.once(
    "close",
    () => !transStream.closed && transStream.end("data: [DONE]\n\n")
  );
  return transStream;
}

/**
 * 从流接收图像
 *
 * @param stream 消息流
 */
async function receiveImages(
  stream: any
): Promise<{ convId: string; imageUrls: string[] }> {
  return new Promise((resolve, reject) => {
    let convId = "";
    const imageUrls = [];
    const parser = createParser((event) => {
      try {
        if (event.type !== "event") return;
        // 解析JSON
        const result = _.attempt(() => JSON.parse(event.data));
        if (_.isError(result))
          throw new Error(`Stream response invalid: ${event.data}`);
        if (!convId && result.conversation_id) convId = result.conversation_id;
        if (result.status == "intervene")
          throw new APIException(EX.API_CONTENT_FILTERED);
        if (result.status != "finish") {
          const { status, content, meta_data } = result.message;
          if(!content)
            return;
          const {
            type,
            text,
            image
          } = content;
          if (
            type == "image" &&
            _.isArray(image) &&
            status == "finish"
          ) {
            image.forEach((value) => {
              if (
                !/^(http|https):\/\//.test(value.image_url) ||
                imageUrls.indexOf(value.image_url) != -1
              )
                return;
              imageUrls.push(value.image_url);
            });
          }
          if (
            type == "text" &&
            status == "finish"
          ) {
            const urlPattern = /\((https?:\/\/\S+)\)/g;
            let match;
            while ((match = urlPattern.exec(text)) !== null) {
              const url = match[1];
              if (imageUrls.indexOf(url) == -1)
                imageUrls.push(url);
            }
          }
        }
      } catch (err) {
        logger.error(err);
        reject(err);
      }
    });
    // 将流数据喂给SSE转换器
    stream.on("data", (buffer) => parser.feed(buffer.toString()));
    stream.once("error", (err) => reject(err));
    stream.once("close", () =>
      resolve({
        convId,
        imageUrls,
      })
    );
  });
}

/**
 * API KEY切分
 *
 * @param authorization 认证字符串
 */
function apiKeySplit(authorization: string) {
  return authorization.replace("Bearer ", "").split(",");
}

export default {
  createCompletion,
  createCompletionStream,
  generateImages,
  apiKeySplit,
};
