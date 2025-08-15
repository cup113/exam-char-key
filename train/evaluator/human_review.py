import json
import csv
from typing import Dict, List, Any, Optional
from pathlib import Path
from scipy.stats import pearsonr
import tkinter as tk
from tkinter import ttk, messagebox


class ManualEvaluator:
    def __init__(
        self,
        completion_file: str = "./train/result/final-completion.jsonl",
        evaluation_file: str = "./train/result/final-evaluation-completion.jsonl",
        dataset_file: str = "./train/evaluation-dataset/dataset.csv",
        output_file: str = "./train/result/manual_evaluation_results.json",
    ):
        self.completion_file = completion_file
        self.evaluation_file = evaluation_file
        self.dataset_file = dataset_file
        self.output_file = output_file
        self.questions: Dict[int, Dict[str, Any]] = {}
        self.human_scores: Dict[int, Dict[str, float]] = {}
        self.ai_scores: Dict[int, Dict[str, float]] = {}
        self.current_index = 0
        self.sample_indices: List[int] = []
        # 存储当前题目的唯一答案（按hex去重）
        self.unique_answers: Dict[str, Dict[str, Any]] = {}
        # 存储评分结果
        self.current_ratings: Dict[str, str] = {}

        # 加载已有的人工作业评分
        self.load_human_scores()

    def load_questions(self):
        """加载所有问题和答案"""
        # 加载题目内容
        with open(self.dataset_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for index, row in enumerate(reader):
                self.questions[index] = {
                    "type": row["type"],
                    "context": row["context"],
                    "query": row["query"],
                    "correct_answer": row["answer"],
                    "answers": {},
                }

        # 加载模型答案（去重，相同hex只保留一个）
        with open(self.completion_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    data = json.loads(line.strip())
                    index = data["index"]
                    if index not in self.questions:
                        continue

                    hex_key = data["hex"]
                    # 对于每个题目和hex组合，只保留一个答案
                    if hex_key not in self.questions[index]["answers"]:
                        self.questions[index]["answers"][hex_key] = {
                            "answer": data["answer"],
                            "human_score": None,
                            "ai_score": None,
                        }

        # 加载AI评分
        with open(self.evaluation_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    data = json.loads(line.strip())
                    custom_id = data["custom_id"]
                    # 解析custom_id: final-000-7b449bfb1d41c399-ev-ql
                    parts = custom_id.split("-")
                    if len(parts) >= 4 and parts[0] == "final":
                        try:
                            index = int(parts[1])
                            hex_key = parts[2]

                            if (
                                index in self.questions
                                and hex_key in self.questions[index]["answers"]
                            ):
                                # 提取AI评分
                                content = data["response"]["body"]["choices"][0][
                                    "message"
                                ]["content"]
                                ai_score = self.extract_ai_score(content)
                                self.questions[index]["answers"][hex_key][
                                    "ai_score"
                                ] = ai_score
                                self.ai_scores.setdefault(index, {})[hex_key] = ai_score
                        except (ValueError, IndexError):
                            continue

    def extract_ai_score(self, content: str) -> Optional[float]:
        """从AI评分结果中提取分数"""
        if "<grade>" in content and "</grade>" in content:
            start = content.find("<grade>") + 7
            end = content.find("</grade>")
            grade = content[start:end].strip()[-1]  # 获取最后一个字符，即等级字母

            grade_mapping = {"A": 1.0, "B": 0.8, "C": 0.5, "D": 0.2, "E": 0.0}

            return grade_mapping.get(grade)
        return None

    def get_sample_indices(
        self, start: int = 18, step: int = 50, max_index: int = 749
    ) -> List[int]:
        """获取抽样索引"""
        indices: List[int] = []
        current = start
        while current <= max_index:
            indices.append(current)
            current += step
        return indices

    def load_human_scores(self):
        """加载已有的人工作业评分"""
        if Path(self.output_file).exists():
            with open(self.output_file, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    self.human_scores = data.get("human_scores", {})
                    # 转换为正确的数据类型
                    for index in list(self.human_scores):
                        self.human_scores[int(index)] = self.human_scores[index]
                except json.JSONDecodeError:
                    self.human_scores = {}

    def save_human_scores(self):
        """保存人工作业评分"""
        data = {"human_scores": self.human_scores, "stats": self.calculate_stats()}
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def rate_answer(self, index: int, hex_key: str, score: float):
        """给人工作业评分"""
        self.human_scores.setdefault(index, {})[hex_key] = score
        self.questions[index]["answers"][hex_key]["human_score"] = score
        self.save_human_scores()

    def calculate_stats(self) -> Dict[str, Any]:
        """计算统计信息"""
        # 收集所有评分对
        ai_scores_list = []
        human_scores_list = []

        for index in self.questions:
            for hex_key, answer_data in self.questions[index]["answers"].items():
                if (
                    answer_data["ai_score"] is not None
                    and answer_data["human_score"] is not None
                ):
                    ai_scores_list.append(answer_data["ai_score"])
                    human_scores_list.append(answer_data["human_score"])

        if len(ai_scores_list) > 1:
            correlation, p_value = pearsonr(ai_scores_list, human_scores_list)
            return {
                "total_rated": len(ai_scores_list),
                "correlation": correlation,
                "p_value": p_value,
            }
        else:
            return {
                "total_rated": len(ai_scores_list),
                "correlation": None,
                "p_value": None,
            }

    def get_next_unrated_question(self) -> Optional[int]:
        """获取下一个未评分的题目索引"""
        for index in self.sample_indices[self.current_index :]:
            # 检查是否已完成评分
            all_rated = True
            if index not in self.questions:
                continue

            for hex_key in self.questions[index]["answers"]:
                if (
                    index not in self.human_scores
                    or hex_key not in self.human_scores[index]
                    or self.human_scores[index][hex_key] is None
                ):
                    all_rated = False
                    break

            if not all_rated:
                return index
        return None

    def start_gui(self):
        """启动GUI界面"""
        self.load_questions()
        self.sample_indices = self.get_sample_indices()

        # 创建主窗口
        self.root = tk.Tk()
        self.root.title("人工评分工具")
        self.root.geometry("900x800")
        self.root.minsize(900, 800)

        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # 创建题目信息区域
        info_frame = ttk.LabelFrame(main_frame, text="题目信息", padding="10")
        info_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        info_frame.columnconfigure(1, weight=1)
        main_frame.columnconfigure(0, weight=1)

        # 题目索引
        ttk.Label(info_frame, text="题目索引:").grid(row=0, column=0, sticky=tk.W)
        self.index_label = ttk.Label(info_frame, text="")
        self.index_label.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))

        # 上下文
        ttk.Label(info_frame, text="上下文:").grid(row=1, column=0, sticky=(tk.W, tk.N))
        self.context_text = tk.Text(info_frame, height=3, width=70, wrap=tk.WORD)
        self.context_text.grid(
            row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=(5, 0)
        )
        self.context_text.config(state=tk.DISABLED)
        scrollbar_context = ttk.Scrollbar(
            info_frame, orient="vertical", command=self.context_text.yview
        )
        scrollbar_context.grid(row=1, column=2, sticky=(tk.N, tk.S))
        self.context_text.configure(yscrollcommand=scrollbar_context.set)

        # 查询词
        ttk.Label(info_frame, text="查询词:").grid(row=2, column=0, sticky=tk.W)
        self.query_label = ttk.Label(info_frame, text="")
        self.query_label.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=(5, 0))

        # 标准答案
        ttk.Label(info_frame, text="标准答案:").grid(row=3, column=0, sticky=tk.W)
        self.correct_answer_label = ttk.Label(info_frame, text="")
        self.correct_answer_label.grid(
            row=3, column=1, sticky=tk.W, padx=(10, 0), pady=(5, 0)
        )

        # 答案区域
        answer_frame = ttk.LabelFrame(main_frame, text="待评分答案", padding="10")
        answer_frame.grid(
            row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10)
        )
        answer_frame.columnconfigure(0, weight=1)
        answer_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)

        # 创建Canvas和滚动条用于答案列表
        self.canvas = tk.Canvas(answer_frame)
        scrollbar = ttk.Scrollbar(
            answer_frame, orient="vertical", command=self.canvas.yview
        )
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # 评分区域
        rating_frame = ttk.LabelFrame(main_frame, text="评分", padding="10")
        rating_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        ttk.Label(
            rating_frame, text="请为每个答案选择评分等级:", font=("Arial", 12)
        ).grid(row=0, column=0, columnspan=5, pady=(0, 10))

        # 确认按钮
        self.confirm_button = ttk.Button(
            rating_frame, text="确认", command=self.confirm_ratings, state=tk.DISABLED
        )
        self.confirm_button.grid(row=1, column=5, padx=(20, 0))

        # 统计信息
        stats_frame = ttk.LabelFrame(main_frame, text="统计信息", padding="10")
        stats_frame.grid(row=3, column=0, sticky=(tk.W, tk.E))
        stats_frame.columnconfigure(1, weight=1)

        ttk.Label(stats_frame, text="已完成:").grid(row=0, column=0, sticky=tk.W)
        self.completed_label = ttk.Label(stats_frame, text="0/0")
        self.completed_label.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))

        ttk.Label(stats_frame, text="相关系数:").grid(row=1, column=0, sticky=tk.W)
        self.correlation_label = ttk.Label(stats_frame, text="N/A")
        self.correlation_label.grid(row=1, column=1, sticky=tk.W, padx=(10, 0))

        # 控制按钮
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(10, 0))

        self.prev_button = ttk.Button(
            control_frame, text="上一题", command=self.prev_question, state=tk.DISABLED
        )
        self.prev_button.grid(row=0, column=0, padx=(0, 5))

        self.skip_button = ttk.Button(
            control_frame, text="跳过题目", command=self.skip_question
        )
        self.skip_button.grid(row=0, column=1, padx=5)

        self.next_button = ttk.Button(
            control_frame, text="下一题", command=self.next_question
        )
        self.next_button.grid(row=0, column=2, padx=5)

        self.save_button = ttk.Button(
            control_frame, text="保存并退出", command=self.save_and_exit
        )
        self.save_button.grid(row=0, column=3, padx=(5, 0))

        # 加载第一个题目
        self.load_next_question()

        # 启动GUI主循环
        self.root.mainloop()

    def load_question(self, index: int):
        """加载题目到界面"""
        if index not in self.questions:
            messagebox.showerror("错误", f"题目 {index} 不存在")
            return

        question = self.questions[index]

        # 显示题目信息
        self.index_label.config(text=str(index))
        self.context_text.config(state=tk.NORMAL)
        self.context_text.delete(1.0, tk.END)
        self.context_text.insert(1.0, question["context"])
        self.context_text.config(state=tk.DISABLED)
        self.query_label.config(text=question["query"])
        self.correct_answer_label.config(text=question["correct_answer"])

        # 准备唯一答案列表（按hex去重）
        self.unique_answers = question["answers"].copy()
        self.current_ratings = {}  # 重置当前评分

        # 显示所有答案
        self.display_answers()

    def display_answers(self):
        """显示所有唯一答案"""
        # 清除之前的答案显示
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        # 显示所有唯一答案
        for i, (hex_key, answer_data) in enumerate(self.unique_answers.items()):
            # 答案框架
            answer_frame = ttk.Frame(self.scrollable_frame)
            answer_frame.grid(row=i, column=0, sticky=(tk.W, tk.E), pady=5)
            answer_frame.columnconfigure(1, weight=1)

            # 答案编号
            ttk.Label(answer_frame, text=f"{i+1}.", width=3).grid(
                row=0, column=0, sticky=tk.W, padx=(0, 5)
            )

            # 答案文本
            answer_text = tk.Text(answer_frame, height=2, width=60, wrap=tk.WORD)
            answer_text.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
            answer_text.insert(1.0, answer_data["answer"])
            answer_text.config(state=tk.DISABLED)

            # 评分按钮框架
            grade_frame = ttk.Frame(answer_frame)
            grade_frame.grid(row=0, column=2)

            # 为每个答案创建独立的评分按钮
            grades = [("A", 1.0), ("B", 0.8), ("C", 0.5), ("D", 0.2), ("E", 0.0)]
            for j, (grade, score) in enumerate(grades):
                button = ttk.Button(
                    grade_frame,
                    text=grade,
                    width=3,
                    command=lambda h=hex_key, g=grade, s=score: self.rate_answer_item(
                        h, g, s
                    ),
                )
                button.grid(row=0, column=j, padx=2)

            # 已评分显示
            rating_var = tk.StringVar(value="")
            rating_label = ttk.Label(answer_frame, textvariable=rating_var, width=5)
            rating_label.grid(row=0, column=3, padx=(10, 0))

            # 保存引用以便后续更新
            setattr(self, f"rating_var_{hex_key}", rating_var)

        # 更新确认按钮状态
        self.update_confirm_button_state()

    def rate_answer_item(self, hex_key: str, grade: str, score: float):
        """为特定答案项评分"""
        # 直接保存评分
        self.current_ratings[hex_key] = grade

        # 更新界面显示
        rating_var = getattr(self, f"rating_var_{hex_key}")
        rating_var.set(f"({grade})")

        # 更新确认按钮状态
        self.update_confirm_button_state()

    def update_confirm_button_state(self):
        """更新确认按钮状态"""
        # 当所有答案都已评分时，激活确认按钮
        if (
            len(self.current_ratings) == len(self.unique_answers)
            and len(self.unique_answers) > 0
        ):
            self.confirm_button.config(state=tk.NORMAL)
        else:
            self.confirm_button.config(state=tk.DISABLED)

    def confirm_ratings(self):
        """确认所有评分"""
        if self.current_index >= len(self.sample_indices):
            return

        index = self.sample_indices[self.current_index]
        if index not in self.questions:
            return

        # 保存所有评分
        for hex_key, grade in self.current_ratings.items():
            # 转换等级到分数
            grade_mapping = {"A": 1.0, "B": 0.8, "C": 0.5, "D": 0.2, "E": 0.0}
            score = grade_mapping[grade]
            self.rate_answer(index, hex_key, score)

        # 移动到下一题
        self.finish_question()

    def load_next_question(self):
        """加载下一个未评分的题目"""
        next_index = self.get_next_unrated_question()
        if next_index is not None:
            self.current_index = self.sample_indices.index(next_index)
            self.load_question(next_index)
            self.update_stats()
        else:
            # 所有题目评分完成
            messagebox.showinfo("完成", "所有抽样题目已完成评分！")
            self.update_stats()

    def finish_question(self):
        """完成当前题目的评分"""
        self.current_index += 1
        self.load_next_question()

    def prev_question(self):
        """上一题"""
        if self.current_index > 0:
            self.current_index -= 1
            index = self.sample_indices[self.current_index]
            self.load_question(index)
            self.update_stats()

    def next_question(self):
        """下一题"""
        if self.current_index < len(self.sample_indices) - 1:
            self.current_index += 1
            index = self.sample_indices[self.current_index]
            self.load_question(index)
            self.update_stats()

    def skip_question(self):
        """跳过当前题目"""
        self.finish_question()

    def update_stats(self):
        """更新统计信息"""
        # 更新已完成数量
        completed = 0
        total_rated = 0

        for index in self.sample_indices[: self.current_index + 1]:
            if index in self.questions:
                for hex_key in self.questions[index]["answers"]:
                    if (
                        index in self.human_scores
                        and hex_key in self.human_scores[index]
                        and self.human_scores[index][hex_key] is not None
                    ):
                        total_rated += 1
                completed += 1

        self.completed_label.config(text=f"{completed}/{len(self.sample_indices)}")

        # 更新相关系数
        stats = self.calculate_stats()
        if stats["correlation"] is not None:
            self.correlation_label.config(text=f"{stats['correlation']:.4f}")
        else:
            self.correlation_label.config(text="N/A")

        # 更新按钮状态
        self.prev_button.config(
            state=tk.NORMAL if self.current_index > 0 else tk.DISABLED
        )

    def save_and_exit(self):
        """保存并退出"""
        self.save_human_scores()
        stats = self.calculate_stats()
        messagebox.showinfo(
            "评分统计",
            f"已完成评分数量: {stats['total_rated']}\n"
            f"AI评分与人工评分相关系数: {stats['correlation'] if stats['correlation'] is not None else 'N/A'}\n"
            f"P值: {stats['p_value'] if stats['p_value'] is not None else 'N/A'}",
        )
        self.root.quit()


if __name__ == "__main__":
    evaluator = ManualEvaluator()
    evaluator.start_gui()
