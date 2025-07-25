from pydantic import BaseModel, Field
from enum import Enum
from typing import Literal, Callable
from datetime import datetime


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


class CorpusStatItem(BaseModel):
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


class FreqInfo(BaseModel):
    word: str
    textbook_freq: int
    guwen_freq: int
    query_freq: int
    notes: list[Note]  # TODO too chaotic

    def get_total_freq(self) -> int:
        return self.textbook_freq * 6 + self.guwen_freq + self.query_freq * 3

    @classmethod
    def create(cls, word: str) -> "FreqInfo":
        return FreqInfo(
            word=word, textbook_freq=0, guwen_freq=0, query_freq=0, notes=[]
        )

    @classmethod
    def from_corpus(
        cls, corpus_stat_item: CorpusStatItem, corpus_items: list[CorpusItem]
    ):
        return cls(
            word=corpus_stat_item.query,
            textbook_freq=corpus_stat_item.freqTextbook,
            guwen_freq=corpus_stat_item.freqDataset,
            query_freq=corpus_stat_item.freqQuery,
            notes=[
                Note(
                    name_passage=corpus_item.query,
                    context=corpus_item.context,
                    index_range=(
                        corpus_item.context.index(corpus_item.query),
                        corpus_item.context.index(corpus_item.query)
                        + len(corpus_item.query),
                    ),
                    detail=corpus_item.answer,
                    core_detail=corpus_item.answer,
                )
                for corpus_item in corpus_items
            ],
        )

    def to_corpus_stat_item(self):
        return CorpusStatItem(
            query=self.word,
            freqTextbook=self.textbook_freq,
            freqDataset=self.guwen_freq,
            freqQuery=self.query_freq,
        )

    def to_corpus_items(self):
        return [
            CorpusItem(
                query=note.get_original_text(),
                queryUser=None,
                type="textbook" if i < self.textbook_freq else "dataset",
                context=note.context,
                answer=note.detail,
            )
            for i, note in enumerate(self.notes)
        ]


class Role(BaseModel):
    id: str
    name: str
    daily_coins: int


class UserRaw(BaseModel):
    id: str
    email: str
    name: str
    total_spent: int
    balance: int
    role: str
    lastActive: str

    def to_user(self, roles_getter: Callable[[str], Role]) -> "User":
        return User(
            id=self.id,
            email=self.email,
            name=self.name,
            total_spent=self.total_spent,
            balance=self.balance,
            role=roles_getter(self.role),
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
