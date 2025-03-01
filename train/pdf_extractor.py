from dataclasses import dataclass
from dataclasses_json import dataclass_json
from enum import Enum
from tqdm import tqdm
from fitz import open as fitz_open  # type: ignore
from fitz import Page  # type: ignore
from re import search
from os import getenv
from openai import OpenAI
from json import loads, dumps
from warnings import warn
from fitz_types import Span, Block
from datetime import datetime


NOTE_LINES = [(60, 204), (67, 211)]
PAGE_INFO_Y = 798
TEXT_BLOCK_TYPE = 0
NOTE_PAIR = ({"〔", "﹝"}, "〕")
PUNCTUATIONS = set("，。；？！")
CONTEXT_CLAUSES = (2, 2)

client = OpenAI(
    api_key=getenv("API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)


def chat_with_model(system_prompt: str, message: str):
    completion = client.chat.completions.create(
        model="qwen2.5-14b-instruct",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message},
        ],
    )
    return loads(completion.model_dump_json())["choices"][0]["message"]["content"]


class FeatureType(Enum):
    TEXT = 0
    NUMBER = 1
    NOTE_IN_TEXT = 2
    NOTE_KEY = 3
    NOTE_DETAIL = 4
    TITLE = 5
    SEQ_NUMBER = 6
    PIN_YIN = 7
    LEARN_HINT = 8
    CHANT_TITLE = 9


@dataclass
class Feature:
    name: FeatureType
    font_in: list[str] | None = None
    size_within: tuple[float, float] | None = None
    color: str | None = None

    def check(self, font: str, size: float, color: int) -> bool:
        if self.color is not None:
            if self.color != hex(color)[len("0x") :]:
                return False
        if self.font_in is not None:
            if font not in self.font_in:
                return False
        if self.size_within is not None:
            if size < self.size_within[0] or size > self.size_within[1]:
                return False
        return True


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

    def judge_ancient(self) -> tuple[float, str]:
        system_prompt = "你是一个文言文判断专家，用户的好帮手，你需要根据文章内容判断它是否是文言文。\n主要依据为其中语言是否可能包含一些文言词汇，因此近代诗文可能也包含在内。你应当在回答的结尾输出形如<p=0.5>的结果，其中数字表示偏向文言文的程度，经典文言文为1.0，经典现代文为0.0，你可以打得绝对一些。"
        prompt = f"以下为文本：\n标题：{self.title}\n作者：{self.author}\n内容节选：{self.content[:100]}\n\n请根据上述内容，判断它是否是文言文。"
        answer = chat_with_model(system_prompt, prompt)
        # 提取<p=0.5>内容
        match_result = search(r"<p=(\d*\.\d*)>", answer)
        if match_result is None:
            warn(f"No <p=[number]> found in {repr(answer)}")
            return (float("nan"), answer)
        else:
            return (float(match_result.group(1)), answer)

    def get_context(self, index_range: tuple[int, int]) -> tuple[str, tuple[int, int]]:
        original_left, original_right = index_range
        if original_left < 0:
            original_left = 0 # TODO: pinyin
        punctuations_left, punctuations_right = CONTEXT_CLAUSES

        left, right = original_left, original_right

        while left > 0 and punctuations_left > 0:
            left -= 1
            if self.content[left] in PUNCTUATIONS:
                punctuations_left -= 1
        if self.content[left] in PUNCTUATIONS:
            left += 1

        while right < len(self.content) and punctuations_right > 0:
            right += 1
            if self.content[right - 1] in PUNCTUATIONS:
                punctuations_right -= 1
        return (self.content[left : right], (original_left - left, original_right - left))

    def extract_primary_notes(self) -> list[Note]:
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
                context, index_range = self.get_context(index_range_original)
            elif end_index == 0:
                # Note right after title
                context = self.title
                detail = note_text
                index_range = (0, len(self.title))
            else:
                continue
            note = Note(
                name_passage=self.title,
                context=context,
                index_range=index_range,
                detail=detail,
                core_detail=detail,
            )
            notes.append(note)

        return notes

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


