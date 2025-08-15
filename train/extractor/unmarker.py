import fitz  # type: ignore
from tqdm import tqdm
import os

# 定义要处理的教材路径
PATHS_TEXTBOOK = [
    "train/textbooks/统编版-高中语文必修上册.pdf",
    "train/textbooks/统编版-高中语文必修下册.pdf",
    "train/textbooks/统编版-高中语文选择性必修上册.pdf",
    "train/textbooks/统编版-高中语文选择性必修中册.pdf",
    "train/textbooks/统编版-高中语文选择性必修下册.pdf",
]

# Y坐标阈值
Y_THRESHOLD = 830


def process_pdf(input_path: str, output_path: str):
    """
    处理PDF文件，删除y坐标>830的内容
    """
    # 打开PDF文档
    doc = fitz.open(input_path)

    # 创建进度条
    progress = tqdm(
        desc=f"Processing {os.path.basename(input_path)}", total=len(doc), unit="Page"
    )

    # 遍历每一页
    for page in doc:
        # 获取页面上的所有绘图对象
        drawings = page.get_drawings()

        # 删除y坐标大于阈值的内容
        page.get_contents()
        for drawing in drawings:
            if "items" in drawing:
                for item in drawing["items"]:
                    if item[0] == "l":  # 线条
                        # 检查线条的y坐标
                        if item[1].y > Y_THRESHOLD or item[2].y > Y_THRESHOLD:
                            # 这里我们不能直接删除个别元素，需要通过内容编辑方式处理
                            pass

        # 获取页面上的所有文本块
        blocks = page.get_textpage().extractDICT()["blocks"]

        # 遍历文本块，标记需要删除的内容
        for block in blocks:
            if block["type"] == 0:  # 文本块
                for line in block["lines"]:
                    for span in line["spans"]:
                        # 检查文本的y坐标
                        if span["origin"][1] > Y_THRESHOLD:
                            # 创建一个红色矩形覆盖需要删除的文本（演示用途）
                            # 实际应用中，我们使用更精确的方法
                            pass

        # 使用更精确的方法：创建新的内容流，只保留需要的内容
        page_rect = page.rect
        # 创建一个矩形区域，只包含y坐标小于等于阈值的部分
        keep_rect = fitz.Rect(0, 0, page_rect.width, min(Y_THRESHOLD, page_rect.height))

        # 清除页面内容，只保留指定区域内的内容
        page.set_cropbox(keep_rect)

        progress.update(1)

    progress.close()

    # 保存处理后的文档
    doc.save(output_path)
    doc.close()


def main():
    """
    主函数：处理所有教材PDF文件
    """
    print("开始处理PDF文件，删除y坐标>830的内容...")

    # 确保输出目录存在
    output_dir = "train/textbooks/processed"
    os.makedirs(output_dir, exist_ok=True)

    # 处理每个教材文件
    for path in PATHS_TEXTBOOK:
        if os.path.exists(path):
            filename = os.path.basename(path)
            name, ext = os.path.splitext(filename)
            output_filename = f"{name}{ext}"
            output_path = os.path.join(output_dir, output_filename)

            print(f"正在处理: {filename}")
            process_pdf(path, output_path)
            print(f"已保存到: {output_path}")
        else:
            print(f"文件不存在: {path}")

    print("所有文件处理完成！")


if __name__ == "__main__":
    main()
