from re import match, DOTALL
from train.utils import JsonlReader, JsonlWriter, IntermediateFiles, SYSTEM_PROMPTS
from train.models import CompletionApiResponse, Note, PromptRaw
from warnings import warn
from dataclasses import dataclass


@dataclass
class ScoredResponse:
    answer: str
    model: str
    scores: list[float]

    def get_average(self) -> float | None:
        if len(self.scores) == 0:
            return None
        return sum(self.scores) / len(self.scores)


@dataclass
class ScoredNote:
    base: Note
    prompt: str
    responses: dict[str, ScoredResponse]


def parse_grade(message: str) -> str | None:
    """
    Parse the score from the message.
    <think>...</think><grade>A</grade>
    """

    grade_match = match(r"(.*?)\<grade\>([ABCDE])\<\/grade\>", message.strip(), DOTALL)

    if grade_match:
        return str(grade_match.group(2))
    else:
        return None


def grade_to_score(grade: str | None) -> float | None:
    if grade is None:
        return None
    return {
        'A': 1.0,
        'B': 0.8,
        'C': 0.5,
        'D': 0.2,
        'E': 0.0,
    }.get(grade)



def check_integrity(message: str) -> bool:
    """
    Check the integrity of the response of the distilled model.
    """

    pattern = r"\*\*思考\*\*::.*?\n\*\*解释\*\*\:.*?\n\*\*答案\*\*\:.*?\n"
    return bool(match(pattern, message.strip(), DOTALL))


data: dict[int, ScoredNote] = {}


def add_data(api_response: CompletionApiResponse) -> None:
    if api_response["error"] is not None:
        warn(f"Error in response: {api_response['error']}")
        return
    content = api_response["response"]["body"]["choices"][0]["message"]["content"]
    id_match = match(r"request-tb-(\d{4})-([a-zA-Z]+)", api_response["custom_id"])
    if not id_match:
        return
    note_id = int(id_match.group(1).lstrip("0") or "0")
    model = id_match.group(2)

    if not check_integrity(content):
        single_line_content = content.replace("\n", "")
        if "<answers>" in single_line_content and not "</answers>" in single_line_content:
            print(f"Response {model} {note_id:04d} incomplete, lacking </answers>")
        else:
            warn(f"Response is not complete: {single_line_content}")
        return
    if model not in data[note_id].responses:
        data[note_id].responses[model] = ScoredResponse(content, model, [])



def add_score(api_response: CompletionApiResponse) -> None:
    if api_response["error"] is not None:
        warn(f"Error in response: {api_response['error']}")
        return
    content = api_response["response"]["body"]["choices"][0]["message"]["content"]
    grade = parse_grade(content)
    score = grade_to_score(grade)
    if score is None:
        single_line_content = content.replace("\n", "")
        warn(f"No score found in response: {single_line_content}")
        return
    id_match = match(r"request-tb-(\d{4})-([a-zA-Z]+)-ev-(.*)", api_response["custom_id"])
    if not id_match:
        return

    note_id = int(id_match.group(1).lstrip("0") or "0")
    model = id_match.group(2)
    if note_id not in data:
        warn(f"Note {note_id} not found in dataset")
        return

    if model not in data[note_id].responses:
        warn(f"Model {model} not found in note {note_id}")
        return
    data[note_id].responses[model].scores.append(score)


with JsonlReader(IntermediateFiles.DatasetThinkingRaw) as reader:
    for i, line in enumerate(reader):
        prompt_raw: PromptRaw = line
        user_prompt = prompt_raw["messages"][1]["content"]
        data[i] = ScoredNote(Note.from_dict(prompt_raw["note"]), user_prompt, {})


with JsonlReader(IntermediateFiles.CompletionBatchThinking1) as reader:
    for line in reader:
        add_data(line)

with JsonlReader(IntermediateFiles.CompletionBatchThinking2) as reader:
    for line in reader:
        add_data(line)

with JsonlReader(IntermediateFiles.CompletionBatchThinking3) as reader:
    for line in reader:
        add_data(line)


with JsonlReader(IntermediateFiles.CompletionBatchEvaluationThinking1) as reader:
    for line in reader:
        add_score(line)

with JsonlReader(IntermediateFiles.CompletionBatchEvaluationThinking2) as reader:
    for line in reader:
        add_score(line)


with JsonlWriter(IntermediateFiles.DatasetThinking) as writer, open(
    "./train/result/dataset-thinking-evaluation-scores.txt", "w", encoding="utf-8"
) as score_file:
    for note_id, note in data.items():
        ACCEPT_THRESHOLD = 0.89

        score_file.write(f"{note.base.get_original_text()}\t")
        responses = list(note.responses.items())
        scores: list[float] = []
        for model, response in responses:
            score = response.get_average()
            if score is None:
                warn(f"No score found for {model} in note {note_id}")
                continue
            scores.append(score)
            scores_display = ";".join(f"{s}" for s in response.scores)
            score_file.write(f"{model}:{score:.1f}:{scores_display}\t")
        if len(scores) == 0:
            warn(f"No score found for note {note_id}")
            score_file.write(f"EMPTY\n")
            continue
        max_score = max(scores)
        if max_score < ACCEPT_THRESHOLD:
            score_file.write(f"0\n")
            continue

        def accept_response(response: ScoredResponse) -> bool:
            avg = response.get_average()
            return avg is not None and avg >= ACCEPT_THRESHOLD

        accepted_models = [
            model for model, response in responses if accept_response(response)
        ]
        score_file.write(f"{len(accepted_models)}\n")
        for model in accepted_models:
            completion = {
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPTS.THINKING_SIMPLIFIED},
                    {"role": "user", "content": note.prompt},
                    {"role": "assistant", "content": note.responses[model].answer }
                ]
            }
            writer.write_line(completion)
