from pydantic import BaseModel, Field
from enum import Enum


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


class FreqInfo(BaseModel):
    word: str
    textbook_freq: int
    guwen_freq: int
    query_freq: int
    notes: list[Note]

    def get_total_freq(self) -> int:
        return self.textbook_freq * 6 + self.guwen_freq + self.query_freq * 3

    @classmethod
    def create(cls, word: str) -> "FreqInfo":
        return FreqInfo(
            word=word, textbook_freq=0, guwen_freq=0, query_freq=0, notes=[]
        )


class Role(BaseModel):
    id: str
    name: str
    daily_coins: int


class AiUsage(BaseModel):
    model: AiModel
    prompt_tokens: int
    completion_tokens: int


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
