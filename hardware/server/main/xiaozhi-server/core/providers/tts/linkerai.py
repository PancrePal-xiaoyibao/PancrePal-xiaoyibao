import os
import queue
import asyncio
import traceback
import aiohttp
from config.logger import setup_logging
from core.utils.tts import MarkdownCleaner
from core.providers.tts.base import TTSProviderBase
from core.utils import opus_encoder_utils, textUtils
from core.providers.tts.dto.dto import SentenceType, ContentType, InterfaceType

TAG = __name__
logger = setup_logging()


class TTSProvider(TTSProviderBase):
    def __init__(self, config, delete_audio_file):
        super().__init__(config, delete_audio_file)
        self.interface_type = InterfaceType.SINGLE_STREAM
        self.access_token = config.get("access_token")
        self.voice = config.get("voice")
        self.api_url = config.get("api_url")
        self.audio_format = "pcm"
        self.before_stop_play_files = []

        # 创建Opus编码器
        self.opus_encoder = opus_encoder_utils.OpusEncoderUtils(
            sample_rate=16000, channels=1, frame_size_ms=60
        )

        # PCM缓冲区
        self.pcm_buffer = bytearray()

    def tts_text_priority_thread(self):
        """流式文本处理线程"""
        while not self.conn.stop_event.is_set():
            try:
                message = self.tts_text_queue.get(timeout=1)
                if message.sentence_type == SentenceType.FIRST:
                    # 初始化参数
                    self.tts_stop_request = False
                    self.processed_chars = 0
                    self.tts_text_buff = []
                    self.before_stop_play_files.clear()
                    self.reset_flow_controller()
                elif ContentType.TEXT == message.content_type:
                    self.tts_text_buff.append(message.content_detail)
                    segment_text = self._get_segment_text()
                    if segment_text:
                        self.to_tts_single_stream(segment_text)

                elif ContentType.FILE == message.content_type:
                    logger.bind(tag=TAG).info(
                        f"添加音频文件到待播放列表: {message.content_file}"
                    )
                    if message.content_file and os.path.exists(message.content_file):
                        # 先处理文件音频数据
                        self._process_audio_file_stream(message.content_file, callback=lambda audio_data: self.handle_audio_file(audio_data, message.content_detail))
                if message.sentence_type == SentenceType.LAST:
                    # 处理剩余的文本
                    self._process_remaining_text_stream(True)

            except queue.Empty:
                continue
            except Exception as e:
                logger.bind(tag=TAG).error(
                    f"处理TTS文本失败: {str(e)}, 类型: {type(e).__name__}, 堆栈: {traceback.format_exc()}"
                )

    def _process_remaining_text_stream(self, is_last=False):
        """处理剩余的文本并生成语音

        Returns:
            bool: 是否成功处理了文本
        """
        full_text = "".join(self.tts_text_buff)
        remaining_text = full_text[self.processed_chars :]
        if remaining_text:
            segment_text = textUtils.get_string_no_punctuation_or_emoji(remaining_text)
            if segment_text:
                self.to_tts_single_stream(segment_text, is_last)
                self.processed_chars += len(full_text)
            else:
                self._process_before_stop_play_files()
        else:
            self._process_before_stop_play_files()

    def to_tts_single_stream(self, text, is_last=False):
        try:
            max_repeat_time = 5
            text = MarkdownCleaner.clean_markdown(text)
            try:
                asyncio.run(self.text_to_speak(text, is_last))
            except Exception as e:
                logger.bind(tag=TAG).warning(
                    f"语音生成失败{5 - max_repeat_time + 1}次: {text}，错误: {e}"
                )
                max_repeat_time -= 1

            if max_repeat_time > 0:
                logger.bind(tag=TAG).info(
                    f"语音生成成功: {text}，重试{5 - max_repeat_time}次"
                )
            else:
                logger.bind(tag=TAG).error(
                    f"语音生成失败: {text}，请检查网络或服务是否正常"
                )
        except Exception as e:
            logger.bind(tag=TAG).error(f"Failed to generate TTS file: {e}")
        finally:
            return None

    ###################################################################################
    # linkerai单流式TTS重写父类的方法--结束
    ###################################################################################

    async def text_to_speak(self, text, is_last):
        """流式处理TTS音频，每句只推送一次音频列表"""
        await self._tts_request(text, is_last)

    async def close(self):
        """资源清理"""
        await super().close()
        if hasattr(self, "opus_encoder"):
            self.opus_encoder.close()

    async def _tts_request(self, text: str, is_last: bool) -> None:
        params = {
            "tts_text": text,
            "spk_id": self.voice,
            "frame_durition": 60,
            "stream": "true",
            "target_sr": 16000,
            "audio_format": "pcm",
            "instruct_text": "请生成一段自然流畅的语音",
        }
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        # 一帧 PCM 所需字节数：60 ms &times; 16 kHz &times; 1 ch &times; 2 B = 1 920
        frame_bytes = int(
            self.opus_encoder.sample_rate
            * self.opus_encoder.channels  # 1
            * self.opus_encoder.frame_size_ms
            / 1000
            * 2
        )  # 16-bit = 2 bytes

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.api_url, params=params, headers=headers, timeout=10
                ) as resp:

                    if resp.status != 200:
                        logger.bind(tag=TAG).error(
                            f"TTS请求失败: {resp.status}, {await resp.text()}"
                        )
                        self.tts_audio_queue.put((SentenceType.LAST, [], None))
                        return

                    self.pcm_buffer.clear()
                    self.tts_audio_queue.put((SentenceType.FIRST, [], text))

                    # 兼容 iter_chunked / iter_chunks / iter_any
                    async for chunk in resp.content.iter_any():
                        data = chunk[0] if isinstance(chunk, (list, tuple)) else chunk
                        if not data:
                            continue

                        # 拼到 buffer
                        self.pcm_buffer.extend(data)

                        # 够一帧就编码
                        while len(self.pcm_buffer) >= frame_bytes:
                            frame = bytes(self.pcm_buffer[:frame_bytes])
                            del self.pcm_buffer[:frame_bytes]

                            self.opus_encoder.encode_pcm_to_opus_stream(
                                frame,
                                end_of_stream=False,
                                callback=self.handle_opus
                            )

                    # flush 剩余不足一帧的数据
                    if self.pcm_buffer:
                        self.opus_encoder.encode_pcm_to_opus_stream(
                            bytes(self.pcm_buffer),
                            end_of_stream=True,
                            callback=self.handle_opus
                        )
                        self.pcm_buffer.clear()

                    # 如果是最后一段，输出音频获取完毕
                    if is_last:
                        self._process_before_stop_play_files()

        except Exception as e:
            logger.bind(tag=TAG).error(f"TTS请求异常: {e}")
            self.tts_audio_queue.put((SentenceType.LAST, [], None))
