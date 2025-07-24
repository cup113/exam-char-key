import pandas as pd
import matplotlib.pyplot as plt
from typing import List

# Convert the string data into a DataFrame
with open("./train/result/evaluation-results-copy.csv", "r", encoding="gbk") as f:
    df = pd.read_csv(f, index_col=False)

    numeric_cols = df.columns[df.columns != 'model_name']
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce').apply(lambda row: row.fillna(row.mean()), axis=1)

def simplify_model_name(model_name: str) -> str:
    return (
        model_name.replace("-avg", "")
        .replace("qwen3-8b", "q8")
        .replace("qwen-max", "qm")
        .replace("deepseek-v3", "ds")
        .replace("flash", "F")
        .replace("-thinking", "")
    )

# Define a function to plot the average scores for each model as a box plot
def plot_average_scores_box(df: pd.DataFrame) -> None:
    models: List[str] = [
        "eck-flash-avg",
        "eck-thinking-avg",
        "qwen3-8b-flash-avg",
        "taiyan-avg",
        "qwen3-8b-avg",
        "qwen-max-avg",
        "deepseek-v3-avg",
        "eck-thinking-offline-avg",
    ]

    # Extract the data for the box plot
    data_to_plot: List[pd.Series] = [df[model] for model in models]

    # Plotting
    plt.figure(figsize=(15, 10))
    plt.boxplot(
        data_to_plot,
        tick_labels=[simplify_model_name(model) for model in models],
        meanline=True,
        showmeans=True,
    )

    plt.title("Box Plot of Average Scores for Each Model")
    plt.xlabel("Model")
    plt.ylabel("Average Score")
    plt.grid(True)
    plt.show()

def plot_row_average_scores_line(df: pd.DataFrame) -> None:
    # Calculate the average score for each row across the numeric columns
    df['row_average'] = df[numeric_cols].mean(axis=1)

    low_score_indices: List[int] = df[df['row_average'] < 2.3].index.tolist()

    print("Rows with average score < 2.3:", low_score_indices)

    # Plotting
    plt.figure(figsize=(15, 10))
    plt.plot(df['row_average'], marker='o')

    for index in low_score_indices:
        plt.scatter(index, df.loc[index, 'row_average'], color='red', zorder=5)

    plt.title("Line Plot of Average Scores for Each Row")
    plt.xlabel("Row")
    plt.ylabel("Average Score")
    plt.grid(True)
    plt.show()

# Call the plotting functions
plot_average_scores_box(df)
plot_row_average_scores_line(df)
