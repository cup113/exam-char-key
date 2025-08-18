import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import re

# 读取CSV文件
df = pd.read_csv("train/result/final-raw.csv")

# 设置中文字体
plt.rcParams["font.sans-serif"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False

# 定义模型分组颜色
model_groups = {
    "eck": "#00bab1",
    "q8": "#0075bf",
    "ql": "#39405E",
    "taiyan": "#0a6409",
    "ds": "#414036",
}


def get_model_group(model_name: str):
    if model_name.startswith("eck"):
        return "eck"
    elif model_name.startswith("q8"):
        return "q8"
    elif model_name.startswith("ql"):
        return "ql"
    elif model_name.startswith("taiyan"):
        return "taiyan"
    elif model_name.startswith("ds"):
        return "ds"
    else:
        raise ValueError(f"Invalid model name: {model_name}")


# 图1: 当前标准下的总分（满分750）
model_scores: dict[str, float] = {}
for col in df.columns:
    if col in ["index", "type", "context", "query", "correct_answer", "AVG"]:
        continue
    if col == "qfF":
        continue
    if not "_answer" in col:
        model_scores[col] = df[col].sum()

# 创建第一个图表 - 当前标准总分
fig1, ax1 = plt.subplots(figsize=(8, 6))
models = list(model_scores.keys())
scores = list(model_scores.values())
colors = [model_groups[get_model_group(model)] for model in models]

# 反转顺序（从上到下显示）
models.reverse()
scores.reverse()
colors.reverse()

# 使用横向条形图并添加误差棒
bars = ax1.barh(models, scores, color=colors, capsize=3)
ax1.set_xlabel("总分", fontsize=14)
ax1.set_ylabel("模型", fontsize=14)
ax1.set_xlim(500, 750)

# 添加数值标签
for bar, score in zip(bars, scores):
    ax1.text(
        bar.get_width() - 5,
        bar.get_y() + bar.get_height() / 2,
        f"{score:.1f}",
        ha="right",
        va="center",
        fontsize=12,
        color="white",
    )

# 添加图例
legend_elements = [
    plt.Rectangle((0, 0), 1, 1, color=model_groups[group], label=group)
    for group in model_groups.keys()
]
ax1.legend(handles=legend_elements, title="模型类型", loc="upper right")

plt.tight_layout()
plt.savefig(
    "train/result/chart1_total_scores_current_standard.png",
    dpi=300,
    bbox_inches="tight",
)


# 图2: 各分项不同性质的测评集模型准确率（表格形式）
# 定义分类规则
def classify_type(type_str: str):
    if type_str == "dtset-txt-off":
        return "A"
    elif re.match(r"model-.*-(blk|cho)", type_str):
        return "B"
    elif re.match(r"model-.*-trn", type_str):
        return "C"
    elif re.match(r".*-(oth|onl)", type_str):
        return "D"
    else:
        return "D"  # 默认归为D类


# 添加分类列
df["category"] = df["type"].apply(classify_type)

# 计算各类别中各模型的准确率
categories = ["A", "B", "C", "D"]
category_names = {"A": "课文注解", "B": "模卷释义", "C": "模卷翻译", "D": "非官方数据"}

# 计算每个类别的数据条数
category_counts = df["category"].value_counts().to_dict()

# 获取需要评估的模型列
model_columns = [
    col
    for col in df.columns
    if col
    not in ["index", "type", "context", "query", "correct_answer", "AVG", "category"]
    and not "_answer" in col
]

# 计算每个模型在各类别中的准确率
model_category_scores = {}
for model in model_columns:
    model_category_scores[model] = {}
    for category in categories:
        category_data = df[df["category"] == category]
        score = category_data[model].mean() * 100  # 转换为百分比
        model_category_scores[model][category] = score

# 创建表格数据
table_data = []
for model in model_columns:
    row = [model]
    for category in categories:
        row.append(f"{model_category_scores[model][category]:.1f}")
    table_data.append(row)

# 创建DataFrame
columns = ["模型"] + [
    f"{cat}\n{category_names[cat]}\n({category_counts.get(cat, 0)}条)"
    for cat in categories
]
table_df = pd.DataFrame(table_data, columns=columns)

# 保存为Excel文件
table_df.to_excel("train/result/chart2_category_accuracy_table.xlsx", index=False)


# 定义模型样式
def get_model_style(model_name: str):
    # 灰色显示对照模型
    big_model = ["ql", "qf", "ds"]
    if any(model_name.startswith(m) for m in big_model):
        return "gray"

    # 浅绿色显示经处理的数据
    handled = ["eckM", "q8M"]
    if model_name in handled:
        return "lightgreen"

    return "normal"


# 找出各类别中的最高分模型（针对特定模型组）
eck_q8_taiyan_models = [
    m
    for m in model_columns
    if any(m.startswith(prefix) for prefix in ["eck", "q8", "taiyan"])
]
f_models = [m for m in eck_q8_taiyan_models if m.endswith("F")]
t_models = [m for m in eck_q8_taiyan_models if m.endswith("T")]

# 找出F模型组中各类别的最高分
f_best_scores = {}
for category in categories:
    f_best_scores[category] = max(
        [model_category_scores[model][category] for model in f_models]
    )

# 找出T模型组中各类别的最高分
t_best_scores = {}
for category in categories:
    t_best_scores[category] = max(
        [model_category_scores[model][category] for model in t_models]
    )

# 创建表格图表
fig, ax = plt.subplots(figsize=(12, 8))
ax.axis("tight")
ax.axis("off")

# 准备表格数据和样式
table_data = []
for model in model_columns:
    row = [model]
    for category in categories:
        score = model_category_scores[model][category]
        row.append(f"{score:.1f}")
    table_data.append(row)

# 创建表格
table = ax.table(cellText=table_data, colLabels=columns, cellLoc="center", loc="center")

# 设置表格样式
table.auto_set_font_size(False)
table.set_fontsize(10)
table.scale(1.2, 1.5)

# 应用样式
for i, model in enumerate(model_columns):
    # 设置行样式
    style = get_model_style(model)
    for j in range(len(columns)):
        cell = table[(i + 1, j)]
        if style == "gray":
            cell.set_text_props(color="gray")
        elif style == "lightgreen":
            cell.set_facecolor("#90EE90")  # 浅绿色

    # 设置粗体（各类别中的最高分）
    for j, category in enumerate(categories):
        score = model_category_scores[model][category]
        # F模型组中的最高分用粗体
        if model in f_models and score == f_best_scores[category]:
            cell = table[(i + 1, j + 1)]
            cell.set_text_props(weight="bold")
        # T模型组中的最高分用粗体
        elif model in t_models and score == t_best_scores[category]:
            cell = table[(i + 1, j + 1)]
            cell.set_text_props(weight="bold")

# 设置表头样式
for j in range(len(columns)):
    cell = table[(0, j)]
    cell.set_facecolor("#4472C4")
    cell.set_text_props(color="white", weight="bold")

plt.title("各数据类别下模型准确率对比", fontsize=14, pad=20)
plt.tight_layout()
plt.savefig(
    "train/result/chart2_category_accuracy_table.png", dpi=300, bbox_inches="tight"
)

print("图表已生成并保存至:")
print("1. train/result/chart1_total_scores_current_standard.png")
print("2. train/result/chart2_category_accuracy_table.png")
print("3. train/result/chart2_category_accuracy_table.xlsx")
