from dataclasses import dataclass
from dataclasses_json import dataclass_json
from json import dumps, loads
from httpx import AsyncClient
from bs4 import BeautifulSoup
from urllib.parse import quote
from .pocketbase_service import PocketBaseService

ZDIC_URL = "https://www.zdic.net/hans/"

@dataclass_json
@dataclass
class ZDicExplanations:
    basic: list[str]
    detailed: list[str]
    phrase: list[str]

    @staticmethod
    def from_dict(_d: dict[str, list[str]]) -> "ZDicExplanations": ...

    def to_dict(self) -> dict[str, list[str]]: ...


@dataclass_json
@dataclass
class ZDicResult:
    basic_explanations: list[str]
    detailed_explanations: list[str]
    phrase_explanations: list[str]
    zdic_prompt: str
    cached: bool

    @staticmethod
    def from_dict(_d: dict[str, list[str] | str | bool]) -> "ZDicResult": ...

    def to_dict(self) -> dict[str, list[str] | str | bool]: ...


class ZDicService:
    def __init__(self):
        self.zdic_url = ZDIC_URL

    async def get_result(self, word: str) -> ZDicResult | None:
        pocketbase = PocketBaseService()
        cache = await pocketbase.retrieve_cache(word)

        if cache is None:
            response = await self.request_zdic(word)
            explanations = self.parse_zdic_response(response)
            await pocketbase.insert_cache(
                word, dumps(explanations.to_dict(), ensure_ascii=False)
            )
            cached = False
        else:
            content = cache.get("content")
            if content is None:
                return None
            explanations = ZDicExplanations.from_dict(loads(content))
            cached = True

        return self.get_final_response(explanations, cached)

    async def request_zdic(self, word: str):
        async with AsyncClient() as client:
            response = await client.get(self.zdic_url + quote(word), timeout=10)
            if response.status_code == 200:
                return response.text
            return f"Error {response.status_code}: {response.text}"

    def parse_zdic_response(self, zdic_response: str) -> ZDicExplanations:
        soup = BeautifulSoup(zdic_response, "html.parser")

        basic = [
            li.get_text()
            for li in soup.select(".zdict div.content.definitions.jnr>ol>li")  # type: ignore
        ]
        detailed = [
            p.get_text() for p in soup.select("#xxjs div.content.definitions.xnr>p")  # type: ignore
        ]
        phrase = [
            p.get_text() for p in soup.select(".nr-box div.content.definitions .jnr>p")  # type: ignore
        ]

        return ZDicExplanations(basic=basic, detailed=detailed, phrase=phrase)

    def get_final_response(self, explanations: ZDicExplanations, cached: bool) -> ZDicResult:
        basic_explanations = explanations.basic
        detailed_explanations = explanations.detailed
        phrase_explanations = explanations.phrase

        prompt_basic = (
            (
                "【基本解释】\n"
                + "\n".join(
                    f"{i + 1}. {exp}" for i, exp in enumerate(basic_explanations)
                )
                + "\n"
            )
            if basic_explanations
            else ""
        )
        prompt_detailed = (
            ("【详细解释】\n" + "\n".join(detailed_explanations) + "\n")
            if detailed_explanations
            else ""
        )
        prompt_phrase = (
            ("【词语解释】\n" + "\n".join(phrase_explanations) + "\n")
            if phrase_explanations
            else ""
        )

        zdic_prompt = prompt_basic + prompt_detailed + prompt_phrase
        zdic_prompt = (
            f"\n汉典给出的解释有：\n{zdic_prompt}"
            if zdic_prompt.strip()
            else "汉典未给出解释"
        )

        return ZDicResult(
            basic_explanations=basic_explanations,
            detailed_explanations=detailed_explanations,
            phrase_explanations=phrase_explanations,
            zdic_prompt=zdic_prompt,
            cached=cached
        )
