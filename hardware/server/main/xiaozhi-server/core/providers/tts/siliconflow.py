import requests
from core.providers.tts.base import TTSProviderBase


class TTSProvider(TTSProviderBase):
    def __init__(self, config, delete_audio_file):
        super().__init__(config, delete_audio_file)
        self.model = config.get("model")
        self.access_token = config.get("access_token")
        if config.get("private_voice"):
            self.voice = config.get("private_voice")
        else:
            self.voice = config.get("voice")
        self.response_format = config.get("response_format", "mp3")
        self.audio_file_type = config.get("response_format", "mp3")
        self.sample_rate = config.get("sample_rate")
        self.speed = float(config.get("speed", 1.0))
        self.gain = config.get("gain")

        self.host = "api.siliconflow.cn"
        self.api_url = f"https://{self.host}/v1/audio/speech"

    async def text_to_speak(self, text, output_file):
        request_json = {
            "model": self.model,
            "input": text,
            "voice": self.voice,
            "response_format": self.response_format,
        }
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        try:
            response = requests.request(
                "POST", self.api_url, json=request_json, headers=headers
            )
            data = response.content
            if output_file:
                with open(output_file, "wb") as file_to_save:
                    file_to_save.write(data)
            else:
                return data
        except Exception as e:
            raise Exception(f"{__name__} error: {e}")
