from tqdm import tqdm
from fitz import open as fitz_open  # type: ignore
from fitz import Page  # type: ignore
from warnings import warn
from enum import Enum
from json import dumps, loads
from fitz_types import Span, Block
from dataclasses import dataclass

from models import Note, Passage


NOTE_LINES = [(60, 204), (67, 211)]
PAGE_INFO_Y = 798
TEXT_BLOCK_TYPE = 0


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


def almost_same(a: float | int, b: float | int) -> bool:
    return abs(a - b) < 1


def get_raw_data(pdf_path: str, is_first: bool):
    doc = fitz_open(pdf_path)

    file = open(f"train/result/raw.txt", "w" if is_first else "a", encoding="utf-8")

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


def draw_feature(pdf_path: str, is_first: bool):
    doc = fitz_open(pdf_path)

    file = open(
        f"train/result/featured.txt", "w" if is_first else "a", encoding="utf-8"
    )

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
                        active_passage.title += text.replace(" ", "")
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


def export_notes(passages: list[Passage]):
    passage_notes: list[Note] = []
    for passage in passages:
        primary_notes = passage.extract_primary_notes()
        passage_notes.extend(primary_notes)

    with open(f"train/result/textbook.jsonl", "w", encoding="utf-8") as f:
        for note in passage_notes:
            f.write(dumps(note.to_dict(), ensure_ascii=False) + "\n")


PATHS_TEXTBOOK = [
    "train/textbooks/统编版-高中语文必修上册.pdf",
    "train/textbooks/统编版-高中语文必修下册.pdf",
    "train/textbooks/统编版-高中语文选择性必修上册.pdf",
    "train/textbooks/统编版-高中语文选择性必修中册.pdf",
    "train/textbooks/统编版-高中语文选择性必修下册.pdf",
][0:5]
RAW_DATA = False


if __name__ == "__main__":
    try:
        with open(
            "./train/result/textbook-is-ancient.jsonl", "r", encoding="utf-8"
        ) as f:
            is_ancient_arr = [loads(line) for line in f]
    except:
        is_ancient_arr = []
    is_ancient_dict = {item["title"]: item["is_ancient"] for item in is_ancient_arr}

    main_progress = tqdm(desc="Total", total=len(PATHS_TEXTBOOK), unit="Book")
    target_passages: list[Passage] = []
    for i, path_textbook in enumerate(PATHS_TEXTBOOK):
        RAW_DATA_POINT = 4
        FEATURE_POINT = 6
        points = RAW_DATA_POINT * int(RAW_DATA) + FEATURE_POINT
        if RAW_DATA:
            get_raw_data(path_textbook, is_first=(i == 0))
            main_progress.update(RAW_DATA_POINT / points)
        passages = draw_feature(path_textbook, is_first=(i == 0))
        main_progress.update(FEATURE_POINT / points)
        default_is_target = len(is_ancient_dict) == 0
        for passage in passages:
            if is_ancient_dict.get(passage.title, default_is_target):
                target_passages.append(passage)
    export_notes(target_passages)
    with open("train/result/textbook-notes.jsonl", "w", encoding="utf-8") as f:
        for passage in target_passages:
            for note in passage.extract_primary_notes():
                f.write(dumps(note.to_dict(), ensure_ascii=False) + "\n")
    with open("train/result/textbook-passages.jsonl", "w", encoding="utf-8") as f:
        for passage in target_passages:
            f.write(dumps(passage.to_dict(), ensure_ascii=False) + "\n")
