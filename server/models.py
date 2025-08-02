from pocketbase.models.dtos import AuthResult, ListResult, Record
from pydantic import BaseModel, Field, field_serializer
from enum import Enum
from typing import Literal, Callable, Coroutine, Any, TypeVar, Generic
from datetime import datetime

T = TypeVar("T")


class ListResultModel(BaseModel, Generic[T]):
    page: int
    per_page: int
    total_items: int
    total_pages: int
    items: list[T]

    @classmethod
    def map_list_result(
        cls, func: Callable[[Record], T], list_result: ListResult[Record]
    ) -> "ListResultModel[T]":
        return cls(
            page=list_result["page"],
            per_page=list_result["perPage"],  # type: ignore
            total_items=list_result["totalItems"],  # type: ignore
            total_pages=list_result["totalPages"],  # type: ignore
            items=[func(item) for item in list_result["items"]],
        )


class AiModel(BaseModel):
    base_url: str
    id: str
    prompt_price: int  # 1e-7 RMB/token
    completion_price: int  # 1e-7 RMB/token
    thinking: bool = Field(default=False)


class Note(BaseModel):
    name_passage: str
    context: str
    index_range: tuple[int, int]
    detail: str
    core_detail: str

    def get_original_text(self):
        return self.context[self.index_range[0] : self.index_range[1]]

    def to_corpus_item(self, type: Literal["textbook", "dataset"]):
        return CorpusItem(
            query=self.get_original_text(),
            queryUser=None,
            type=type,
            context=self.context,
            answer=self.core_detail,
        )


class CorpusStatItem(BaseModel):
    query: str
    freqTextbook: int
    freqDataset: int
    freqQuery: int

    def get_total_freq(self) -> int:
        return self.freqTextbook * 6 + self.freqDataset + self.freqQuery * 3


class CorpusStatItemRaw(BaseModel):
    id: str
    query: str
    freqTextbook: int
    freqDataset: int
    freqQuery: int


class CorpusItem(BaseModel):
    query: str
    queryUser: str | None
    type: Literal["textbook", "dataset", "query"]
    context: str
    answer: str


class CorpusItemRaw(BaseModel):
    id: str
    query: str
    queryUser: str | None
    type: Literal["textbook", "dataset", "query"]
    context: str
    answer: str


class FreqInfoFileRaw(BaseModel):
    word: str
    textbook_freq: int
    guwen_freq: int
    query_freq: int
    notes: list[Note]

    def to_freq_info(self):
        return FreqInfo(
            stat=CorpusStatItem(
                query=self.word,
                freqTextbook=self.textbook_freq,
                freqDataset=self.guwen_freq,
                freqQuery=self.query_freq,
            ),
            notes=[
                note.to_corpus_item("textbook" if i < self.textbook_freq else "dataset")
                for i, note in enumerate(self.notes)
            ],
            total_pages=1,
        )


class FreqInfo(BaseModel):
    stat: CorpusStatItem
    notes: list[CorpusItem]
    total_pages: int

    @classmethod
    def empty(cls, word: str) -> "FreqInfo":
        return FreqInfo(
            stat=CorpusStatItem(
                query=word,
                freqTextbook=0,
                freqDataset=0,
                freqQuery=0,
            ),
            notes=[],
            total_pages=1,
        )


class Role(BaseModel):
    id: str
    name: str
    daily_coins: int


RolesGetter = Callable[[str], Coroutine[Any, Any, Role]]


class UserRaw(BaseModel):
    id: str
    email: str
    name: str
    total_spent: int
    balance: int
    role: str
    lastActive: str

    async def to_user(self, roles_getter: RolesGetter) -> "User":
        return User(
            id=self.id,
            email=self.email,
            name=self.name,
            total_spent=self.total_spent,
            balance=self.balance,
            role=await roles_getter(self.role),
            last_active=datetime.fromisoformat(self.lastActive.replace("Z", "+00:00")),
        )


class User(BaseModel):
    id: str
    email: str
    name: str
    total_spent: int
    balance: int
    role: Role
    last_active: datetime

    @field_serializer("last_active")
    def serialize_last_active(self, value: datetime) -> str:
        return value.isoformat()


class AuthResultModel(BaseModel):
    token: str
    user: User

    @classmethod
    async def from_raw(cls, auth_result: AuthResult, roles_getter: RolesGetter):
        return cls(
            token=auth_result["token"],
            user=await UserRaw.model_validate(auth_result["record"]).to_user(
                roles_getter
            ),
        )


class BalanceDetail(BaseModel):
    user: str
    delta: int
    remaining: int
    reason: str


class BalanceDetailRaw(BaseModel):
    user: str
    delta: int
    remaining: int
    reason: str
    id: str
    created: str


class AiUsage(BaseModel):
    model: AiModel
    prompt_tokens: int
    completion_tokens: int

    def calc_cost(self) -> int:
        return (
            self.prompt_tokens * self.model.prompt_price
            + self.completion_tokens * self.model.completion_price
        )


class CompletionChunkResponse(BaseModel):
    stopped: bool
    content: str


class ZdicExplanations(BaseModel):
    basic: list[str]
    detailed: list[str]
    phrase: list[str]


class ZdicResult(BaseModel):
    basic_explanations: list[str]
    detailed_explanations: list[str]
    phrase_explanations: list[str]
    zdic_prompt: str
    cached: bool

    @classmethod
    def empty(cls):
        return cls(
            basic_explanations=[],
            detailed_explanations=[],
            phrase_explanations=[],
            zdic_prompt="",
            cached=False,
        )


class ServerResponseType(str, Enum):
    AiUsage = "ai-usage"
    AiFlash = "ai-flash"
    AiThinking = "ai-thinking"
    AiExtract = "ai-extract"
    SearchOriginal = "search-original"
    Zdic = "zdic"
    FreqInfo = "freq"


class ServerResponseItem(BaseModel):
    type: ServerResponseType

    def to_jsonl_str(self):
        return self.model_dump_json() + "\n"


class ServerResponseAiUsage(ServerResponseItem):
    type: ServerResponseType = Field(ServerResponseType.AiUsage)
    data: AiUsage

    @classmethod
    def create(cls, data: AiUsage):
        return cls(type=ServerResponseType.AiUsage, data=data)


class ServerResponseAi(ServerResponseItem):
    data: CompletionChunkResponse

    @classmethod
    def create(cls, type: ServerResponseType, data: CompletionChunkResponse):
        return cls(type=type, data=data)


class ServerResponseAiFlash(ServerResponseItem):
    type: ServerResponseType = Field(ServerResponseType.AiFlash)
    data: str

    @classmethod
    def create(cls, data: str):
        return cls(type=ServerResponseType.AiFlash, data=data)


class ServerResponseZdic(ServerResponseItem):
    type: ServerResponseType = Field(ServerResponseType.Zdic)
    data: ZdicResult

    @classmethod
    def create(cls, data: ZdicResult):
        return cls(type=ServerResponseType.Zdic, data=data)


class ServerResponseFreqInfo(ServerResponseItem):
    type: ServerResponseType = Field(ServerResponseType.FreqInfo)
    data: FreqInfo

    @classmethod
    def create(cls, data: FreqInfo):
        return cls(type=ServerResponseType.FreqInfo, data=data)