class PageHelper:
    @classmethod
    def get_block_key_func(
        cls, sep_line_y: float | None, page_size: tuple[float, float]
    ):
        def get_block_key(block: Block) -> float:
            x, y = block["bbox"][0], block["bbox"][1]
            if sep_line_y is None or y < sep_line_y:
                basic = y - x * 0.02
            else:
                # comments, 2-column notes
                is_left = x < page_size[0] / 2
                basic = (y if is_left else (y + (page_size[1] - sep_line_y))) - x * 0.02
            if block["type"] == TEXT_BLOCK_TYPE:
                for lines in block["lines"]:
                    for span in lines["spans"]:
                        for feature in FEATURES:
                            if feature.name == FeatureType.TITLE and feature.check(
                                span["font"], span["size"], span["color"]
                            ):
                                return basic - 25
            return basic

        return get_block_key

    @classmethod
    def get_blocks(cls, page: Page) -> list[Block]:
        blocks: list[Block] = page.get_textpage().extractDICT()["blocks"]  # type: ignore
        return blocks  # type: ignore

    @classmethod
    def get_size(cls, page: Page) -> tuple[float, float]:
        d = page.get_textpage().extractDICT()  # type: ignore
        return [d["width"], d["height"]]  # type: ignore

    @classmethod
    def get_spans(cls, page: Page) -> list[Span]:
        spans: list[Span] = []
        sep_line = cls.get_note_sep_line(page)
        if len(sep_line) > 1:
            warn(f"More than one note line found in {repr(page)}")
        blocks = cls.get_blocks(page)
        key = cls.get_block_key_func(
            sep_line[0] if sep_line else None, cls.get_size(page)
        )
        blocks.sort(key=key)
        for block in blocks:
            if block["type"] == TEXT_BLOCK_TYPE:
                for line in block["lines"]:
                    for span in line["spans"]:
                        spans.append(span)

        return spans

    @classmethod
    def get_note_sep_line(cls, page: Page):
        drawings = page.get_drawings(True)  # type: ignore
        result: list[float] = []
        for drawing in filter(lambda d: "items" in d, drawings):  # type: ignore
            item = drawing["items"][0]  # type: ignore
            if item[0] == "l":
                if almost_same(item[1].y, item[2].y):  # type: ignore
                    for start_x, end_x in NOTE_LINES:
                        x_passed = almost_same(item[1].x, start_x) and almost_same(  # type: ignore
                            item[2].x, end_x  # type: ignore
                        )
                        if x_passed:
                            result.append(item[1].y)  # type: ignore

        return result


FEATURES = [
    Feature(
        FeatureType.SEQ_NUMBER,
        font_in=["FZZHUNYSJW--GB1-0"],
        size_within=(23, 25),
        color="af6b5c",
    ),
    Feature(
        FeatureType.TITLE,
        font_in=["FZZHUNYSK--GBK1-0"],
        size_within=(20, 22),
        color="af6b5c",
    ),
    Feature(
        FeatureType.CHANT_TITLE,
        font_in=["FZZHUNYSK--GBK1-0"],
        size_within=(17, 19),
        color="231f20",
    ),
    Feature(
        FeatureType.TEXT,
        font_in=["FZSSJW--GB1-0", "FZSSK--GBK1-0", "FZKTJW--GB1-0", "FZFSJW--GB1-0"],
        size_within=(11, 13),
        color="231f20",
    ),
    Feature(
        FeatureType.NOTE_IN_TEXT,
        font_in=["RopeSequenceNumberST-R"],
        size_within=(6, 8),
        color="231f20",
    ),
    Feature(
        FeatureType.NOTE_KEY,
        font_in=["RopeSequenceNumberST-R"],
        size_within=(8, 10),
        color="231f20",
    ),
    Feature(
        FeatureType.NOTE_DETAIL,
        font_in=["FZSSJW--GB1-0", "FZSSK--GBK1-0"],
        size_within=(8, 10),
        color="231f20",
    ),
    Feature(FeatureType.NUMBER, font_in=["Times-Roman"]),
    Feature(
        FeatureType.PIN_YIN,
        font_in=["NEU-XT-Regular"],
        size_within=(8, 10),
        color="231f20",
    ),
    Feature(
        FeatureType.LEARN_HINT,
        font_in=["FZLTZHK--GBK1-0"],
        color="af6b5c",
        size_within=(13, 15),
    ),
]


def get_datetime_str():
    now = datetime.now()
    return now.strftime("%Y%m%d%H%M%S") + f"{now.microsecond:06d}"


def almost_same(a: float | int, b: float | int) -> bool:
    return abs(a - b) < 1


def get_raw_data(pdf_path: str):
    doc = fitz_open(pdf_path)

    file = open(f"train/result/raw_{get_datetime_str()}.txt", "w", encoding="utf-8")

    progress = tqdm(desc="RawData", total=len(doc), unit="Page")

    for page in doc:
        progress.update(1)
        file.write("\n")

        spans = PageHelper.get_spans(page)
        for span in spans:
            text = span["text"].strip()
            size = round(span["size"], 2)
            origin = (
                round(span["origin"][0], 2),
                round(span["origin"][1], 2),
            )
            font = span["font"]
            color = span["color"]
            file.write(
                "\t".join((str(size), str(origin), font, hex(color), text)) + "\n"
            )

    file.close()
    doc.close()


