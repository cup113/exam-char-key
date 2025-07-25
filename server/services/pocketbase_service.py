from pocketbase import PocketBase
from pocketbase.models.dtos import AuthResult, Record
from pocketbase.models.errors import PocketBaseNotFoundError

from os import getenv
from tqdm import tqdm
from datetime import datetime, timezone
from asyncio import gather
from typing import Coroutine, Any

from server.services.logging_service import main_logger
from server.config import Config, Roles
from server.models import Role, FreqInfo, CorpusStatItem, CorpusItem, UserRaw


class NotEnoughBalanceError(Exception):
    def __init__(self, user_id: str, remaining: int):
        message = f"User {user_id} has not enough balance ({remaining} left)"
        super().__init__(message)
        main_logger.warning(self.args[0])
        self.user_id = user_id
        self.remaining = remaining


class PocketBaseService:
    def __init__(self):
        pocketbase_url = getenv("POCKETBASE_URL")
        if pocketbase_url is None:
            raise KeyError("POCKETBASE_URL not set.")
        self.pb = PocketBase(pocketbase_url)
        self.user_id = ""
        self.zdic_cache = self.pb.collection("zdicCache")
        self.corpus = self.pb.collection("corpus")
        self.corpus_stats = self.pb.collection("corpusStats")
        self.users = self.pb.collection("users")
        self.roles = self.pb.collection("roles")
        self.balance_details = self.pb.collection("balanceDetails")
        self.superusers = self.pb.collection("_superusers")

    @classmethod
    def sanitize(cls, word: str):
        FORBIDDEN_CHARACTERS = {"'", '"'}
        return "".join(c for c in word if c not in FORBIDDEN_CHARACTERS)

    @classmethod
    def get_current_time(cls) -> str:
        now = datetime.now(timezone.utc)
        return now.isoformat(timespec="milliseconds").replace("+00:00", "Z")

    ## Init ##

    async def init_corpus(self):
        if not await self.corpus_is_empty():
            main_logger.info("Corpus already initialized.")
            return

        main_logger.info("Initializing Corpus...")
        with open(Config.FREQUENCY_PATH, "r", encoding="utf-8") as f:
            for line in tqdm(f, "Initializing Corpus"):
                freq_info = FreqInfo.model_validate_json(line)
                await self.corpus_init_load(freq_info)

    async def init_roles(self):
        for role in Config.ROLES:
            if await self.roles_retrieve(role.id) is None:
                await self.roles_create(role)

    ## Auth ##

    async def auth_superuser(self) -> bool:
        email = getenv("POCKETBASE_EMAIL")
        password = getenv("POCKETBASE_PASSWORD")
        assert email is not None and password is not None

        try:
            await self.superusers.auth.with_password(email, password)
            return True
        except Exception as e:
            main_logger.error(f"Auth (superuser) failed: {e}")
            return False

    async def auth_login(self, email: str, password: str) -> AuthResult | None:
        try:
            auth_result = await self.users.auth.with_password(email, password)
            self.user_id = auth_result.get("record").get("id") or ""
            await self.users_update_active()
            return auth_result
        except Exception as e:
            main_logger.error(f"Auth (login) failed: {e}")
            return None

    async def auth_register(
        self, email: str, password: str, role: Role
    ) -> AuthResult | None:
        try:
            await self.users.create(
                params={
                    "email": email,
                    "password": password,
                    "passwordConfirm": password,
                    "name": email,
                    "total_spent": 0,
                    "balance": role.daily_coins,
                    "role": role.id,
                    "lastActive": self.get_current_time(),
                }
            )
            main_logger.info(f"Auth (register) success: {email}")
            return await self.auth_login(email, password)

        except Exception as e:
            main_logger.error(f"Auth (register) failed: {e}")
            return None

    async def auth_user(self, token: str) -> AuthResult | None:
        try:
            auth_result = await self.users.auth.refresh(
                {"headers": {"Authorization": f"Bearer {token}"}}
            )
            self.user_id = auth_result.get("record").get("id") or ""
            await self.users_update_active()
            return auth_result
        except Exception as e:
            main_logger.error(f"Auth (user) failed: {e}")
            return None

    async def auth_guest(self, ip: str):
        cleaned_ip = ip.replace(".", "__").replace(":", "_")
        fake_email = f"guest_{cleaned_ip}@none.com"
        fake_pwd = f"guest.{cleaned_ip}"
        try:
            try:
                auth_result = await self.auth_login(fake_email, fake_pwd)
            except PocketBaseNotFoundError:
                auth_result = await self.auth_register(
                    fake_email, fake_pwd, Roles.GUEST
                )

            if auth_result is not None:
                self.user_id = auth_result.get("record").get("id") or ""
            await self.users_update_active()
            return auth_result

        except Exception as e:
            main_logger.error(f"Auth (guest) failed: {e}")
            return None

    ## Users ##

    async def users_spend_coins(self, coins: int, reason: str) -> Record:
        """
        If it's an income, coins should be negative.

        A user spends coins and returns the new user info.
        """

        user = await self.users.get_one(self.user_id)
        balance: int | None = user.get("balance")
        total_spent: int | None = user.get("total_spent")
        assert balance is not None
        assert total_spent is not None
        remaining = balance - coins

        await self.users.update(
            self.user_id,
            {
                "balance": remaining,
                "total_spent": total_spent + max(coins, 0),
            },
        )

        result = await self.balance_details_create(
            delta=-coins,
            remaining=remaining,
            reason=reason,
        )

        if coins > 0 and balance < 0:
            raise NotEnoughBalanceError(user_id=self.user_id, remaining=remaining)

        return result

    async def users_guest_upgrade(self, email: str, password: str) -> Record:
        """Upgrade from guest to user"""
        return await self.users.update(
            self.user_id,
            {
                "email": email,
                "password": password,
                "passwordConfirm": password,
                "role": Roles.USER.id,
            },
        )

    async def users_update_active(self):
        """Update user's last active time"""
        user = UserRaw.model_validate(await self.users.get_one(self.user_id))
        last_active_raw = user.lastActive
        assert isinstance(last_active_raw, str)
        last_active_date = datetime.fromisoformat(
            last_active_raw.replace("Z", "+00:00")
        ).date()
        current = self.get_current_time()
        current_date = datetime.fromisoformat(current.replace("Z", "+00:00")).date()

        if last_active_date != current_date:
            role = await self.roles_get(user.role)
            await self.users_spend_coins(
                coins=-role.daily_coins, reason="Daily bonus" # TODO role
            )

        await self.users.update(self.user_id, {"lastActive": current})

    ## Zdic Cache ##

    async def zdc_create(self, query: str, content: str):
        size_kb = len(bytes(content, encoding="utf-8")) / 1024
        main_logger.info(f"Creating Zdic Cache ({query}, {size_kb:.2f} KB)")
        return await self.zdic_cache.create(
            params={
                "query": query,
                "content": content,
            }
        )

    async def zdc_search(self, query: str):
        try:
            cache = await self.zdic_cache.get_first(
                options={"filter": f"query='{self.sanitize(query)}'"}
            )
            main_logger.info(f"ZDic Cache Retrieved ({query})")
            return cache
        except PocketBaseNotFoundError:
            return None

    ## Roles ##

    async def roles_create(self, role: Role):
        main_logger.info(f"Creating role ({role.name})")
        return await self.roles.create(
            params={
                "id": role.id,
                "name": role.name,
                "daily_coins": role.daily_coins,
            }
        )

    async def roles_get(self, id: str) -> Role:
        return Role.model_validate(await self.roles.get_one(id))

    async def roles_retrieve(self, id: str) -> Role | None:
        try:
            role = await self.roles.get_one(id)
            return Role.model_validate(dict(role))
        except PocketBaseNotFoundError:
            return None

    ## Corpus & Corpus Stats ##

    async def corpus_delete_all(self):
        corpus_list = await self.corpus_list_all()
        corpus_stats_list = await self.corpus_stats_list_all()

        for c in tqdm(corpus_list, desc="Creating Corpus Deletion Tasks"):
            c_id = c.get("id")
            assert c_id is not None
            await self.corpus.delete(c_id)

        for c in tqdm(corpus_stats_list, desc="Creating Corpus Stats Deletion Tasks"):
            c_id = c.get("id")
            assert c_id is not None
            await self.corpus_stats.delete(c_id)

        main_logger.info("Corpus Deletion Completed.")

    async def corpus_init_load(self, freq_info: FreqInfo):
        tasks: list[Coroutine[Any, Any, Any]] = []

        tasks.append(
            self.corpus_stats.create(freq_info.to_corpus_stat_item().model_dump())
        )

        for note in freq_info.to_corpus_items():
            tasks.append(self.corpus.create(note.model_dump()))

        result = await gather(*tasks, return_exceptions=True)
        for r in result:
            if isinstance(r, Exception):
                main_logger.error(f"Corpus Init Load Failed in {freq_info.word}: {r}")
                return False

    async def corpus_freq_retrieve(self, query: str) -> FreqInfo | None:
        try:
            corpus_stats_item = await self.corpus_stats.get_first(
                options={"filter": f"query='{self.sanitize(query)}'"}
            )
            corpus_items = await self.corpus.get_list(
                page=1,
                per_page=30,
                options={"filter": f"query='{self.sanitize(query)}'"},
            )
            await self.users_spend_coins(
                20 + len(corpus_items["items"]) * 5, reason="Freq Retrieve"
            )
            return FreqInfo.from_corpus(
                corpus_stat_item=CorpusStatItem.model_validate(dict(corpus_stats_item)),
                corpus_items=[
                    CorpusItem.model_validate(dict(item))
                    for item in corpus_items["items"]
                ],
            )
        except PocketBaseNotFoundError:
            return None

    async def corpus_stats_list_all(self):
        return await self.corpus_stats.get_full_list()

    async def corpus_list_all(self):
        return await self.corpus.get_full_list()

    async def corpus_create_query(self, query: str, context: str, answer: str):
        try:
            stats = await self.corpus_stats.get_first({
                "filter": f"query = '{self.sanitize(query)}'",
            })
        except PocketBaseNotFoundError:
            stats = await self.corpus_stats.create(
                CorpusStatItem(
                    query=query,
                    freqTextbook=0,
                    freqDataset=0,
                    freqQuery=0,
                ).model_dump()
            )

        assert "id" in stats

        await self.corpus_stats.update(stats["id"], params={
            "freqQuery": stats.get("freqQuery", 0) + 1,
        })

        return await self.corpus.create(
            CorpusItem(
                query=query,
                queryUser=self.user_id,
                type="query",
                context=context,
                answer=answer,
            ).model_dump()
        )

    async def corpus_is_empty(self) -> bool:
        try:
            await self.corpus.get_first()
            return False
        except PocketBaseNotFoundError:
            return True

    ## Balance Details ##

    async def balance_details_list(self, page: int):
        return await self.balance_details.get_list(
            page=page, per_page=20, options={"sort": "-created"}
        )

    async def balance_details_create(self, delta: int, remaining: int, reason: str):
        return await self.balance_details.create(
            params={"delta": delta, "remaining": remaining, "reason": reason}
        )
