from dotenv import load_dotenv
from os import getenv
from server.models import AiModel, Role

load_dotenv(".env")


class Roles:
    ADMIN = Role(id="role00admin0000", name="Admin", daily_coins=10_000_000)
    CORE = Role(id="role00core00000", name="Core", daily_coins=5_000_000)
    USER = Role(id="role00user00000", name="User", daily_coins=1_000_000)
    GUEST = Role(id="role00guest0000", name="Guest", daily_coins=200_000)


class Config:
    API_KEY = getenv("API_KEY")
    AI_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    GENERAL_MODEL = AiModel(
        base_url=AI_BASE_URL, id="qwen-plus", prompt_price=8, completion_price=20
    )
    LONG_MODEL = AiModel(
        base_url=AI_BASE_URL, id="qwen-long-latest", prompt_price=5, completion_price=20
    )

    WYW_FLASH_MODEL = AiModel(
        base_url=AI_BASE_URL,
        id="qwen3-8b-ft-202508031744-1c46",
        prompt_price=5,
        completion_price=20,
    )
    WYW_THINKING_MODEL = AiModel(
        base_url=AI_BASE_URL,
        id="qwen3-8b-ft-202508041131-e7d8",
        prompt_price=5,
        completion_price=50,
    )

    ROLES = [Roles.ADMIN, Roles.CORE, Roles.USER, Roles.GUEST]

    FREQUENCY_PATH = "server/word-frequency.jsonl"

    PROMPT_FLASH = "你专精于简短、准确地回答高中语文文言文语境中的词语释义。从本义出发，仅特殊情况下补充引申义。不输出多余内容。"

    PROMPT_AI_THOUGHT = """你专精于简短、准确地回答高中语文文言文语境中的词语释义。从本义出发，仅特殊情况下补充引申义。你可以参考汉典的义项（若有）。输出格式时，要求以“**思考**：”“**解释**：”“**答案**：”分别开头输出三行文本。代入时要深度思考，解释时要解释句子含义及代入词语解释，答案输出 1~2 个，若 2 个则用“；”分隔。"""

    PROMPT_AI_SEARCH_ORIGINAL = """你是一位助手，要根据节选的内容，【搜索文言文原文】并输出。请不要输出任何其他格式类和互动类信息，仅仅给出原文内容。"""

    PROMPT_AI_EXTRACT_MODEL_TEST = """你是一位助教，你要帮助教师完成重复性的操作任务。请细致地完成。教师会给你一段文本、题目、标准答案，但他正在编撰一套汇编题目，专门针对文言释义这一板块的内容。高考中有三道题是考察这一方面的，一般是14（两道填空）、15（两道选择）、17（翻译句子），题号可能有所变动。格式为 Markdown，一般来说需要解释的词语会被加粗，但也有时会遗漏。这时，需要解释的词语需要你结合标准答案进行推断。此外，原文下可能会有注释，注释可以是不错的补充。其余题目如断句、选择、简答分析不必理会。

对于两道填空和两道选择，你要忠于原文和答案，从原文中补充上下文后，原样输出。
对于翻译句子的题目，你需要选择考察的重难点字词，将其提炼出后输出。选取 1~3 个即可。中档、简单的不需要提取。最好取单字，若确实为一体则取整词。
若原文下有注释，将不过于生僻的字词同样从原文补充上下文后输出。若该注释很长，适当精简使其适合作为一道考试题目的答案。

你的任务流程为：先对三个题块（和注释，若有）逐题分析，每一题块都要找到合适的上下文和需要解释的字词，然后合并所有内容输出最终答案。

特别注意：不可以只输出题目的那几个字，这些上下文是不够做题的！

你输出的结尾应该是几行 CSV 代码（使用代码块括起），格式为 type,context,query,answer，其中 type 为题目板块，可取值为 填空/选择/翻译/注释； context 需要你选取考察的词语的完整上下文，这一语境应为考生能推断出词义的最小语境。query应为考察的关键字词。answer应为期望的标准回答。"""