def draw_feature(pdf_path: str):
    doc = fitz_open(pdf_path)

    file = open(f"train/result/featured_{get_datetime_str()}.txt", "w", encoding="utf-8")

    total_pages = len(doc)
    progress = tqdm(desc="Feature", total=total_pages, unit="Page")
    passages: list[Passage] = []
    active_passage: Passage | None = None
    author_y: float | None = None

    for i in range(total_pages):
        page = doc[i]
        progress.update(1)

        active_note_key: int | None = None
        page_notes: dict[int, tuple[Passage, int, int]] = {}

        spans = PageHelper.get_spans(page)
        for span in spans:
            text = span["text"].strip()
            if not text:
                continue
            size = span["size"]
            font = span["font"]
            color = span["color"]
            origin_y = span["origin"][1]
            if origin_y > PAGE_INFO_Y:
                continue
            for feature in FEATURES:
                if not feature.check(font, size, color):
                    continue
                if (
                    feature.name == FeatureType.TITLE
                    or feature.name == FeatureType.CHANT_TITLE
                ):
                    if active_passage and not active_passage.content:
                        # Likely to be disrupted by font changes
                        active_passage.title += text
                    else:
                        active_passage = Passage.with_title(text)
                        passages.append(active_passage)
                elif feature.name == FeatureType.TEXT:
                    if active_passage and not active_passage.text_end:
                        if not active_passage.author:
                            active_passage.author = text
                            author_y = origin_y
                        elif author_y and abs(author_y - origin_y) < 5:
                            active_passage.author += text
                        else:
                            author_y = None
                            active_passage.content += text
                elif feature.name == FeatureType.NUMBER:
                    if active_passage:
                        if active_note_key:
                            Passage.add_note_text(page_notes[active_note_key], text)
                        elif not active_passage.text_end:
                            active_passage.content += text
                elif feature.name == FeatureType.NOTE_IN_TEXT:
                    if active_passage:
                        page_notes[Passage.note_str_to_number(text)] = (
                            active_passage,
                            len(active_passage.notes),
                            len(active_passage.content),
                        )
                        active_passage.notes.append((len(active_passage.content), ""))
                elif feature.name == FeatureType.NOTE_KEY:
                    active_note_key = Passage.note_str_to_number(text)
                elif feature.name == FeatureType.NOTE_DETAIL:
                    if active_note_key:
                        Passage.add_note_text(page_notes[active_note_key], text)
                elif feature.name == FeatureType.PIN_YIN:
                    if active_note_key:
                        Passage.add_note_text(page_notes[active_note_key], text)
                elif feature.name == FeatureType.SEQ_NUMBER:
                    pass
                elif feature.name == FeatureType.LEARN_HINT:
                    if active_passage:
                        active_passage.text_end = True
                break

    for passage in passages:
        file.write(str(passage) + "\n")

    file.close()
    doc.close()

    return passages


def judge_passages(passages: list[Passage]):
    with open(f"train/result/judge_{get_datetime_str()}.txt", "w", encoding="utf-8") as f:
        progress = tqdm(desc="Judge", total=len(passages), unit="Passage")
        for passage in passages:
            prob, answer = passage.judge_ancient()
            answer_nowrap = answer.replace("\r", "").replace("\n", "  ")
            f.write(f"{passage.title}\t{prob}\t{answer_nowrap}\n")
            f.flush()
            progress.update(1)
            yield (passage, prob)


def export_notes(passages: list[Passage]):
    passage_notes: list[Note] = []
    for passage in passages:
        primary_notes = passage.extract_primary_notes()
        passage_notes.extend(primary_notes)

    with open(f"train/result/textbook_{get_datetime_str()}.json", "w", encoding="utf-8") as f:
        f.write(dumps([n.to_dict() for n in passage_notes], indent=2, ensure_ascii=False))

PATHS_TEXTBOOK = [
    "train/textbooks/统编版-高中语文必修上册.pdf",
    "train/textbooks/统编版-高中语文必修下册.pdf",
    "train/textbooks/统编版-高中语文选择性必修上册.pdf",
    "train/textbooks/统编版-高中语文选择性必修中册.pdf",
    "train/textbooks/统编版-高中语文选择性必修下册.pdf",
][0:5]
RAW_DATA = False
FILTER_ANCIENT = False


if __name__ == "__main__":
    main_progress = tqdm(desc="Total", total=len(PATHS_TEXTBOOK), unit="Book")
    target_passages: list[Passage] = []
    for path_textbook in PATHS_TEXTBOOK:
        RAW_DATA_POINT = 4
        FEATURE_POINT = 6
        FILTER_ANCIENT_POINT = 88
        points = RAW_DATA_POINT * int(RAW_DATA) + FEATURE_POINT + FILTER_ANCIENT_POINT * int(FILTER_ANCIENT)
        if RAW_DATA:
            get_raw_data(path_textbook)
            main_progress.update(RAW_DATA_POINT / points)
        passages = draw_feature(path_textbook)
        main_progress.update(FEATURE_POINT / points)
        if FILTER_ANCIENT:
            for passage, prob in judge_passages(passages):
                main_progress.update(FILTER_ANCIENT_POINT / points / len(passages))
                if prob >= 0.5:  # TODO confirm between [0.3, 0.7]
                    target_passages.append(passage)
        else:
            target_passages.extend(passages)
    export_notes(target_passages)
