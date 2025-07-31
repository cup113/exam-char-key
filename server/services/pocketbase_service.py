from pocketbase import PocketBase
from pocketbase.models.errors import PocketBaseNotFoundError, PocketBaseBadRequestError

from os import getenv
from tqdm import tqdm
from datetime import datetime, timezone
from asyncio import gather
from typing import Coroutine, Any

from asyncio import Lock, current_task

from server.services.logging_service import main_logger
from server.config import Config, Roles
from server.models import (
    Role,
    FreqInfo,
    FreqInfoFileRaw,
    CorpusStatItem,
    CorpusStatItemRaw,
    CorpusItem,
    CorpusItemRaw,
    UserRaw,
    BalanceDetail,
    BalanceDetailRaw,
    AuthResultModel,
    ListResultModel,
)


class ServerException(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        main_logger.error(message)


class NotEnoughBalanceError(ServerException):
    def __init__(self, user_id: str, remaining: int):
        message = f"User {user_id} doesn't have enough balance ({remaining} left)"
        super().__init__(message)
        self.user_id = user_id
        self.remaining = remaining


class ReentrantLock:
    def __init__(self):
        self._lock = Lock()
        self._owner = None
        self._count = 0

    async def __aenter__(self):
        _current_task = current_task()
        if self._owner == _current_task:
            self._count += 1
        else:
            await self._lock.__aenter__()
            self._owner = _current_task
            self._count = 1
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ):
        _current_task = current_task()
        if self._owner == _current_task:
            self._count -= 1
            if self._count == 0:
                self._owner = None
                await self._lock.__aexit__(exc_type, exc_val, exc_tb)
        else:
            raise RuntimeError("Cannot release un-acquired lock")


class UserLockManager:
    def __init__(self):
        self._user_locks: dict[str, ReentrantLock] = {}
        self._user_locks_lock = Lock()

    async def get_user_lock(self, user_id: str) -> ReentrantLock:
        lock = self._user_locks.get(user_id)
        if lock is not None:
            return lock

        async with self._user_locks_lock:
            if user_id not in self._user_locks:
                self._user_locks[user_id] = ReentrantLock()
            return self._user_locks[user_id]

    async def cleanup_user_lock(self, user_id: str):
        async with self._user_locks_lock:
            if user_id in self._user_locks:
                del self._user_locks[user_id]


user_lock_manager = UserLockManager()


