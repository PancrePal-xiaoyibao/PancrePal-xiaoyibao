import asyncio
import time
import json
import uuid
import os
import websockets
import gzip
import hmac
import base64
import hashlib
import random
from urllib import parse
from tabulate import tabulate
from config.settings import load_config
description = "流式ASR首词耗时测试"

class AccessToken:
    @staticmethod
    def _encode_text(text):
        encoded_text = parse.quote_plus(text)
        return encoded_text.replace("+", "%20").replace("*", "%2A").replace("%7E", "~")

    @staticmethod
    def _encode_dict(dic):
        keys = dic.keys()
        dic_sorted = [(key, dic[key]) for key in sorted(keys)]
        encoded_text = parse.urlencode(dic_sorted)
        return encoded_text.replace("+", "%20").replace("*", "%2A").replace("%7E", "~")

    @staticmethod
    def create_token(access_key_id, access_key_secret):
        parameters = {
            "AccessKeyId": access_key_id,
            "Action": "CreateToken",
            "Format": "JSON",
            "RegionId": "cn-shanghai",
            "SignatureMethod": "HMAC-SHA1",
            "SignatureNonce": str(uuid.uuid1()),
            "SignatureVersion": "1.0",
            "Timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "Version": "2019-02-28",
        }
        query_string = AccessToken._encode_dict(parameters)
        string_to_sign = (
            "GET" + "&" + AccessToken._encode_text("/") + "&" + AccessToken._encode_text(query_string)
        )
        secreted_string = hmac.new(
            bytes(access_key_secret + "&", encoding="utf-8"),
            bytes(string_to_sign, encoding="utf-8"),
            hashlib.sha1,
        ).digest()
        signature = base64.b64encode(secreted_string)
        signature = AccessToken._encode_text(signature)
        full_url = "http://nls-meta.cn-shanghai.aliyuncs.com/?Signature=%s&%s" % (signature, query_string)
        response = requests.get(full_url)
        if response.ok:
            root_obj = response.json()
            if "Token" in root_obj:
                return root_obj["Token"]["Id"], root_obj["Token"]["ExpireTime"]
        return None, None


