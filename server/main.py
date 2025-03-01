from fastapi import FastAPI, Query
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from typing import Any
from json import load

app = FastAPI()

with open('server/textbook.json', 'r', encoding='utf-8') as f:
    textbook_data = load(f)
    tender_dict: dict[str, set[int]] = dict()
    for i, record in enumerate(textbook_data):
        word = record['context'][record['index_range'][0]:record['index_range'][1]]
        for ch in word:
            if ch not in tender_dict:
                tender_dict[ch] = set()
            tender_dict[ch].add(i)


@app.get("/api/query")
async def query(q: str = Query(..., description="The query word")) -> list[Any]:
    if not q:
        return []
    possible_set = tender_dict.get(q[0]) or set()
    for ch in q[1:]:
        possible_set = possible_set & tender_dict[ch]
    result = [textbook_data[i] for i in possible_set]
    return result

@app.get("/")
async def root():
    return RedirectResponse('/index.html')


app.mount("/", StaticFiles(directory="client/build"), name="static")

