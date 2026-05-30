import json
import httpx
from bs4 import BeautifulSoup  # pyright: ignore[reportMissingTypeStubs]
from openai import AsyncOpenAI
from config import settings
from db_helper import get_dict_cache, set_dict_cache, check_and_decrease_quota
from log_helper import get_logger
from prompt import ZDIC_STRUCTURE_PROMPT

logger = get_logger("spider")

client = AsyncOpenAI(api_key=settings.LLM_API_KEY, base_url=settings.LLM_BASE_URL)

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0"
}


# ── Direct HTML parsers (new zdic.net UI) ──────────────────────────


def _parse_char_section(soup: BeautifulSoup) -> dict:
    """解析汉字页面（如 國、贲）"""
    result: dict = {
        "pinyin": [],
        "zhuyin": [],
        "radical": "",
        "strokes": 0,
        "basic_explanation": [],
        "detailed_explanation": [],
    }

    meta = soup.select_one(".char-card__main .char-meta")
    if meta:
        for py_el in meta.select(".meta-pinyin"):
            txt = py_el.get_text(strip=True)
            if txt:
                result["pinyin"].append(txt)
        for zy_el in meta.select(".meta-zhuyin"):
            txt = zy_el.get_text(strip=True)
            if txt:
                result["zhuyin"].append(txt)
        rad_el = meta.select_one(".meta-radical")
        if rad_el:
            result["radical"] = rad_el.get_text(strip=True)
        for span in meta.select(".meta-badge"):
            if "总笔画" in span.get_text(strip=True):
                nxt = span.find_next_sibling()
                if nxt:
                    try:
                        result["strokes"] = int(nxt.get_text(strip=True))
                    except ValueError:
                        pass

    # 基本解释 #jbjs
    jbjs = soup.select_one("#jbjs")
    if jbjs:
        for item in jbjs.select(".jbjs-item"):
            def_el = item.select_one(".jbjs-item__def")
            if not def_el:
                continue
            brief = def_el.get_text(" ", strip=True)
            examples = []
            eg_el = item.select_one(".jbjs-item__eg")
            if eg_el:
                examples.append(eg_el.get_text(strip=True))
            result["basic_explanation"].append(
                {
                    "brief": brief,
                    "examples": examples,
                }
            )

    # 详细解释 #xxjs
    xxjs = soup.select_one("#xxjs")
    if xxjs:
        for pos_section in xxjs.select(".xxjs-pos-section"):
            pos_badge = pos_section.select_one(".xxjs-pos-badge")
            pos = pos_badge.get_text(strip=True) if pos_badge else ""
            for item in pos_section.select(".xxjs-item"):
                def_el = item.select_one(".xxjs-item__def")
                if not def_el:
                    continue
                brief = def_el.get_text(" ", strip=True)

                citations = []
                for cit_item in item.select(".xxjs-citation__item"):
                    text_el = cit_item.select_one(".xxjs-citation__text")
                    source_el = cit_item.select_one(".xxjs-citation__source")
                    text = text_el.get_text(strip=True) if text_el else ""
                    source = source_el.get_text(strip=True) if source_el else ""
                    if text and source:
                        citations.append(f"{text}——{source}")
                    elif text:
                        citations.append(text)

                examples = []
                also_el = item.select_one(".xxjs-also")
                if also_el:
                    also_text = also_el.select_one(".xxjs-also__text")
                    if also_text:
                        examples.append(also_text.get_text(strip=True))

                english = ""
                en_el = item.select_one(".xxjs-english")
                if en_el:
                    en_text = en_el.select_one(".xxjs-english__text")
                    if en_text:
                        english = en_text.get_text(strip=True)
                # TODO: zdic.net 部分义项缺 .xxjs-english 元素，但 brief 内嵌 [English]
                #       如「二的大写 [two]——用于会计账中以防伪造」。可考虑用正则
                #       \[([A-Za-z ;,./-]+)\] 提取作为 fallback English。

                result["detailed_explanation"].append(
                    {
                        "brief": brief,
                        "pos": pos,
                        "english": english,
                        "citations": citations,
                        "examples": examples,
                    }
                )

    return result


def _parse_word_section(soup: BeautifulSoup) -> dict:
    """解析词语页面（如 明府）"""
    result: dict = {
        "word": "",
        "pinyin": [],
        "zhuyin": [],
        "basic_explanation": [],
        "detailed_explanation": [],
    }

    headword = soup.select_one(".word-headword-row")
    if headword:
        result["word"] = headword.get_text(strip=True)

    for py_el in soup.select(".word-pronun-text .meta-pinyin"):
        txt = py_el.get_text(strip=True)
        if txt:
            result["pinyin"].append(txt)

    for zy_el in soup.select(".word-pronun-text .meta-zhuyin"):
        txt = zy_el.get_text(strip=True)
        if txt:
            result["zhuyin"].append(txt)

    xxjs = soup.select_one("#xxjs")
    if xxjs:
        for item in xxjs.select(".xxjs-item"):
            def_el = item.select_one(".xxjs-item__def")
            if not def_el:
                continue
            brief = def_el.get_text(" ", strip=True)

            citations = []
            for cit_item in item.select(".xxjs-citation__item"):
                text_el = cit_item.select_one(".xxjs-citation__text")
                source_el = cit_item.select_one(".xxjs-citation__source")
                text = text_el.get_text(strip=True) if text_el else ""
                source = source_el.get_text(strip=True) if source_el else ""
                if text and source:
                    citations.append(f"{text}——{source}")
                elif text:
                    citations.append(text)

            english = ""
            en_el = item.select_one(".xxjs-english")
            if en_el:
                en_text = en_el.select_one(".xxjs-english__text")
                if en_text:
                    english = en_text.get_text(strip=True)

            result["detailed_explanation"].append(
                {
                    "brief": brief,
                    "pos": "",
                    "english": english,
                    "citations": citations,
                    "examples": [],
                }
            )

    return result


