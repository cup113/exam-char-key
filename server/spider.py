import httpx
from bs4 import BeautifulSoup  # pyright: ignore[reportMissingTypeStubs]
from openai import AsyncOpenAI
from config import settings
from db_helper import get_dict_cache, set_dict_cache
from log_helper import get_logger
from prompt import ZDIC_STRUCTURE_PROMPT

logger = get_logger("spider")

client = AsyncOpenAI(api_key=settings.LLM_API_KEY, base_url=settings.LLM_BASE_URL)


async def scrape_zdic(word: str) -> str:
    """爬取汉典页面，提取文言文字词释义"""
    url = f"https://www.zdic.net/hans/{word}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    logger.info("爬取汉典 | word=%s", word)
    async with httpx.AsyncClient(follow_redirects=True, timeout=15) as http:
        resp = await http.get(url, headers=headers)
        resp.raise_for_status()
    logger.debug("爬取成功 | word=%s | status=%d | size=%d", word, resp.status_code, len(resp.text))

    soup = BeautifulSoup(resp.text, "html.parser")

    # 提取主要内容区域
    sections: list[str] = []
    for selector in [".content.definitions.jnr", "#xxjs", ".nr-box.nr-box-shiyi.jbjs"]:
        for el in soup.select(selector):  # pyright: ignore
            sections.append(el.get_text(strip=True))  # type: ignore

    return "\n".join(sections) if sections else f"未找到「{word}」的释义"


async def structure_dict_data(word: str, raw_text: str) -> str:
    """用预处理模型将原始爬取数据结构化"""
    response = await client.chat.completions.create(
        model=settings.MODEL_DICT_PREPROCESS,
        messages=[
            {
                "role": "system",
                "content": ZDIC_STRUCTURE_PROMPT,
            },
            {"role": "user", "content": raw_text},
        ],
        response_format={"type": "json_object"},
        reasoning_effort="low",
    )
    return response.choices[0].message.content or "结构化失败"


async def get_dict_entry(word: str) -> str:
    """完整流程：查缓存 → 爬取 → 结构化 → 写缓存"""
    cached = get_dict_cache(word)
    if cached:
        logger.debug("字典缓存命中 | word=%s", word)
        return cached

    logger.info("字典缓存未命中，开始爬取 | word=%s", word)
    raw = await scrape_zdic(word)
    logger.info("爬取原始数据 | word=%s | raw=%s", word, raw)
    structured = await structure_dict_data(word, raw)
    set_dict_cache(word, structured)
    logger.info("字典数据已缓存 | word=%s | data_len=%d", word, len(structured))
    return structured
