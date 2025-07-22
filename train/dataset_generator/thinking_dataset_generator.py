from re import match
from train.utils import JsonlReader, JsonlWriter, IntermediateFiles
from train.models import CompletionApiResponse, Note
from warnings import warn
from dataclasses import dataclass


@dataclass
class ScoredResponse:
    base: CompletionApiResponse
    scores: list[int]

    def get_average(self) -> float | None:
        if len(self.scores) == 0:
            return None
        return sum(self.scores) / len(self.scores)


@dataclass
class ScoredNote:
    base: Note
    responses: list[ScoredResponse]


def parse_score(message: str) -> int | None:
    """
    Parse the score from the message.
    <think>...</think><score>9</score>
    """

    score_match = match(r"(.*?)<score>([0-9]|10)</score>", message)

    if score_match:
        return int(score_match.group(2))
    else:
        return None


def check_integrity(message: str) -> bool:
    """
    Check the integrity of the response of the distilled model.
    """

    pattern = r"<think>(.*?)</think>(.*?)<explain>(.*?)</explain>(.*?)<answers>(.*?)</answers>"
    return bool(match(pattern, message.strip()))


data: dict[str, ScoredNote] = {}


with JsonlReader(IntermediateFiles.CompletionBatchEvaluationThinking1) as reader:
    for line in reader:
        api_response: CompletionApiResponse = line
        if api_response["error"] is not None:
            warn(f"Error in response: {api_response['error']}")
            continue
        content = api_response["response"]["body"]["choices"][0]["message"]["content"]
        score = parse_score(content)
        if score is None:
            warn(f"No score found in response: {content}")
            continue

