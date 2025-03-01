import os
from openai import OpenAI
from json import loads

client = OpenAI(
    api_key=os.getenv("API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)
completion = client.chat.completions.create(
    model="qwen2.5-14b-instruct",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "请判断这篇文章是不是一篇文言文（包括古诗文），主要依据为其中语言是否可能包含一些文言词汇，因此近代诗文可能也包含在内。你应当在回答的结尾输出形如<p=0.5>的结果，其中数字表示偏向文言文的程度，经典文言文为1.0，经典现代文为0.0，你可以打得绝对一些。\n以下：标题：百合花\n作者或出处：茹志鹃\n首句：1946年的中秋。这天打海岸的部队决定晚上总攻。我们文工团创作室的几个同志，就由主攻团的团长分派到各个战斗连去帮助工作。大概因为我是个女同志吧，团长对我抓了半天后脑勺，最后才叫一个通讯员送我到前沿包扎所去。"},
    ],
)

print(loads(completion.model_dump_json())["choices"][0]["message"]["content"])
