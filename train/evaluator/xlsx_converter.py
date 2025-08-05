import json
import pandas as pd


def process_jsonl_to_excel(input_file: str, output_file: str):
    processed_data = []

    # 读取JSONL文件
    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():  # 跳过空行
                data = json.loads(line)

                # 提取基本信息
                index = data.get("index", "")
                type_value = data.get("type", "")  # 新增type字段
                context = data.get("context", "")
                query = data.get("query", "")
                correct_answer = data.get("correct_answer", "")

                # 处理answers字段
                answers = data.get("answers", {})

                # 为每个模型创建一列
                row_data = {
                    "index": index,
                    "type": type_value,  # 添加type字段到数据中
                    "context": context,
                    "query": query,
                    "correct_answer": correct_answer,
                }

                # 添加每个模型的回答
                for _model_id, answer_info in answers.items():
                    models = answer_info.get("models", [])
                    answer = answer_info.get("answer", "")
                    scores = answer_info.get("scores", [])
                    score = (sum(scores) / len(scores)) if scores else ""

                    # 使用模型名称作为列名
                    for model_name in models:
                        # 替换模型名称
                        display_name = model_name
                        display_name = display_name.replace("deepseek-v3", "ds")
                        display_name = display_name.replace("qwen-plus", "qp")
                        display_name = display_name.replace("qwen-long", "ql")
                        display_name = display_name.replace("qwen3-8b", "q8")
                        display_name = display_name.replace("-flash", "F")

                        row_data[f"{display_name}_answer"] = answer
                        row_data[f"{display_name}"] = score

                processed_data.append(row_data)

    # 转换为DataFrame
    df = pd.DataFrame(processed_data)

    # 创建新列 eckM, q8M, qpM 表示某些模型的最高分
    # 首先初始化这些列为0
    df["eckM"] = 0
    df["q8M"] = 0
    df["qpM"] = 0

    # 计算 eckM (eck-flash, eck-thinking 的最高分)
    eck_flash_scores = df.get("eckF", pd.Series([0] * len(df)))
    eck_thinking_scores = df.get("eck-thinking", pd.Series([0] * len(df)))
    df["eckM"] = pd.concat([eck_flash_scores, eck_thinking_scores], axis=1).max(axis=1)

    # 计算 q8M (qwen3-8b-flash, qwen3-8b 的最高分)
    q8_flash_scores = df.get("q8F", pd.Series([0] * len(df)))
    q8_scores = df.get("q8", pd.Series([0] * len(df)))
    df["q8M"] = pd.concat([q8_flash_scores, q8_scores], axis=1).max(axis=1)

    # 计算 qpM (qwen-plus, qwen-plus-flash 的最高分)
    qp_scores = df.get("qp", pd.Series([0] * len(df)))
    qp_flash_scores = df.get("qpF", pd.Series([0] * len(df)))
    df["qpM"] = pd.concat([qp_scores, qp_flash_scores], axis=1).max(axis=1)

    # 过滤出真正的分数列（模型分数列）
    actual_score_columns = [
        col
        for col in df.columns
        if not col.endswith("M") and not col.endswith("_answer") and col not in ["index", "type", "context", "query", "correct_answer"]
    ]
    if actual_score_columns:
        df["AVG"] = df[actual_score_columns].mean(axis=1, skipna=True)
    else:
        df["AVG"] = 0

    # 重新排列列的顺序，将分数列放在前面
    cols = df.columns.tolist()

    # 分离分数列和答案列
    other_cols = [col for col in cols if not col.endswith("_answer")]
    answer_cols = [col for col in cols if col.endswith("_answer")]

    # 定义模型排序
    model_order = [
        "eckF",
        "q8F",
        "taiyan",
        "qpF",
        "eck-thinking",
        "q8",
        "qp",
        "ql",
        "ds",
        "eckM",
        "q8M",
        "qpM",
    ]

    # 构建新的列顺序
    new_cols = ["index", "type"]

    new_cols.extend(["context", "query", "correct_answer", "AVG"])

    # 按指定顺序添加模型分数列
    for model in model_order:
        if model in other_cols:
            new_cols.append(model)

    # 添加剩余的其他列（如果有的话）
    for col in other_cols:
        if col not in new_cols:
            new_cols.append(col)

    # 最后添加答案列
    new_cols.extend(answer_cols)

    df = df[new_cols]

    # 保存为Excel文件
    df.to_excel(output_file, index=False, engine="openpyxl")
    print(f"数据已成功转换并保存到 {output_file}")


if __name__ == "__main__":
    input_file = "./train/result/final-raw.jsonl"
    output_file = "./train/result/final-raw.xlsx"

    process_jsonl_to_excel(input_file, output_file)
