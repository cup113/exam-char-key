import pandas as pd
import matplotlib.pyplot as plt

# Convert the string data into a DataFrame
with open("./train/result/evaluation-results-copy.csv", "r", encoding="gbk") as f:
    df = pd.read_csv(f, index_col=False)

    numeric_cols = df.columns[df.columns != 'model_name']
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce').apply(lambda row: row.fillna(row.mean()), axis=1)
    df = df.fillna(3).clip(upper=3)

def simplify_model_name(model_name: str):
    return (
        model_name.replace("-avg", "")
        .replace("qwen3-8b", "q8")
        .replace("qwen-max", "qm")
        .replace("deepseek-v3", "ds")
        .replace("flash", "F")
        .replace("-thinking", "")
    )

# Define a function to plot the average scores for each model as a box plot
def plot_average_scores_box(df):
    models = [
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
    data_to_plot = [df[model] for model in models]

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

# Define a function to plot the average scores for each row as a line plot
def plot_row_average_scores_line(df):
    # Calculate the average score for each row across the numeric columns
    df['row_average'] = df[numeric_cols].mean(axis=1)

    # Plotting
    plt.figure(figsize=(15, 10))
    plt.plot(df['row_average'], marker='o')

    plt.title("Line Plot of Average Scores for Each Row")
    plt.xlabel("Row")
    plt.ylabel("Average Score")
    plt.grid(True)
    plt.show()

# Call the plotting functions
plot_average_scores_box(df)
plot_row_average_scores_line(df)
