from httpx import AsyncClient
from train.models import AiSubject, CompletionSourcePack


class FlashAiSubject(AiSubject):
    async def ask(self, pack: CompletionSourcePack) -> str:
        return await self.get_flash_completion(pack)


class OnlineAiSubject(AiSubject):
    async def ask(self, pack: CompletionSourcePack) -> str:
        return await self.get_online_completion(pack)


class EckFlashSubject(FlashAiSubject):
    model_code = "qwen3-8b-ft-202508061056-4a88"
    model_name = "eck-flash"


class EckThinkingSubject(OnlineAiSubject):
    model_code = "qwen3-8b-ft-202508061132-1695"
    model_name = "eck-thinking"


class AiTaiyanSubject(AiSubject):
    model_code = "taiyan"
    model_name = "taiyan"

    async def ask(self, pack: CompletionSourcePack) -> str:
        text = f"{pack.context}@@@@@{pack.query}"
        cache_key = f"TAIYAN@@{text}"
        cached = pack.cache_handler.query_cache(cache_key)
        if cached:
            return cached

        content = await AsyncClient().post(
            "https://t.shenshen.wiki/shiyi",
            headers={
                "Origin": "https://t.shenshen.wiki",
                "Referer": "https://t.shenshen.wiki/",
            },
            json={"mission": "shiyi", "text": text},
        )
        pack.cache_handler.save_cache(cache_key, content.text)
        return content.text


class Qwen8BSubject(OnlineAiSubject):
    model_code = "qwen3-8b"
    model_name = "qwen3-8b"


class Qwen8BFlashSubject(FlashAiSubject):
    model_code = "qwen3-8b"
    model_name = "qwen3-8b-flash"


class QwenFlashSubject(FlashAiSubject):
    model_code = "qwen-flash"
    model_name = "qwen-flash"


class QwenLongSubject(OnlineAiSubject):
    model_code = "qwen-long-latest"
    model_name = "qwen-long"


class QwenLongFlashSubject(FlashAiSubject):
    model_code = "qwen-long-latest"
    model_name = "qwen-long-flash"


class DeepSeekV3Subject(OnlineAiSubject):
    model_code = "deepseek-v3"
    model_name = "deepseek-v3"
