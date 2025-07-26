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
        base_url=AI_BASE_URL, id="qwen-plus", prompt_price=8, completion_price=2
    )

    WYW_FLASH_MODEL = AiModel(
        base_url=AI_BASE_URL,
        id="qwen3-8b-ft-202507232312-96a6",
        prompt_price=5,
        completion_price=20,
    )
    WYW_THINKING_MODEL = AiModel(
        base_url=AI_BASE_URL,
        id="qwen3-8b-ft-202507251314-0fd2",
        prompt_price=5,
        completion_price=40,  # Half reasoning
    )

    DEFAULT_BALANCE = 200_000

    ROLES = [Roles.ADMIN, Roles.CORE, Roles.USER, Roles.GUEST]

    FREQUENCY_PATH = "server/word-frequency.jsonl"

    PROMPT_FLASH = "你是一位高中语文老师，深入研究高考文言文词语解释。答案简短，并且不太过意译。一般可以给出一个精准解释，语境特殊时可以补充引申义。若涉及通假字，则需答：通“(通假字)”，(含义)。你需要简洁地回答用户的问题，除答案外不输出任何内容。"

    PROMPT_AI_THOUGHT = """<prompt>
    你是一位高中语文老师，对高考文言文词语解释与句子翻译有着深入研究。高考的词语解释答案常常在 6 字以内，不能太过意译，一般地可以给出一个精准解释，若语境确实特殊可以表示为：(原义)，这里指(引申义)。若涉及通假字，则需答：通“(通假字)”，(含义)。
    汉典是一个权威的网站，内含该字的基本义项，但不一定全面。
    你要做的事情如下：
    - 对句义进行详细而有深度的思考，敢于多次尝试并依照汉典义项（若有）代入阐释。用<think></think>标签包裹。
    - 给出用你思考结果代入的句子解释。用<explain></explain>标签包裹。
    - 输出 1~3 个可以写在高考试卷上的词语解释，用<answers></answers>包裹，每个义项之间用分号“；”分隔。
    - 输出的最外层不需要做任何修饰，每步需要换行，每步内部可以换行。
    </prompt>"""

    PROMPT_AI_SEARCH_ORIGINAL = """你是一位助手，要根据节选的内容，【搜索文言文原文】并输出。请不要输出任何其他格式类和互动类信息，仅仅给出原文内容。"""
