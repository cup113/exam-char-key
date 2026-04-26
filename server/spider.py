import httpx
from bs4 import BeautifulSoup
from openai import AsyncOpenAI
from config import settings
from db_helper import get_dict_cache, set_dict_cache

client = AsyncOpenAI(api_key=settings.LLM_API_KEY, base_url=settings.LLM_BASE_URL)

async def scrape_zdic(word: str) -> str:
    """爬取汉典页面，提取文言文字词释义"""
    url = f"https://www.zdic.net/hans/{word}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    async with httpx.AsyncClient(follow_redirects=True, timeout=15) as http:
        resp = await http.get(url, headers=headers)
        resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    # 提取主要内容区域
    sections = []
    for selector in [".content.definitions.jnr", "#xxjs", ".nr-box.nr-box-shiyi.jbjs"]:
        for el in soup.select(selector):
            sections.append(el.get_text(strip=True))

    return "\n".join(sections) if sections else f"未找到「{word}」的释义"


async def structure_dict_data(word: str, raw_text: str) -> str:
    """用预处理模型将原始爬取数据结构化"""
    response = await client.chat.completions.create(
        model=settings.MODEL_DICT_PREPROCESS,
        messages=[
            {
                "role": "system",
                "content": (
                    "你是一个文言文学习数据结构化助手。"
                    "请将用户提供的汉典原始文本整理为结构化JSON格式。"
                    "输出格式（必须为有效JSON）：\n"
                    "{\n"
                    "  \"basic_explanation\": [{\"brief\": string, \"examples\": string[]}],\n"
                    "  \"detailed_explanation\": [{\"brief\": string, \"english\": string, \"examples\": string[]}]\n"
                    "}\n"
                    "“基本解释”放到 `basic_explanation` 中，“详细解释”和“词语解释”放到 `detailed_explanation`中。若无，直接置空对应项。请直接输出JSON，不要其他文字。"
                ),
            },
            {"role": "user", "content": f"词语：{word}\n原始文本：{raw_text}"},
        ],
        response_format={ "type": "json_object" },
        reasoning_effort="low"
    )
    return response.choices[0].message.content or "结构化失败"


async def get_dict_entry(word: str) -> str:
    """完整流程：查缓存 → 爬取 → 结构化 → 写缓存"""
    cached = get_dict_cache(word)
    if cached:
        return cached

    raw = await scrape_zdic(word)
    print(raw)
    structured = await structure_dict_data(word, raw)
    set_dict_cache(word, structured)
    return structured
