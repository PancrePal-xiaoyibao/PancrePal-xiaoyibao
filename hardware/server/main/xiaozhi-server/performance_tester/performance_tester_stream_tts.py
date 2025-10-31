import asyncio
import time
import json
import uuid
import aiohttp
import websockets
from tabulate import tabulate
from config.settings import load_config

description = "流式TTS语音合成首词耗时测试"
class StreamTTSPerformanceTester:
    def __init__(self):
        self.config = load_config()
        self.test_texts = [
            "你好，这是一句话。"
        ]
        self.results = []
    
    async def test_aliyun_tts(self, text=None, test_count=5):
        """测试阿里云流式TTS首词延迟（测试多次取平均）"""
        text = text or self.test_texts[0]
        latencies = []
        
        for i in range(test_count):
            try:
                tts_config = self.config["TTS"]["AliyunStreamTTS"]
                appkey = tts_config["appkey"]
                token = tts_config["token"]
                voice = tts_config["voice"]
                host = tts_config["host"]
                ws_url = f"wss://{host}/ws/v1"

                start_time = time.time()
                async with websockets.connect(ws_url, extra_headers={"X-NLS-Token": token}) as ws:
                    task_id = str(uuid.uuid4())
                    message_id = str(uuid.uuid4())
                    
                    start_request = {
                        "header": {
                            "message_id": message_id,
                            "task_id": task_id,
                            "namespace": "FlowingSpeechSynthesizer",
                            "name": "StartSynthesis",
                            "appkey": appkey,
                        },
                        "payload": {
                            "voice": voice,
                            "format": "pcm",
                            "sample_rate": 16000,
                            "volume": 50,
                            "speech_rate": 0,
                            "pitch_rate": 0,
                        }
                    }
                    await ws.send(json.dumps(start_request))
                    
                    start_response = json.loads(await ws.recv())
                    if start_response["header"]["name"] != "SynthesisStarted":
                        raise Exception("启动合成失败")
                    
                    run_request = {
                        "header": {
                            "message_id": str(uuid.uuid4()),
                            "task_id": task_id,
                            "namespace": "FlowingSpeechSynthesizer",
                            "name": "RunSynthesis",
                            "appkey": appkey,
                        },
                        "payload": {"text": text}
                    }
                    await ws.send(json.dumps(run_request))
                    
                    while True:
                        response = await ws.recv()
                        if isinstance(response, bytes):
                            latency = time.time() - start_time
                            latencies.append(latency)
                            break
                        elif isinstance(response, str):
                            data = json.loads(response)
                            if data["header"]["name"] == "TaskFailed":
                                raise Exception(f"合成失败: {data['payload']['error_info']}")
                    
            except Exception as e:
                latencies.append(0)
        
        return self._calculate_result("阿里云TTS", latencies, test_count)

    async def test_doubao_tts(self, text=None, test_count=5):
        """测试火山引擎流式TTS首词延迟（测试多次取平均）"""
        text = text or self.test_texts[0]
        latencies = []
        
        for i in range(test_count):
            try:
                tts_config = self.config["TTS"]["HuoshanDoubleStreamTTS"]
                ws_url = tts_config["ws_url"]
                app_id = tts_config["appid"]
                access_token = tts_config["access_token"]
                resource_id = tts_config["resource_id"]
                speaker = tts_config["speaker"]

                start_time = time.time()
                ws_header = {
                    "X-Api-App-Key": app_id,
                    "X-Api-Access-Key": access_token,
                    "X-Api-Resource-Id": resource_id,
                    "X-Api-Connect-Id": str(uuid.uuid4()),
                }
                async with websockets.connect(ws_url, additional_headers=ws_header, max_size=1000000000) as ws:
                    session_id = uuid.uuid4().hex
                    
                    # 发送会话启动请求
                    header = bytes([
                        (0b0001 << 4) | 0b0001, 
                        0b0001 << 4 | 0b100,     
                        0b0001 << 4 | 0b0000,    
                        0                         
                    ])
                    optional = bytearray()
                    optional.extend((1).to_bytes(4, "big", signed=True))
                    session_id_bytes = session_id.encode()
                    optional.extend(len(session_id_bytes).to_bytes(4, "big", signed=True))
                    optional.extend(session_id_bytes)
                    payload = json.dumps({"speaker": speaker}).encode()
                    await ws.send(header + optional + len(payload).to_bytes(4, "big", signed=True) + payload)
                    
                    # 发送文本
                    header = bytes([
                        (0b0001 << 4) | 0b0001, 
                        0b0001 << 4 | 0b100,     
                        0b0001 << 4 | 0b0000,    
                        0                        
                    ])
                    optional = bytearray()
                    optional.extend((200).to_bytes(4, "big", signed=True))
                    session_id_bytes = session_id.encode()
                    optional.extend(len(session_id_bytes).to_bytes(4, "big", signed=True))
                    optional.extend(session_id_bytes)
                    payload = json.dumps({"text": text, "speaker": speaker}).encode()
                    await ws.send(header + optional + len(payload).to_bytes(4, "big", signed=True) + payload)
                    
                    first_chunk = await ws.recv()
                    latency = time.time() - start_time
                    latencies.append(latency)
                    
            except Exception as e:
                latencies.append(0)
        
        return self._calculate_result("火山引擎TTS", latencies, test_count)

    async def test_paddlespeech_tts(self, text=None, test_count=5):
        """测试PaddleSpeech流式TTS首词延迟（测试多次取平均）"""
        text = text or self.test_texts[0]
        latencies = []
        
        for i in range(test_count):
            try:
                tts_config = self.config["TTS"]["PaddleSpeechTTS"]
                tts_url = tts_config["url"]
                spk_id = tts_config["spk_id"]
                speed = tts_config["speed"]
                volume = tts_config["volume"]

                start_time = time.time()
                async with websockets.connect(tts_url) as ws:
                    # 发送开始请求
                    await ws.send(json.dumps({
                        "task": "tts",
                        "signal": "start"
                    }))
                    
                    start_response = json.loads(await ws.recv())
                    if start_response.get("status") != 0:
                        raise Exception("连接失败")
                    
                    # 发送文本数据
                    await ws.send(json.dumps({
                        "text": text,
                        "spk_id": spk_id,
                        "speed": speed,
                        "volume": volume
                    }))
                    
                    # 接收第一个数据块
                    first_chunk = await ws.recv()
                    latency = time.time() - start_time
                    latencies.append(latency)
                    
                    # 发送结束请求
                    end_request = {
                        "task": "tts",
                        "signal": "end"
                    }
                    await ws.send(json.dumps(end_request))
                    
                    # 确保连接正常关闭
                    try:
                        await ws.recv()
                    except websockets.exceptions.ConnectionClosedOK:
                        pass
                        
            except Exception as e:
                latencies.append(0)
        
        return self._calculate_result("PaddleSpeechTTS", latencies, test_count)
            
    async def test_indexstream_tts(self, text=None, test_count=5):
        """测试IndexStream流式TTS首词延迟（测试多次取平均）"""
        text = text or self.test_texts[0]
        latencies = []
        
        for i in range(test_count):
            try:
                tts_config = self.config["TTS"]["IndexStreamTTS"]
                api_url = tts_config.get("api_url")
                voice = tts_config.get("voice")
                
                start_time = time.time()
                
                async with aiohttp.ClientSession() as session:
                    payload = {"text": text, "character": voice}
                    async with session.post(api_url, json=payload, timeout=10) as resp:
                        if resp.status != 200:
                            raise Exception(f"请求失败: {resp.status}, {await resp.text()}")
                        
                        async for chunk in resp.content.iter_any():
                            data = chunk[0] if isinstance(chunk, (list, tuple)) else chunk
                            if not data:
                                continue
                            
                            latency = time.time() - start_time
                            latencies.append(latency)
                            resp.close()
                            break
                        else:
                            latencies.append(0)
                            
            except Exception as e:
                latencies.append(0)
        
        return self._calculate_result("IndexStreamTTS", latencies, test_count)

    async def test_linkerai_tts(self, text=None, test_count=5):
        """测试Linkerai流式TTS首词延迟（测试多次取平均）"""
        text = text or self.test_texts[0]
        latencies = []
        
        for i in range(test_count):
            try:
                tts_config = self.config["TTS"]["LinkeraiTTS"]
                api_url = tts_config["api_url"]
                access_token = tts_config["access_token"]
                voice = tts_config["voice"]
                
                start_time = time.time()
                async with aiohttp.ClientSession() as session:
                    params = {
                        "tts_text": text,
                        "spk_id": voice,
                        "frame_durition": 60,
                        "stream": "true",
                        "target_sr": 16000,
                        "audio_format": "pcm",
                        "instruct_text": "请生成一段自然流畅的语音",
                    }
                    headers = {
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json",
                    }
                    
                    async with session.get(api_url, params=params, headers=headers, timeout=10) as resp:
                        if resp.status != 200:
                            raise Exception(f"请求失败: {resp.status}, {await resp.text()}")
                        
                        # 接收第一个数据块
                        async for _ in resp.content.iter_any():
                            latency = time.time() - start_time
                            latencies.append(latency)
                            break
                        else:
                            latencies.append(0)
                            
            except Exception as e:
                latencies.append(0)
        
        return self._calculate_result("LinkeraiTTS", latencies, test_count)


    def _calculate_result(self, service_name, latencies, test_count):
        """计算测试结果"""
        valid_latencies = [l for l in latencies if l > 0]
        if valid_latencies:
            avg_latency = sum(valid_latencies) / len(valid_latencies)
            status = f"成功（{len(valid_latencies)}/{test_count}次有效）"
        else:
            avg_latency = 0
            status = "失败: 所有测试均失败"
        return {"name": service_name, "latency": avg_latency, "status": status}

    def _print_results(self, test_text, test_count):
        """打印测试结果"""
        if not self.results:
            print("没有有效的TTS测试结果")
            return

        print(f"\n{'='*60}")
        print("流式TTS首词延迟测试结果")
        print(f"{'='*60}")
        print(f"测试文本: {test_text}")
        print(f"测试次数: 每个TTS服务测试 {test_count} 次")

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

        print(tabulate(table_data, headers=["TTS服务", "首词延迟(秒)", "状态"], tablefmt="grid"))
        print("\n测试说明：测量从发送请求到接收第一个音频数据块的时间，取多次测试平均值")
        print("- 超时控制: 单个请求最大等待时间为10秒")
        print("- 错误处理: 无法连接和超时的列为网络错误")
        print("- 排序规则: 按平均耗时从快到慢排序")


    async def run(self, test_text=None, test_count=5):
        """执行测试
        
        Args:
            test_text: 要测试的文本，如果为None则使用默认文本
            test_count: 每个TTS服务的测试次数
        """
        test_text = test_text or self.test_texts[0]
        print(f"开始流式TTS首词延迟测试...")
        print(f"测试文本: {test_text}")
        print(f"每个TTS服务测试次数: {test_count}次")
        
        if not self.config.get("TTS"):
            print("配置文件中未找到TTS配置")
            return
        
        # 测试每种TTS服务
        self.results = []
        
        # 测试阿里云TTS
        result = await self.test_aliyun_tts(test_text, test_count)
        self.results.append(result)
        
        # 测试火山引擎TTS
        result = await self.test_doubao_tts(test_text, test_count)
        self.results.append(result)
        
        # 测试PaddleSpeech TTS
        result = await self.test_paddlespeech_tts(test_text, test_count)
        self.results.append(result)
        
        # 测试Linkerai TTS
        result = await self.test_linkerai_tts(test_text, test_count)
        self.results.append(result)
        
        # 测试IndexStreamTTS
        result = await self.test_indexstream_tts(test_text, test_count)
        self.results.append(result)
        
        # 打印结果
        self._print_results(test_text, test_count)


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="流式TTS首词延迟测试工具")
    parser.add_argument("--text", help="要测试的文本内容")
    parser.add_argument("--count", type=int, default=5, help="每个TTS服务的测试次数")
    
    args = parser.parse_args()
    await StreamTTSPerformanceTester().run(args.text, args.count)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())