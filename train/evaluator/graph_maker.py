import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from typing import List

# Convert the string data into a DataFrame
with open("./train/result/evaluation-results.csv", "r", encoding="gbk") as f:
    df = pd.read_csv(f, index_col=False)

    numeric_cols = df.columns[df.columns != "model_name"]
    df[numeric_cols] = (
        df[numeric_cols]
        .apply(pd.to_numeric, errors="coerce")
        .apply(lambda row: row.fillna(row.mean()), axis=1)
    )


def simplify_model_name(model_name: str) -> str:
    return (
        model_name.replace("-avg", "")
        .replace("qwen3-8b", "q8")
        .replace("qwen3-14b", "q14")
        .replace("qwen3-32b", "q32")
        .replace("qwen-max", "qm")
        .replace("deepseek-v3", "ds")
        .replace("flash", "F")
        .replace("-thinking", "")
    )


def plot_row_average_scores_line(df: pd.DataFrame) -> None:
    # Calculate the average score for each row across the numeric columns
    df["row_average"] = df[numeric_cols].mean(axis=1)

    low_score_indices: List[int] = df[df["row_average"] < 2].index.tolist()

    print("Rows with average score < 2:", low_score_indices)

    # Plotting
    plt.figure(figsize=(15, 10))
    plt.plot(df["row_average"], marker="o")

    for index in low_score_indices:
        plt.scatter(index, df.loc[index, "row_average"], color="red", zorder=5)

    plt.title("Line Plot of Average Scores for Each Row")
    plt.xlabel("Row")
    plt.ylabel("Average Score")
    plt.grid(True)
    plt.show()

def plot_bar_chart(df: pd.DataFrame) -> None:
    models: List[str] = [
        "eck-flash-avg",
        "eck-thinking-avg",
        "qwen3-8b-flash-avg",
        "taiyan-avg",
        "qwen3-8b-avg",
        "qwen-max-avg",
        "deepseek-v3-avg",
    ]

    # Calculate means and standard deviations
    means = [df[model].mean() for model in models]
    stds = [df[model].std() for model in models]
    
    # Calculate perfect score rates (scores >= 3)
    perfect_rates = [
        (df[model] >= 2.49).sum() / len(df[model]) * 100 for model in models
    ]

    # Simplify model names for display
    simple_names = [simplify_model_name(model) for model in models]

    # Create bar chart
    fig, ax = plt.subplots(figsize=(12, 8))
    bars = plt.bar(
        simple_names,
        means,
        yerr=stds,
        capsize=5,
        alpha=0.7,
        color="skyblue",
        edgecolor="navy",
    )

    # Add value labels on bars (mean ± std)
    for bar, mean, std in zip(bars, means, stds):
        height = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2.0,
            height + std + 0.05,
            f"{mean:.2f}±{std:.2f}",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    # Add perfect score rate as text on bars
    for bar, rate in zip(bars, perfect_rates):
        plt.text(
            bar.get_x() + bar.get_width() / 2.0,
            bar.get_height() + 0.2,
            f"Full={rate:.1f}%",
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold",
            color="darkblue",
        )

    # Add a horizontal line at y=3 to indicate full score
    plt.axhline(y=3, color='green', linestyle='--', linewidth=2, label='Full Score (3.0)')
    plt.legend()

    plt.title("Average Scores for Each Model", fontsize=16)
    plt.xlabel("Model", fontsize=12)
    plt.ylabel("Average Score", fontsize=12)
    plt.ylim(1.0, 4.0)
    plt.grid(True, axis="y")

    # Rotate x-axis labels for better readability
    plt.xticks(rotation=30, ha="right", fontsize=10)
    plt.yticks(fontsize=10)

    # Adjust layout to prevent label cutoff
    plt.tight_layout()
    
    # Show the plot
    plt.show()

# Call the plotting functions
plot_bar_chart(df)
plot_row_average_scores_line(df)
