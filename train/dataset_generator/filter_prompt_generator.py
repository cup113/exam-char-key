from train.utils import SYSTEM_PROMPTS, IntermediateFiles, JsonlReader, JsonlWriter
from train.models import Note, BatchRequest

with JsonlReader(IntermediateFiles.NotesTextbook) as f:
    notes = [Note.from_dict(line) for line in f]

with JsonlReader(IntermediateFiles.NotesModelTests) as f:
    notes.extend(Note.from_dict(line) for line in f)

with JsonlWriter(IntermediateFiles.PromptFilter) as f:
    for i, note in enumerate(notes):
        user_prompt = f"考察对象：“{note.context}”中的“{note.get_original_text()}”\n标准答案：{note.core_detail}”"
        req: BatchRequest = {
            "url": "/v1/chat/completions",
            "method": "POST",
            "custom_id": f"request-fr-{i:03d}",
            "body": {
                "model": "qwen-long-latest",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPTS.PRE_FILTER},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.2,
                "top_p": 0.8,
            }
        }
        f.write_line(req)
