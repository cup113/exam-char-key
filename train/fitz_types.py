from typing import TypedDict, Literal, Union

class Span(TypedDict):
    bbox: tuple[float, float, float, float]
    origin: tuple[float, float]
    font: str
    ascender: float
    descender: float
    size: float
    flags: int
    char_flags: int
    color: int
    alpha: int
    text: str

class Line(TypedDict):
    bbox: tuple[float, float, float, float]
    wmode: Literal[0, 1]
    dir: tuple[float, float]
    spans: list[Span]

class ImageBlock(TypedDict):
    type: Literal[1]
    bbox: tuple[float, float, float, float]
    number: int
    ext: str
    width: int
    height: int
    colorspace: int
    xres: int
    yres: int
    bpc: int
    transform: tuple[float, float, float, float, float, float]
    size: int
    image: bytes
    mask: bytes

class TextBlock(TypedDict):
    type: Literal[0]
    bbox: tuple[float, float, float, float]
    number: int
    lines: list[Line]


Block = Union[ImageBlock, TextBlock]
