from train.utils import IntermediateFiles, JsonlReader, JsonlWriter
from train.models import CompletionApiResponse
from re import match, DOTALL
from pydantic import BaseModel
from warnings import warn
from csv import DictReader


class FinalCompletionRaw(BaseModel):
    index: int
    answer: str
    hex: str
    model: str


class ScoredAnswer(BaseModel):
    answer: str
    models: list[str]
    score: float


class ScoredQuestion(BaseModel):
    index: int
    type: str
    context: str
    query: str
    correct_answer: str
    answers: dict[str, ScoredAnswer]


def extract_score(content: str) -> float | None:
    match_obj = match(r"(.*?)\<grade\>.*([A-E]).*<\/grade\>", content, DOTALL)
    if match_obj is None:
        return None
    return {
        "A": 1.0,
        "B": 0.8,
        "C": 0.5,
        "D": 0.2,
        "E": 0.0,
    }[match_obj.group(2)]


questions: dict[int, ScoredQuestion] = {}

with JsonlReader(IntermediateFiles.CompletionFinals) as f:
    for final_completion in f:
        r = FinalCompletionRaw.model_validate(final_completion)
        questions.setdefault(
            r.index,
            ScoredQuestion(
                type="", context="", query="", correct_answer="", answers={}, index=r.index
            ),
        ).answers.setdefault(
            r.hex, ScoredAnswer(answer=r.answer, models=[], score=0.88)
        ).models.append(
            r.model
        )

with open("./train/evaluation-dataset/dataset.csv", "r", encoding="utf-8") as f:
    reader = DictReader(f)
    for index, row in enumerate(reader):
        questions[index].type = row["type"]
        questions[index].context = row["context"]
        questions[index].query = row["query"]
        questions[index].correct_answer = row["answer"]

def process_score_response(response: CompletionApiResponse) -> None:
    cid = response["custom_id"]
    cid_match = match(r"final-(\d+)-([0-9a-f]+)-ev-([a-z]+)", cid)
    assert cid_match is not None, f"Invalid custom id: {cid}"
    note_id = int(cid_match.group(1).lstrip("0") or "0")
    answer_hex = cid_match.group(2)
    score_content = response["response"]["body"]["choices"][0]["message"]["content"]
    score = extract_score(score_content)
    if score is None:
        warn(f"Invalid score: {score_content}")
        return
    questions[note_id].answers[answer_hex].score = score


with JsonlReader(IntermediateFiles.CompletionBatchEvaluationFinal) as f:
    for final_evaluation in f:
        response: CompletionApiResponse = final_evaluation
        process_score_response(response)

with JsonlWriter(IntermediateFiles.FinalRaw) as f:
    for question in questions.values():
        f.write_line(question.model_dump())