class DoubaoStreamASRPerformanceTester:
    def __init__(self):
        self.config = load_config()
        self.test_audio_files = self._load_test_audio_files()
        self.results = []
        
    def _load_test_audio_files(self):
        """加载测试用的音频文件"""
        audio_root = os.path.join(os.getcwd(), "config", "assets")
        test_files = []
        
        if os.path.exists(audio_root):
            for file_name in os.listdir(audio_root):
                if file_name.endswith('.wav') or file_name.endswith('.pcm'):
                    with open(os.path.join(audio_root, file_name), 'rb') as f:
                        test_files.append(f.read())
        return test_files
    
    async def test_doubao_stream_asr(self, test_count=5):
        """测试豆包流式ASR首词响应时间"""
        if not self.test_audio_files:
            print("没有找到测试音频文件")
            return
            
        asr_config = self.config["ASR"]["DoubaoStreamASR"]
        latencies = []
        
        for i in range(test_count):
            try:
                ws_url = "wss://openspeech.bytedance.com/api/v3/sauc/bigmodel"
                appid = asr_config["appid"]
                access_token = asr_config["access_token"]
                uid = asr_config.get("uid", "streaming_asr_service")
                
                start_time = time.time()
                
                headers = {
                    "X-Api-App-Key": appid,
                    "X-Api-Access-Key": access_token,
                    "X-Api-Resource-Id": "volc.bigasr.sauc.duration",
                    "X-Api-Connect-Id": str(uuid.uuid4())
                }
                
                async with websockets.connect(
                    ws_url,
                    additional_headers=headers,
                    max_size=1000000000,
                    ping_interval=None,
                    ping_timeout=None,
                    close_timeout=10
                ) as ws:
                    # 发送初始化请求
                    request_params = {
                        "app": {
                            "appid": appid,
                            "token": access_token
                        },
                        "user": {"uid": uid},
                        "request": {
                            "reqid": str(uuid.uuid4()),
                            "workflow": "audio_in,resample,partition,vad,fe,decode,itn,nlu_punctuate",
                            "show_utterances": True,
                            "result_type": "single",
                            "sequence": 1
                        },
                        "audio": {
                            "format": "pcm",
                            "codec": "pcm",
                            "rate": 16000,
                            "language": "zh-CN",
                            "bits": 16,
                            "channel": 1,
                            "sample_rate": 16000
                        }
                    }
                    
                    payload_bytes = str.encode(json.dumps(request_params))
                    payload_bytes = gzip.compress(payload_bytes)
                    full_client_request = self._generate_header()
                    full_client_request.extend((len(payload_bytes)).to_bytes(4, "big"))
                    full_client_request.extend(payload_bytes)
                    
                    await ws.send(full_client_request)
                    
                    init_res = await ws.recv()
                    result = self._parse_response(init_res)
                    
                    if "code" in result and result["code"] != 1000:
                        raise Exception(f"ASR服务初始化失败: {result.get('payload_msg', {}).get('error', '未知错误')}")
                    
                    # 发送音频数据
                    audio_data = self.test_audio_files[0]
                    if audio_data.startswith(b'RIFF'):
                        audio_data = audio_data[44:]
                        
                    # 直接发送原始音频数据，不进行opus解码
                    payload = gzip.compress(audio_data)
                    audio_request = bytearray(self._generate_audio_default_header())
                    audio_request.extend(len(payload).to_bytes(4, "big"))
                    audio_request.extend(payload)
                    await ws.send(audio_request)
                    
                    # 等待第一个数据块
                    first_chunk = await ws.recv()
                    latency = time.time() - start_time
                    latencies.append(latency)
                    await ws.close()
                    
            except Exception as e:
                print(f"第{i+1}次测试: {str(e)}")
                latencies.append(0)
        
        return self._calculate_result("豆包流式ASR", latencies, test_count)
        
    async def test_aliyun_stream_asr(self, test_count=5):
        """测试阿里云流式ASR首词响应时间"""
        if not self.test_audio_files:
            print("没有找到测试音频文件")
            return
            
        asr_config = self.config["ASR"]["AliyunStreamASR"]
        latencies = []
        
        for i in range(test_count):
            try:
                access_key_id = asr_config["access_key_id"]
                access_key_secret = asr_config["access_key_secret"]
                appkey = asr_config["appkey"]
                host = asr_config.get("host", "nls-gateway-cn-shanghai.aliyuncs.com")
                
                # 获取Token
                token, _ = AccessToken.create_token(access_key_id, access_key_secret)
                if not token:
                    raise Exception("无法获取阿里云ASR Token")
                
                # 确定WebSocket URL
                if "-internal." in host:
                    ws_url = f"ws://{host}/ws/v1"
                else:
                    ws_url = f"wss://{host}/ws/v1"
                
                start_time = time.time()
                async with websockets.connect(
                    ws_url,
                    additional_headers={"X-NLS-Token": token},
                    max_size=1000000000,
                    ping_interval=None,
                    ping_timeout=None,
                    close_timeout=10
                ) as ws:
                    # 发送开始请求
                    start_request = {
                        "header": {
                            "namespace": "SpeechTranscriber",
                            "name": "StartTranscription",
                            "status": 20000000,
                            "message_id": ''.join(random.choices('0123456789abcdef', k=32)),
                            "task_id": ''.join(random.choices('0123456789abcdef', k=32)),
                            "status_text": "Gateway:SUCCESS:Success.",
                            "appkey": appkey
                        },
                        "payload": {
                            "format": "pcm",
                            "sample_rate": 16000,
                            "enable_intermediate_result": True,
                            "enable_punctuation_prediction": True,
                            "enable_inverse_text_normalization": True,
                            "max_sentence_silence": asr_config.get("max_sentence_silence", 8000),
                            "enable_voice_detection": False,
                        }
                    }
                    await ws.send(json.dumps(start_request, ensure_ascii=False))
                    
                    # 等待服务器准备
                    start_response = await ws.recv()
                    response_data = json.loads(start_response)
                    if response_data["header"]["name"] != "TranscriptionStarted":
                        raise Exception("阿里云ASR服务初始化失败")
                    
                    # 发送音频数据
                    audio_data = self.test_audio_files[0]
                    if audio_data.startswith(b'RIFF'):
                        audio_data = audio_data[44:]  # 去掉WAV头
                    
                    await ws.send(audio_data)
                    
                    # 等待第一个结果
                    while True:
                        response = await ws.recv()
                        if isinstance(response, str):
                            result = json.loads(response)
                            if result["header"]["name"] == "TranscriptionResultChanged":
                                latency = time.time() - start_time
                                latencies.append(latency)
                                break
                            elif result["header"]["name"] == "TaskFailed":
                                raise Exception(f"阿里云ASR识别失败: {result.get('payload', {}).get('error_info', '未知错误')}")
                    
                    # 发送停止请求
                    stop_msg = {
                        "header": {
                            "namespace": "SpeechTranscriber",
                            "name": "StopTranscription",
                            "status": 20000000,
                            "message_id": ''.join(random.choices('0123456789abcdef', k=32)),
                            "status_text": "Client:Stop",
                            "appkey": appkey
                        }
                    }
                    await ws.send(json.dumps(stop_msg, ensure_ascii=False))
                    await ws.close()
                    
            except Exception as e:
                print(f"第{i+1}次测试: {str(e)}")
                latencies.append(0)
        
        return self._calculate_result("阿里云流式ASR", latencies, test_count)
    
    def _generate_header(self):
        """生成请求头"""
        header = bytearray()
        header.append((0x01 << 4) | 0x01)
        header.append((0x01 << 4) | 0x00)
        header.append((0x01 << 4) | 0x01)
        header.append(0x00)
        return header
    
    def _generate_audio_default_header(self):
        """生成音频请求头"""
        return self._generate_header()
    
    def _parse_response(self, res: bytes) -> dict:
        """解析响应"""
        try:
            if len(res) < 4:
                return {"error": "响应数据长度不足"}
                
            header = res[:4]
            message_type = header[1] >> 4
            
            if message_type == 0x0F:
                code = int.from_bytes(res[4:8], "big", signed=False)
                msg_length = int.from_bytes(res[8:12], "big", signed=False)
                error_msg = json.loads(res[12:].decode("utf-8"))
                return {
                    "code": code,
                    "msg_length": msg_length,
                    "payload_msg": error_msg
                }
                
            try:
                json_data = res[12:].decode("utf-8")
                return {"payload_msg": json.loads(json_data)}
            except (UnicodeDecodeError, json.JSONDecodeError):
                return {"error": "JSON解析失败"}
                
        except Exception:
            return {"error": "解析响应失败"}
    
    def _calculate_result(self, service_name, latencies, test_count):
        """计算结果"""
        valid_latencies = [l for l in latencies if l > 0]
        if valid_latencies:
            avg_latency = sum(valid_latencies) / len(valid_latencies)
            status = f"成功（{len(valid_latencies)}/{test_count}次有效）"
        else:
            avg_latency = 0
            status = "失败: 所有测试均失败"
        return {"name": service_name, "latency": avg_latency, "status": status}
    
    def _print_results(self, test_count):
        """打印测试结果"""
        if not self.results:
            print("没有有效的ASR测试结果")
            return

        print(f"\n{'='*60}")
        print("流式ASR首词响应时间测试结果")
        print(f"{'='*60}")
        print(f"测试次数: 每个ASR服务测试 {test_count} 次")

        # 排序结果：成功优先，按延迟升序
        success_results = sorted(
            [r for r in self.results if "成功" in r["status"]],
            key=lambda x: x["latency"]
        )
        failed_results = [r for r in self.results if "成功" not in r["status"]]

        table_data = [
            [r["name"], f"{r['latency']:.3f}", r["status"]]
            for r in success_results + failed_results
        ]

        print(tabulate(table_data, headers=["ASR服务", "首词延迟(秒)", "状态"], tablefmt="grid"))
        print("\n测试说明：测量从发送请求到接收第一个识别结果的时间，取多次测试平均值")
        print("- 超时控制: 单个请求最大等待时间为10秒")
        print("- 错误处理: 无法连接和超时的列为网络错误")
        print("- 排序规则: 按平均耗时从快到慢排序")
    
    async def run(self, test_count=5):
        """执行测试"""
        print(f"开始流式ASR首词响应时间测试...")
        print(f"每个ASR服务测试次数: {test_count}次")
        
        if not self.config.get("ASR"):
            print("配置文件中未找到ASR配置")
            return
        
        # 测试每种ASR服务
        self.results = []
        
        # 测试豆包ASR
        if self.config["ASR"].get("DoubaoStreamASR"):
            result = await self.test_doubao_stream_asr(test_count)
            self.results.append(result)
        else:
            print("配置文件中未找到豆包流式ASR配置，跳过测试")
        
        # 测试阿里云ASR
        if self.config["ASR"].get("AliyunStreamASR"):
            result = await self.test_aliyun_stream_asr(test_count)
            self.results.append(result)
        else:
            print("配置文件中未找到阿里云流式ASR配置，跳过测试")
        
        # 打印结果
        self._print_results(test_count)

async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="流式ASR首词响应时间测试工具")
    parser.add_argument("--count", type=int, default=5, help="测试次数")
    
    args = parser.parse_args()
    await DoubaoStreamASRPerformanceTester().run(args.count)

if __name__ == "__main__":
    import os
    import gzip
    import opuslib_next
    asyncio.run(main())