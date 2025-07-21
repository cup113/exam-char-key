from pocketbase import PocketBase
from pocketbase.models.errors import PocketBaseNotFoundError
from os import getenv
from .logging_service import main_logger


class PocketBaseService:
    def __init__(self):
        pocketbase_url = getenv("POCKETBASE_URL")
        if pocketbase_url is None:
            raise KeyError("POCKETBASE_URL not set.")
        self.pb = PocketBase(pocketbase_url)
        self.zdic_cache = self.pb.collection("zdicCache")

    @classmethod
    def sanitize(cls, word: str):
        FORBIDDEN_CHARACTERS = {"'", '"'}
        return "".join(c for c in word if c not in FORBIDDEN_CHARACTERS)

    async def insert_cache(self, query: str, content: str):
        size_kb = len(bytes(content, encoding="utf-8")) / 1024
        main_logger.info(f"ZDic Cache created ({query}, {size_kb:.2f} KB)")
        return await self.zdic_cache.create(
            params={
                "query": query,
                "content": content,
            }
        )

    async def retrieve_cache(self, query: str):
        try:
            cache = await self.zdic_cache.get_first(
                options={"filter": f"query='{self.sanitize(query)}'"}
            )
            main_logger.info(f"ZDic Cache Retrieved ({query})")
            return cache
        except PocketBaseNotFoundError:
            return None
