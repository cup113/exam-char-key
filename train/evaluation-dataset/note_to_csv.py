import json
import os


def convert_textbook_to_dataset(input_file: str, output_file: str):
    """
    将textbook-selected.jsonl格式转换为dataset.csv格式
    """
    if not os.path.exists(input_file):
        print(f"错误：输入文件 {input_file} 不存在")
        return

    with open(input_file, "r", encoding="utf-8") as fi, open(
        output_file, "w", encoding="utf-8"
    ) as outfile:
        for line_num, line in enumerate(fi, 1):
            try:
                # 解析JSON行
                data = json.loads(line.strip())

                # 提取数据
                context = data["context"]
                index_start, index_end = data["index_range"]
                detail = data["core_detail"]

                # 提取关键词
                keyword = context[index_start:index_end]

                # 写入CSV格式
                outfile.write(f"dtset-txt-off,{context},{keyword},{detail}\n")

            except json.JSONDecodeError as e:
                print(f"警告：第 {line_num} 行 JSON 解析错误：{e}")
            except KeyError as e:
                print(f"警告：第 {line_num} 行缺少必要字段：{e}")
            except Exception as e:
                print(f"警告：第 {line_num} 行处理出错：{e}")


if __name__ == "__main__":
    input_file = "train/evaluation-dataset/textbook-selected.jsonl"
    output_file = "train/evaluation-dataset/dataset-textbook.csv"

    convert_textbook_to_dataset(input_file, output_file)
    print(f"转换完成，结果已保存到 {output_file}")
