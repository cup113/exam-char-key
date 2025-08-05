from dataclasses import dataclass
from dataclasses_json import dataclass_json
from warnings import warn
from re import match, DOTALL
from typing import TypedDict, Literal, Any
from train.utils import SYSTEM_PROMPTS
from openai import AsyncOpenAI
from os import path, mkdir
from hashlib import sha256
from json import load, JSONDecodeError, dump
from datetime import datetime


NOTE_PAIR = ({"〔", "﹝"}, "〕")
PUNCTUATIONS = set("，。；？！")
NONSTOP_PUNCTUATIONS = set("，；")
CONTEXT_CLAUSES = (3, 2)


class EvaluationData(TypedDict):
    type: str
    context: str
    query: str
    answer: str


@dataclass
class ScoredAnswer:
    answer: str
    scores: dict[str, float]

    def get_average_score(self) -> float:
        return sum(self.scores.values()) / max(len(self.scores), 1)


@dataclass
class EvaluationResult:
    base: EvaluationData
    results: dict[str, ScoredAnswer]

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.base["type"],
            "context": self.base["context"],
            "query": self.base["query"],
            "answer": self.base["answer"],
            **{
                f"{subject}-avg": scored_answer.get_average_score()
                for subject, scored_answer in self.results.items()
            },
            **{
                f"{subject}-ans": scored_answer.answer
                for subject, scored_answer in self.results.items()
            },
        }


class CacheHandler:
    def __init__(self, cache_dir: str):
        self.cache_dir = cache_dir
        if not path.exists(cache_dir):
            mkdir(cache_dir)

    def get_cache_info(self, hash_key: str) -> tuple[str, str, str]:
        full_hash = sha256(hash_key.encode()).hexdigest()
        first_char = full_hash[0]
        second_third_chars = full_hash[1:3]
        return full_hash, first_char, second_third_chars

    def query_cache(self, hash_key: str) -> str | None:
        full_hash, first_char, second_third_chars = self.get_cache_info(hash_key)

        dir_path = path.join(self.cache_dir, first_char)
        if not path.exists(dir_path):
            return None

        json_path = path.join(dir_path, f"{second_third_chars}.json")
        if not path.exists(json_path):
            return None

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                cache_data = load(f)

            if full_hash in cache_data:
                return cache_data[full_hash]["content"]
            return None
        except (JSONDecodeError, KeyError):
            return None

    def save_cache(self, hash_key: str, content: str) -> None:
        full_hash, first_char, second_third_chars = self.get_cache_info(hash_key)

        dir_path = path.join(self.cache_dir, first_char)
        if not path.exists(dir_path):
            mkdir(dir_path)

        json_path = path.join(dir_path, f"{second_third_chars}.json")

        cache_data = {}
        if path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    cache_data = load(f)
            except JSONDecodeError:
                cache_data = {}

        cache_data[full_hash] = {
            "content": content,
            "created": datetime.now().isoformat(),
        }

        with open(json_path, "w", encoding="utf-8") as f:
            dump(cache_data, f, ensure_ascii=False)


@dataclass
class CompletionSourcePack:
    context: str
    query: str
    zdic_prompt: str
    client: AsyncOpenAI
    cache_handler: CacheHandler


class AiSubject:
    model_code: str
    model_name: str

    def __init__(self):
        pass

    async def get_flash_completion(self, pack: CompletionSourcePack) -> str:
        supplement_prompt = (
            "不要输出除答案外的无关文字。" if "ft" not in self.model_code else ""
        )
        system_prompt = (
            SYSTEM_PROMPTS.FLASH
            if "ft" not in self.model_code
            else SYSTEM_PROMPTS.FLASH_SIMPLIFIED
        )
        content = await self.get_ali_completion(
            system_prompt=system_prompt,
            user_prompt=f"请解释古文“{pack.context}”中，“{pack.query}”的含义。请迅速回答。{supplement_prompt}",
            client=pack.client,
            cache_handler=pack.cache_handler,
        )
        return content

    async def get_online_completion(self, pack: CompletionSourcePack) -> str:
        system_prompt = (
            SYSTEM_PROMPTS.THINKING
            if "ft" not in self.model_code
            else SYSTEM_PROMPTS.THINKING_SIMPLIFIED
        )
        content = await self.get_ali_completion(
            system_prompt=system_prompt,
            user_prompt=f"请解释古文“{pack.context}”中，“{pack.query}”的含义。请按要求仔细思考后回答。\n{pack.zdic_prompt}",
            client=pack.client,
            cache_handler=pack.cache_handler,
        )
        match_content = match(r"(.*?)\*\*答案\*\*[:：]\s*(.*)", content.strip(), DOTALL)
        if not match_content:
            warn(f"Model illegal response: {content}")
            return ""
        return match_content.group(2).strip()

    async def get_ali_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        client: AsyncOpenAI,
        cache_handler: CacheHandler,
    ) -> str:
        cache_key = f"{system_prompt}||{user_prompt}||{self.model_code}"
        cache = cache_handler.query_cache(cache_key)
        if cache is not None:
            return cache

        completion = await client.chat.completions.create(
            model=self.model_code,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            extra_body={"enable_thinking": False},
            temperature=0.2,
            top_p=0.95,
        )
        content = (completion.choices[0].message.content or "").strip()
        if completion.choices[0].finish_reason == "stop":
            cache_handler.save_cache(cache_key, content)
        return content

    async def ask(self, pack: CompletionSourcePack) -> str:
        raise NotImplementedError

    @classmethod
    def answer_to_hex(cls, answer: str) -> str:
        return sha256(answer.replace("；", "，").encode("utf-8")).hexdigest()[:16]