class PocketBaseService:
    def __init__(self):
        self.pocketbase_url = getenv("POCKETBASE_URL")
        if self.pocketbase_url is None:
            raise KeyError("POCKETBASE_URL not set.")
        self.pb = PocketBase(self.pocketbase_url)
        self.latest_auth_result: AuthResultModel | None = None
        self.zdic_cache = self.pb.collection("zdicCache")
        self.corpus = self.pb.collection("corpus")
        self.corpus_stats = self.pb.collection("corpusStats")
        self.users = self.pb.collection("users")
        self.roles = self.pb.collection("roles")
        self.balance_details = self.pb.collection("balanceDetails")
        self.superusers = self.pb.collection("_superusers")

    @classmethod
    def sanitize(cls, word: str) -> str:
        FORBIDDEN_CHARACTERS = {"'", '"'}
        return "".join(c for c in word if c not in FORBIDDEN_CHARACTERS)

    @classmethod
    def get_current_time(cls) -> str:
        now = datetime.now(timezone.utc)
        return now.isoformat(timespec="milliseconds").replace("+00:00", "Z")

    def get_token(self) -> str:
        assert self.latest_auth_result is not None
        return self.latest_auth_result.token

    def get_user_id(self) -> str:
        assert self.latest_auth_result is not None
        return self.latest_auth_result.user.id

    ## Init ##

    async def init_corpus(self) -> None:
        if not await self._corpus_is_empty():
            main_logger.info("Corpus already initialized.")
            return

        main_logger.info("Initializing Corpus...")
        with open(Config.FREQUENCY_PATH, "r", encoding="utf-8") as f:
            for line in tqdm(f, "Initializing Corpus"):
                freq_info = FreqInfoFileRaw.model_validate_json(line).to_freq_info()
                await self._corpus_init_load(freq_info)

    async def init_roles(self) -> None:
        for role in Config.ROLES:
            if await self.roles_retrieve(role.id) is None:
                await self._roles_create(role)

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

    async def auth_login(self, email: str, password: str) -> AuthResultModel:
        auth_result = await AuthResultModel.from_raw(
            await self.users.auth.with_password(email, password), self.roles_get
        )
        self.latest_auth_result = auth_result

        await self.users_update_active()
        return auth_result

    async def auth_register(
        self, email: str, password: str, role: Role
    ) -> AuthResultModel | None:
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

    async def auth_user(self, token: str) -> AuthResultModel | None:
        try:
            auth_result = await AuthResultModel.from_raw(
                await self.users.auth.refresh(
                    {"headers": {"Authorization": f"Bearer {token}"}}
                ),
                self.roles_get,
            )
            self.latest_auth_result = auth_result
            await self.users_update_active()
            return auth_result
        except Exception as e:
            main_logger.error(f"Auth (user) failed: {e}")
            return None

    async def auth_guest(self, ip: str) -> AuthResultModel | None:
        cleaned_ip = ip.replace(":", "_")
        fake_email = f"{cleaned_ip}@guest.com"
        fake_pwd = f"guest.{cleaned_ip}"
        try:
            try:
                auth_result = await self.auth_login(fake_email, fake_pwd)
            except (PocketBaseNotFoundError, PocketBaseBadRequestError) as e:
                main_logger.warning(f"Auth (login) failed: {e}")
                auth_result = await self.auth_register(
                    fake_email, fake_pwd, Roles.GUEST
                )

            if auth_result is not None:
                self.latest_auth_result = auth_result
            await self.users_update_active()
            return auth_result

        except Exception as e:
            main_logger.error(f"Auth (guest) failed: {e}")
            return None

    ## Users ##

    async def users_spend_coins(self, coins: int, reason: str) -> BalanceDetailRaw:
        """
        If it's an income, coins should be negative.

        A user spends coins and returns the new user info.
        """

        user_lock = await user_lock_manager.get_user_lock(self.get_user_id())

        async with user_lock:
            user = await self.users.get_one(self.get_user_id())
            balance: int | None = user.get("balance")
            total_spent: int | None = user.get("total_spent")
            assert balance is not None
            assert total_spent is not None
            remaining = balance - coins

            await self.users.update(
                self.get_user_id(),
                {
                    "balance": remaining,
                    "total_spent": total_spent + max(coins, 0),
                },
            )

            result = await self._balance_details_create(
                BalanceDetail(
                    user=self.get_user_id(),
                    delta=-coins,
                    remaining=remaining,
                    reason=reason,
                )
            )

            return result

    async def users_guest_upgrade(self, email: str, password: str) -> AuthResultModel:
        """Upgrade from guest to user"""

        assert self.latest_auth_result is not None
        assert self.latest_auth_result.user.role.id == Roles.GUEST.id

        balance = self.latest_auth_result.user.balance
        await self.users_spend_coins(balance // 10 * 9, "升级至正式用户")
        result = await self.auth_register(email, password, Roles.USER)

        assert result is not None

        await self.users_spend_coins(-balance // 10 * 9, "继承自游客账户")

        return result

    async def users_update_active(self):
        """Update user's last active time"""
        user_lock = await user_lock_manager.get_user_lock(self.get_user_id())

        async with user_lock:
            user = UserRaw.model_validate(await self.users.get_one(self.get_user_id()))
            last_active_raw = user.lastActive
            assert isinstance(last_active_raw, str)
            last_active_date = datetime.fromisoformat(
                last_active_raw.replace("Z", "+00:00")
            ).date()
            current = self.get_current_time()
            current_date = datetime.fromisoformat(current.replace("Z", "+00:00")).date()

            await self.users.update(self.get_user_id(), {"lastActive": current})

            if last_active_date != current_date:
                role = await self.roles_get(user.role)
                await self.users_spend_coins(coins=-role.daily_coins, reason="每日登录奖励")

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

    async def _roles_create(self, role: Role) -> None:
        main_logger.info(f"Creating role ({role.name})")
        await self.roles.create(params=role.model_dump())

    async def roles_get(self, id: str) -> Role:
        return Role.model_validate(await self.roles.get_one(id))

    async def roles_retrieve(self, id: str) -> Role | None:
        try:
            role = await self.roles.get_one(id)
            return Role.model_validate(dict(role))
        except PocketBaseNotFoundError:
            return None

    ## Corpus & Corpus Stats ##

    async def _corpus_delete_all(self) -> None:
        corpus_list = await self._corpus_list_all()
        corpus_stats_list = await self._corpus_stats_list_all()

        for c in tqdm(corpus_list, desc="Creating Corpus Deletion Tasks"):
            await self.corpus.delete(c.id)

        for c in tqdm(corpus_stats_list, desc="Creating Corpus Stats Deletion Tasks"):
            await self.corpus_stats.delete(c.id)

        main_logger.info("Corpus Deletion Completed.")

    async def _corpus_init_load(self, freq_info: FreqInfo) -> bool:
        tasks: list[Coroutine[Any, Any, Any]] = []

        tasks.append(self.corpus_stats.create(freq_info.model_dump()))

        result = await gather(*tasks, return_exceptions=True)
        for r in result:
            if isinstance(r, Exception):
                main_logger.error(
                    f"Corpus Init Load Failed in {freq_info.stat.query}: {r}"
                )
                return False

        return True

    async def corpus_freq_retrieve(self, query: str, page: int) -> FreqInfo | None:
        try:
            corpus_stats_item = await self.corpus_stats.get_first(
                options={"filter": f"query='{self.sanitize(query)}'"}
            )
            corpus_items = await self.corpus.get_list(
                page=page,
                per_page=15,
                options={"filter": f"query='{self.sanitize(query)}'"},
            )
            await self.users_spend_coins(
                20 + len(corpus_items["items"]) * 5, reason=f"词频查询 {query}"
            )
            return FreqInfo(
                stat=CorpusStatItem.model_validate(dict(corpus_stats_item)),
                notes=[
                    CorpusItem.model_validate(dict(item))
                    for item in corpus_items["items"]
                ],
                total_pages=corpus_items["totalPages"],  # type: ignore
            )
        except PocketBaseNotFoundError:
            return None

    async def _corpus_stats_list_all(self) -> list[CorpusStatItemRaw]:
        return [
            CorpusStatItemRaw.model_validate(item)
            for item in await self.corpus_stats.get_full_list()
        ]

    async def _corpus_list_all(self) -> list[CorpusItemRaw]:
        return [
            CorpusItemRaw.model_validate(item)
            for item in await self.corpus.get_full_list()
        ]

    async def corpus_create_query(
        self, query: str, context: str, answer: str
    ) -> CorpusItemRaw:
        try:
            stats = await self.corpus_stats.get_first(
                {
                    "filter": f"query = '{self.sanitize(query)}'",
                }
            )
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

        await self.corpus_stats.update(
            stats["id"],
            params={
                "freqQuery": stats.get("freqQuery", 0) + 1,
            },
        )

        return CorpusItemRaw.model_validate(
            await self.corpus.create(
                CorpusItem(
                    query=query,
                    queryUser=self.get_user_id(),
                    type="query",
                    context=context,
                    answer=answer,
                ).model_dump()
            )
        )

    async def _corpus_is_empty(self) -> bool:
        try:
            await self.corpus.get_first()
            return False
        except PocketBaseNotFoundError:
            return True

    ## Balance Details ##

    async def balance_details_list(
        self, page: int
    ) -> ListResultModel[BalanceDetailRaw]:
        return ListResultModel[BalanceDetailRaw].map_list_result(
            BalanceDetailRaw.model_validate,
            await self.balance_details.get_list(
                page=page, per_page=15, options={"sort": "-created"}
            ),
        )

    async def _balance_details_create(
        self, balance_detail: BalanceDetail
    ) -> BalanceDetailRaw:
        return BalanceDetailRaw.model_validate(
            await self.balance_details.create(params=balance_detail.model_dump())
        )

    async def balance_check(self) -> None:
        balance = UserRaw.model_validate(await self.users.get_one(self.get_user_id())).balance
        if balance < 0:
            raise NotEnoughBalanceError(self.get_user_id(), balance)