def parse_zdic_html(resp_text: str) -> dict | None:
    """尝试直接解析新汉典 HTML，成功返回结构化 dict，失败返回 None。"""
    soup = BeautifulSoup(resp_text, "html.parser")

    # 404 / 无内容
    has_char_card = bool(soup.select_one(".char-card"))
    has_word_row = bool(soup.select_one(".word-headword-row"))
    if not has_char_card and not has_word_row:
        return None

    if has_word_row and not has_char_card:
        return _parse_word_section(soup)
    return _parse_char_section(soup)


# ── LLM fallback (kept for edge cases) ────────────────────────────


async def structure_dict_data(word: str, raw_text: str) -> str:
    """用预处理模型将原始爬取数据结构化（fallback）。"""
    response = await client.chat.completions.create(
        model=settings.MODEL_DICT_PREPROCESS,
        messages=[
            {"role": "system", "content": ZDIC_STRUCTURE_PROMPT},
            {"role": "user", "content": raw_text},
        ],
        response_format={"type": "json_object"},
        reasoning_effort="low",
    )
    return response.choices[0].message.content or "结构化失败"


# ── Public API ────────────────────────────────────────────────────


async def scrape_zdic(word: str, identifier: str = "", limit: int = 200) -> str:
    """爬取汉典页面，优先直接解析 HTML，失败时回退到 LLM 结构化。

    identifier: 回退 LLM 时扣额度的用户标识，为空时不扣。
    """
    url = f"https://www.zdic.net/hans/{word}"
    logger.info("爬取汉典 | word=%s", word)
    async with httpx.AsyncClient(
        follow_redirects=True, timeout=settings.ZDIC_TIMEOUT
    ) as http:
        resp = await http.get(url, headers=_HEADERS)
        if resp.status_code == 404:
            return '{"basic_explanation":[],"detailed_explanation":[]}'
        resp.raise_for_status()
    logger.debug(
        "爬取成功 | word=%s | status=%d | size=%d",
        word,
        resp.status_code,
        len(resp.text),
    )

    parsed = parse_zdic_html(resp.text)
    if parsed is not None:
        logger.info("HTML 直接解析成功 | word=%s", word)
        return json.dumps(parsed, ensure_ascii=False)

    # 回退 LLM：有 identifier 时先扣 4 额度（成本 ~$0.01/word，促使用户反馈 parser 失效）
    if identifier and not check_and_decrease_quota(identifier, limit, 4):
        logger.warning("LLM 回退额度不足 | word=%s | identifier=%s", word, identifier)
        return '{"basic_explanation":[],"detailed_explanation":[]}'
    logger.info("HTML 解析失败，回退 LLM | word=%s | identifier=%s", word, identifier)
    soup = BeautifulSoup(resp.text, "html.parser")
    sections: list[str] = []
    for selector in [".content.definitions.jnr", "#xxjs", ".nr-box.nr-box-shiyi.jbjs"]:
        for el in soup.select(selector):
            sections.append(el.get_text(strip=True))
    raw = "\n".join(sections) if sections else f"未找到「{word}」的释义"
    return await structure_dict_data(word, raw)


async def get_dict_entry(word: str, identifier: str = "", limit: int = 200) -> str:
    """完整流程：查缓存 → 爬取（解析优先） → 写缓存"""
    cached = get_dict_cache(word)
    if cached:
        logger.debug("字典缓存命中 | word=%s", word)
        return cached

    logger.info("字典缓存未命中，开始爬取 | word=%s", word)
    structured = await scrape_zdic(word, identifier, limit)
    set_dict_cache(word, structured)
    logger.info("字典数据已缓存 | word=%s | data_len=%d", word, len(structured))
    return structured


def format_dict_for_prompt(dict_data_json: str) -> str:
    """将结构化的JSON字典数据转换为LLM易读的文本格式（兼容新旧 schema）。"""
    try:
        data = json.loads(dict_data_json)
    except json.JSONDecodeError:
        return dict_data_json

    lines: list[str] = []
    basic = data.get("basic_explanation", [])
    if basic:
        lines.append("【基本解释】")
        for item in basic:
            brief = item.get("brief", "")
            examples = item.get("examples", [])
            if examples:
                lines.append(f"  {brief}（例：{'；'.join(examples)}）")
            else:
                lines.append(f"  {brief}")

    detailed = data.get("detailed_explanation", [])
    if detailed:
        lines.append("【详细解释】")
        for item in detailed:
            parts = []
            pos = item.get("pos", "")
            if pos:
                parts.append(f"[{pos}]")
            brief = item.get("brief", "")
            parts.append(brief)
            english = item.get("english", "")
            if english:
                parts.append(f"[{english}]")

            # 优先展示 citations（新 schema），其次 examples（旧 schema）
            citations = item.get("citations", [])
            examples = item.get("examples", [])
            if citations:
                parts.append(f"书证：{'；'.join(citations)}")
            if examples:
                parts.append(f"例：{'；'.join(examples)}")

            lines.append("  " + " ".join(parts))

    return "\n".join(lines)
