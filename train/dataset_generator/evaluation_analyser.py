import csv


def parse_line(line: str):
    parts = line.strip().split("\t")
    word = parts[0]
    qm_qp = qm_ql = qm_avg = ds_qp = ds_ql = ds_avg = None
    pass_count = int(parts[-1])

    for part in parts[1:-1]:
        if part.startswith("qm:"):
            scores = part.split(":")[2].split(";")
            qm_avg = float(part.split(":")[1])
            qm_qp = float(scores[0])
            qm_ql = float(scores[1]) if len(scores) == 2 else None
        elif part.startswith("ds:"):
            scores = part.split(":")[2].split(";")
            ds_avg = float(part.split(":")[1])
            ds_qp = float(scores[0])
            ds_ql = float(scores[1]) if len(scores) == 2 else None

    return word, qm_qp, qm_ql, qm_avg, ds_qp, ds_ql, ds_avg, pass_count


def convert_to_csv(input_file: str, output_file: str):
    with open(input_file, "r", encoding="utf-8") as infile, open(
        output_file, "w", newline="", encoding="gbk"
    ) as outfile:
        reader = infile.readlines()
        writer = csv.writer(outfile)
        writer.writerow(
            ["词汇", "qm-qp", "qm-ql", "qm-平均", "ds-qp", "ds-ql", "ds-平均", "通过数"]
        )

        for line in reader:
            word, qm_qp, qm_ql, qm_avg, ds_qp, ds_ql, ds_avg, pass_count = parse_line(
                line
            )
            writer.writerow(
                [word, qm_qp, qm_ql, qm_avg, ds_qp, ds_ql, ds_avg, pass_count]
            )


# Specify the input and output file paths
input_file_path = "./train/result/dataset-thinking-evaluation-scores.txt"
output_file_path = "./train/result/dataset-thinking-evaluation-scores.csv"

# Convert the file
convert_to_csv(input_file_path, output_file_path)