class AiEvaluator:
    model_code: str
    model_name: str

    def __init__(self):
        pass

    def get_request(
        self,
        data: EvaluationData,
        subject_answer: str,
        cache_handler: CacheHandler,
        id_prefix: str,
    ) -> "BatchRequest | None":
        answer = data["answer"]
        context = data["context"]
        query = data["query"]
        user_prompt = f"“{context}”中的“{query}”，标准答案为：{answer}\n学生答案为：{subject_answer}\n请按要求评分并按格式输出。"
        system_prompt = SYSTEM_PROMPTS.EVALUATION

        cache_key = f"EV&&{system_prompt}&&{user_prompt}&&{self.model_name}"
        cache_result = cache_handler.query_cache(cache_key)
        if cache_result:
            return None

        return {
            "url": "/v1/chat/completions",
            "method": "POST",
            "custom_id": f"{id_prefix}-ev-{self.model_name}",
            "body": {
                "model": self.model_code,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.2,
                "top_p": 0.95,
            },
        }


@dataclass_json
@dataclass
class Note:
    name_passage: str
    context: str
    index_range: tuple[int, int]
    detail: str
    core_detail: str

    def get_original_text(self):
        return self.context[self.index_range[0] : self.index_range[1]]

    def extract_sub_notes(self) -> "list[Note]":
        """
        Extract sub notes and in the meantime renew `core_detail`.

        Example:
            [秧根未牢莳未匝] 意思是，这块田里还没有栽插完毕。莳，移栽、种植。匝，布满、遍及。 -> [[莳] 移栽、种植, [匝] 布满、遍及]
        """
        self.name_passage = self.name_passage.replace(" ", "")
        sub_notes: "list[Note]" = []
        if self.detail == "":
            return []
        if self.detail[-1] in NONSTOP_PUNCTUATIONS:
            self.detail = self.detail[:-1]
            self.core_detail = self.core_detail[:-1]
        if self.detail[-1] not in PUNCTUATIONS:
            self.detail += "。"
            self.core_detail += "。"
        punctuation_index_list = [
            i for i, c in enumerate(self.detail) if c in PUNCTUATIONS
        ]
        comma_index_list = [i for i in punctuation_index_list if self.detail[i] == "，"]
        sub_end_index_list = [
            i for i in punctuation_index_list if i not in comma_index_list
        ]
        punctuation_index_list.append(-1)
        for i in reversed(comma_index_list):
            # to delete core detail parts from tail to head
            last_punctuation_index = max(
                filter(lambda x: x < i, punctuation_index_list)
            )
            sub_end_index = min(filter(lambda x: x > i, sub_end_index_list))
            start_index = last_punctuation_index + 1
            sub_string = self.detail[start_index:i]
            if sub_string in self.get_original_text():
                original_index = (
                    self.get_original_text().index(sub_string) + self.index_range[0]
                )
                sub_note_detail = self.detail[(i + 1) : (sub_end_index + 1)]
                sub_note = Note(
                    self.name_passage,
                    self.context,
                    (original_index, original_index + len(sub_string)),
                    sub_note_detail,
                    sub_note_detail,
                )
                if len(sub_note.get_original_text()) == 0:
                    warn(
                        f"Empty sub note in {self.name_passage}: {self.get_original_text()}"
                    )
                    continue
                sub_notes.append(sub_note)
                self.core_detail = (
                    self.core_detail[:start_index]
                    + self.core_detail[(sub_end_index + 1) :]
                )

        return sub_notes

    def is_short_note(self) -> bool:
        SHORT_NOTE_THRESHOLD = 3
        original_text = self.get_original_text()
        return len(original_text) <= SHORT_NOTE_THRESHOLD and len(original_text) > 0

    def is_title_note(self) -> bool:
        return self.get_original_text() == self.name_passage

    def to_dict(self) -> dict[str, str | list[int]]: ...

    @staticmethod
    def from_dict(d: dict[str, str | list[int]]) -> "Note": ...


