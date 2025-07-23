from dataclasses import dataclass
from dataclasses_json import dataclass_json
from warnings import warn
from re import sub
from typing import TypedDict, Literal

NOTE_PAIR = ({"〔", "﹝"}, "〕")
PUNCTUATIONS = set("，。；？！")
NONSTOP_PUNCTUATIONS = set("，；")
CONTEXT_CLAUSES = (2, 2)


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
                sub_notes.append(sub_note)
                self.core_detail = (
                    self.core_detail[:start_index]
                    + self.core_detail[(sub_end_index + 1) :]
                )

        return sub_notes

    def is_short_note(self) -> bool:
        SHORT_NOTE_THRESHOLD = 3
        return len(self.detail) <= SHORT_NOTE_THRESHOLD

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
                punctuations_left -= 1
        if content[left] in PUNCTUATIONS:
            left += 1

        while (
            right < len(content) and content[right] != "\n" and punctuations_right > 0
        ):
            right += 1
            if content[right - 1] in PUNCTUATIONS:
                punctuations_right -= 1
        if content[right - 1] in NONSTOP_PUNCTUATIONS:
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


@dataclass_json
@dataclass
class ChineseGswPassage:
    title: str
    content: str
    remark: str
    writer: str

    def extract_notes(self) -> list[Note]:
        UNICODE_NUMBERING_SET = set(
            "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳⑴⑵⑶⑷⑸⑹⑺⑻⑼⑽⑾⑿⒀⒁⒂⒃⒄⒅⒆⒇"
            "⒈⒉⒊⒋⒌⒍⒎⒏⒐⒑⒒⒓⒔⒕⒖⒗⒘⒙⒚⒛➀➁➂➃➄➅➆➇➈➉❶❷❸❹❺❻❼❽❾❿"
        )

        # 1. Data Cleaning
        self.content = self.unify_punctuation(self.content)
        self.remark = "".join(
            ch for ch in self.remark if ch not in UNICODE_NUMBERING_SET
        )  # remove numbering
        self.remark = self.unify_punctuation(self.remark)
        # remove patterns like （不足贵 一作：何足贵；不复醒 一作：不愿醒/不用醒） and pinyin in notes
        REGEX_PARENTHESES = r"（.*?）"
        REGEX_NUMBERING = r"(\d+)、|【(\d+)】|(\d+)。|(\d+)\."
        self.content = sub(REGEX_PARENTHESES, "", self.content)
        self.content = sub(REGEX_NUMBERING, "", self.content)
        self.remark = sub(REGEX_PARENTHESES, "", self.remark)
        # 2. extract notes
        # Pattern like 唐张籍《吴楚词》（说/诗/诗云）：“今朝社日停针线。” where "：" marks content in other books, which should be excluded.
        colon_index_list: list[int] = []
        for i, c in enumerate(self.remark):
            if c == "：":
                if "》" in self.remark[max(i - 3, 0) : i]:
                    continue
                if i >= 2 and self.remark[i - 2 : i] in ["古义", "今义"]:
                    continue
                colon_index_list.append(i)

        remark_list: list[tuple[int, int]] = []
        STOP_CHARACTERS = (PUNCTUATIONS - NONSTOP_PUNCTUATIONS) | {"\n"}
        for colon_index in colon_index_list:
            cur = colon_index - 1
            while cur >= 0 and self.remark[cur] not in STOP_CHARACTERS:
                cur -= 1
            remark_list.append((cur + 1, colon_index))
        remark_list.reverse()
        remark_end = len(self.remark)
        context_cursor = len(self.content)

        notes: list[Note] = []

        for remark_start, colon_index in remark_list:
            original_text = self.remark[remark_start:colon_index].strip()
            text_start = self.content.find(original_text, 0, context_cursor)
            detail = self.remark[(colon_index + 1) : remark_end].strip()

            if text_start == -1:
                if original_text in self.title:
                    index_start = self.title.find(original_text)
                    note = Note(
                        name_passage=self.title,
                        context=self.title,
                        index_range=(index_start, index_start + len(original_text)),
                        detail=detail,
                        core_detail=detail,
                    )
                    notes.append(note)
                    notes.extend(note.extract_sub_notes())
                    remark_end = remark_start
                    continue

                text_start = self.content.find(original_text)
                if text_start == -1:
                    if "句" in original_text:
                        # pattern like “但歌”二句, which cannot be found in the content
                        continue
                    warn(f"[{self.title}]“{original_text}”not found")
                    continue
                else:
                    warn(
                        f"[{self.title}]“{original_text}”not found, but found after“{text_start}”"
                    )
            index_range = (text_start, text_start + len(original_text))
            context, new_index_range = Passage.get_context(self.content, index_range)

            note = Note(
                name_passage=self.title,
                context=context,
                index_range=new_index_range,
                detail=detail,
                core_detail=detail,
            )
            notes.append(note)
            notes.extend(note.extract_sub_notes())
            remark_end = remark_start

        return notes

    @classmethod
    def unify_punctuation(cls, text: str) -> str:
        """
        Replace English punctuation with Chinese punctuation
        """

        PUNCTUATION_MAP = {
            ":": "：",
            ",": "，",
            ".": "。",
            "?": "？",
            "!": "！",
            ";": "；",
            "(": "（",
            ")": "）",
            "[": "【",
            "]": "】",
        }

        return "".join(PUNCTUATION_MAP.get(char, char) for char in text)

    @staticmethod
    def from_dict(d: dict[str, str]) -> "ChineseGswPassage": ...


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
