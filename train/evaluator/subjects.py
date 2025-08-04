from httpx import AsyncClient
from train.models import AiSubject, CompletionSourcePack


class FlashAiSubject(AiSubject):
    async def ask(self, pack: CompletionSourcePack) -> str:
        return await self.get_flash_completion(pack)


class OnlineAiSubject(AiSubject):
    async def ask(self, pack: CompletionSourcePack) -> str:
        return await self.get_online_completion(pack)


class EckFlashSubject(FlashAiSubject):
    model_code = "qwen3-8b-ft-202508031744-1c46"
    model_name = "eck-flash"


class EckThinkingSubject(OnlineAiSubject):
    model_code = "qwen3-8b-ft-202508041131-e7d8"
    model_name = "eck-thinking"


class AiTaiyanSubject(AiSubject):
    model_code = "taiyan"
    model_name = "taiyan"

    async def ask(self, pack: CompletionSourcePack) -> str:
        content = await AsyncClient().post(
            "https://t.shenshen.wiki/shiyi",
            headers={
                "Origin": "https://t.shenshen.wiki",
                "Referer": "https://t.shenshen.wiki/",
            },
            json={"mission": "shiyi", "text": f"{pack.context}@@@@@{pack.query}"},
        )
        return content.text


class Qwen8BSubject(OnlineAiSubject):
    model_code = "qwen3-8b"
    model_name = "qwen3-8b"


class Qwen8BFlashSubject(FlashAiSubject):
    model_code = "qwen3-8b"
    model_name = "qwen3-8b-flash"


class QwenLongSubject(OnlineAiSubject):
    model_code = "qwen-long-latest"
    model_name = "qwen-long"


class QwenPlusSubject(OnlineAiSubject):
    model_code = "qwen-plus-latest"
    model_name = "qwen-plus"


class QwenPlusFlashSubject(FlashAiSubject):
    model_code = "qwen-plus-latest"
    model_name = "qwen-plus-flash"


class DeepSeekV3Subject(OnlineAiSubject):
    model_code = "deepseek-v3"
    model_name = "deepseek-v3"