@dataclass_json
@dataclass
class Passage:
    title: str
    author: str
    content: str
    notes: list[tuple[int, str]]
    text_end: bool

    def __str__(self):
        result = f"标 题: {self.title}\n作 者: {self.author}\n原 文: {self.content}\n"
        if self.notes:
            result += "注 释:\n"
            result += "".join(f"{index}\t{content}\n" for index, content in self.notes)
        return result

    def extract_primary_notes(self) -> list[Note]:
        """
        textbook format
        例如：
        （正文）有一言@1可以终身行之者乎
        （注释）@1〔一言〕一个字
        """

        notes: list[Note] = []

        for note in self.notes:
            end_index, note_text = note
            if not note_text:
                warn(f"Empty note in {self.title}:{end_index}")
                continue
            if note_text[0] in NOTE_PAIR[0]:
                index_right_sep = note_text.index(NOTE_PAIR[1])
                original_text = note_text[1:index_right_sep]
                detail = note_text[index_right_sep + 1 :]

                start_index = end_index
                note_chars = list(original_text)
                while start_index > 0 and note_chars:
                    start_index -= 1
                    if self.content[start_index] in note_chars:
                        note_chars.remove(self.content[start_index])
                    else:
                        start_index += 1
                        break

                index_range_original = (start_index, end_index)
                context, index_range = Passage.get_context(
                    self.content, index_range_original
                )
            elif end_index == 0:
                # Note right after title
                context = self.title
                detail = note_text
                index_range = (0, len(self.title))
            else:
                continue
            if not detail or index_range[0] == index_range[1]:
                warn(f"Empty note in {self.title}:{end_index}")
                continue
            note = Note(
                name_passage=self.title,
                context=context,
                index_range=index_range,
                detail=detail,
                core_detail=detail,
            )
            sub_notes = note.extract_sub_notes()
            notes.append(note)
            notes.extend(sub_notes)

        return notes

    @staticmethod
    def get_context(
        content: str, index_range: tuple[int, int]
    ) -> tuple[str, tuple[int, int]]:
        original_left, original_right = index_range
        if original_left < 0:
            original_left = 0
        punctuations_left, punctuations_right = CONTEXT_CLAUSES

        left, right = original_left, original_right

        while left > 0 and punctuations_left > 0:
            left -= 1
            if content[left] == "\n":
                left += 1
                break
            if content[left] in PUNCTUATIONS:
                punctuations_left -= 1 if content[left] in NONSTOP_PUNCTUATIONS else 2
        while content[left] in PUNCTUATIONS:
            left += 1

        while (
            right < len(content) and content[right] != "\n" and punctuations_right > 0
        ):
            right += 1
            if content[right - 1] in PUNCTUATIONS:
                punctuations_right -= (
                    1 if content[right - 1] in NONSTOP_PUNCTUATIONS else 2
                )
        while content[right - 1] in NONSTOP_PUNCTUATIONS:
            right -= 1
        return (content[left:right], (original_left - left, original_right - left))

    @classmethod
    def with_title(cls, title: str):
        return cls(title, "", "", [], False)

    @staticmethod
    def add_note_text(info: "tuple[Passage, int, int]", text: str):
        passage, note_index, _ = info
        pos, original_text = passage.notes[note_index]
        passage.notes[note_index] = (pos, original_text + text)

    @staticmethod
    def note_str_to_number(text: str) -> int:
        """
        a -> 1, b -> 2 ...
        @1 -> 21, @2 -> 22, ...
        #0 -> 30, #1 -> 31, ...
        """
        text = "".join(
            filter(lambda x: x in "abcdefghijklmnopqrstuvwxyz@#0123456789", text)
        )
        if text.startswith("@"):
            return int(text[1:]) + 20
        elif text.startswith("#"):
            return int(text[1:]) + 30
        else:
            return ord(text[0]) - ord("a") + 1

    def to_dict(self) -> dict[str, str | list[tuple[int, str]]]: ...

    @staticmethod
    def from_dict(d: dict[str, str | list[tuple[int, str]]]) -> "Passage": ...


class BatchRequestMessage(TypedDict):
    role: Literal["user", "system", "assistant"]
    content: str


class BatchRequestBody(TypedDict):
    model: str
    messages: list[BatchRequestMessage]
    temperature: float
    top_p: float


class BatchRequest(TypedDict):
    custom_id: str
    method: Literal["POST"]
    url: Literal["/v1/chat/completions"]
    body: BatchRequestBody


class PromptRaw(TypedDict):
    messages: list[BatchRequestMessage]
    note: dict[str, str | list[int]]


class CompletionChoice(TypedDict):
    finish_reason: str
    index: int
    message: "CompletionMessage"


class CompletionMessage(TypedDict):
    role: str
    content: str


class CompletionUsage(TypedDict):
    completion_tokens: int
    prompt_tokens: int
    total_tokens: int


class CompletionResponseBody(TypedDict):
    created: int
    usage: CompletionUsage
    model: str
    id: str
    choices: list[CompletionChoice]


class CompletionResponse(TypedDict):
    status_code: int
    request_id: str
    body: CompletionResponseBody


class CompletionApiResponse(TypedDict):
    id: str
    custom_id: str
    response: CompletionResponse
    error: str | None
