from pocketbase import PocketBase
from pocketbase.models.errors import PocketBaseNotFoundError
from os import getenv
from datetime import datetime, timezone
from server.services.logging_service import main_logger
from server.config import Config, Roles
from server.models import Role


class PocketBaseService:
    def __init__(self):
        pocketbase_url = getenv("POCKETBASE_URL")
        if pocketbase_url is None:
            raise KeyError("POCKETBASE_URL not set.")
        self.pb = PocketBase(pocketbase_url)
        self.zdic_cache = self.pb.collection("zdicCache")
        self.corpus = self.pb.collection("corpus")
        self.corpus_stats = self.pb.collection("corpusStats")
        self.users = self.pb.collection("users")
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
        _frequency_file = Config.FREQUENCY_PATH

    async def init_roles(self):
        pass

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

    async def auth_login(self, email: str, password: str) -> str | None:
        try:
            auth_result = await self.superusers.auth.with_password(email, password)
            return auth_result.get("token")
        except Exception as e:
            main_logger.error(f"Auth (login) failed: {e}")
            return None

    async def auth_register(self, email: str, password: str, role: Role):
        try:
            await self.superusers.create(
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
            return self.auth_login(email, password)

        except Exception as e:
            main_logger.error(f"Auth (register) failed: {e}")
            return None

    async def auth_user(self, token: str) -> str | None:
        try:
            auth_result = await self.users.auth.refresh({
                "headers": {"Authorization": f"Bearer {token}"}
            })
            return auth_result.get("token")
        except Exception as e:
            main_logger.error(f"Auth (user) failed: {e}")
            return None

    async def auth_guest(self, ip: str):
        cleaned_ip = ip.replace(".", "__").replace(":", "_")
        fake_email = f"guest_{cleaned_ip}@none.com"
        fake_pwd = f"guest.{cleaned_ip}"
        try:
            try:
                user = await self.users.get_first({
                    "filter": f"email='{fake_email}'"
                })
            except PocketBaseNotFoundError:
                user = await self.auth_register(fake_email, fake_pwd, Roles.GUEST)

            return user
        except Exception as e:
            main_logger.error(f"Auth (guest) failed: {e}")
            return None

    ## ZDic Cache ##

    async def zdc_insert(self, query: str, content: str):
        size_kb = len(bytes(content, encoding="utf-8")) / 1024
        main_logger.info(f"ZDic Cache created ({query}, {size_kb:.2f} KB)")
        return await self.zdic_cache.create(
            params={
                "query": query,
                "content": content,
            }
        )

    async def zdc_retrieve(self, query: str):
        try:
            cache = await self.zdic_cache.get_first(
                options={"filter": f"query='{self.sanitize(query)}'"}
            )
            main_logger.info(f"ZDic Cache Retrieved ({query})")
            return cache
        except PocketBaseNotFoundError:
            return None

    ## Roles ##

    async def get_role(self, id: str) -> Role | None:
        try:
            role = await self.superusers.get_first(
                options={"filter": f"role='{id}'"}
            )
            return Role.model_validate(dict(role))
        except PocketBaseNotFoundError:
            return None

    async def add_role(self, role: Role):
        pass

    ## Corpus ##

    ## Corpus Stats ##
