"""
processor.py - 多模态输入处理模块
负责解析用户上传的教学材料（PPT/PDF/图片），提取文本和图像路径，
输出统一的结构化JSON数据供后续模型调用使用。

支持的输入格式：
  - PDF (.pdf)   → 用 pdfplumber 提取每页文本
  - PPT (.pptx)  → 用 python-pptx 提取每页文本 + 尝试提取内嵌图片
  - 图片 (.png/.jpg等) → 直接作为图像路径保留

输出格式见函数 docstring 和 README 中的接口规范。
"""

import os
import shutil
from typing import List, Dict, Any, Optional

# PDF解析
import pdfplumber

# PPT解析
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

# 图像处理
from PIL import Image

# 项目内工具
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from modules.utils.helpers import (
    generate_material_id,
    get_file_type,
    get_file_name_without_ext,
    ensure_dir,
    save_json,
)


class MaterialProcessor:
    """
    教学材料处理器
    负责将各种格式的输入文件统一解析为结构化的材料数据
    """

    def __init__(self, raw_dir: str = "data/raw",
                 processed_dir: str = "data/processed"):
        """
        初始化处理器
        Args:
            raw_dir: 原始上传文件的存放目录
            processed_dir: 处理结果的输出目录
        """
        # 处理路径（相对于项目根目录）
        self.raw_dir = raw_dir
        self.processed_dir = processed_dir
        ensure_dir(raw_dir)
        ensure_dir(processed_dir)

    def process(self, file_path: str) -> Dict[str, Any]:
        """
        处理上传的文件，自动判断类型并调用对应的解析方法
        Args:
            file_path: 用户上传的文件路径
        Returns:
            统一格式的材料数据字典，格式：
            {
                "material_id": "material_xxx",
                "title": "文件名",
                "text_blocks": [{"page": 1, "text": "提取的文字"}, ...],
                "image_paths": ["图片路径1", "图片路径2"]
            }
        """
        file_type = get_file_type(file_path)
        material_id = generate_material_id()
        title = get_file_name_without_ext(file_path)

        # 将原始文件复制到 raw 目录
        raw_copy_path = os.path.join(self.raw_dir, os.path.basename(file_path))
        ensure_dir(self.raw_dir)
        if not os.path.exists(raw_copy_path):
            shutil.copy2(file_path, raw_copy_path)

        # 根据文件类型选择解析策略
        if file_type == "pdf":
            text_blocks, image_paths = self._parse_pdf(file_path, material_id)
        elif file_type == "ppt":
            text_blocks, image_paths = self._parse_ppt(file_path, material_id)
        elif file_type == "image":
            text_blocks, image_paths = self._parse_image(file_path, material_id)
        else:
            # 不支持的文件格式，返回空结果
            print(f"[警告] 不支持的文件格式: {file_path}")
            text_blocks, image_paths = [], []

        # 组装统一的输出结构
        material_data = {
            "material_id": material_id,
            "title": title,
            "text_blocks": text_blocks,
            "image_paths": image_paths,
        }

        # 保存处理结果到 processed 目录
        output_path = os.path.join(
            self.processed_dir, f"{material_id}.json"
        )
        save_json(material_data, output_path)
        print(f"[完成] 材料已处理并保存到: {output_path}")

        return material_data

    # ============================================================
    # PDF 解析
    # ============================================================
    def _parse_pdf(self, file_path: str, material_id: str
                   ) -> tuple[List[Dict], List[str]]:
        """
        解析 PDF 文件，提取每页文本
        Args:
            file_path: PDF 文件路径
            material_id: 材料ID（用于命名导出文件）
        Returns:
            (text_blocks, image_paths) 元组
            - text_blocks: [{"page": 页码, "text": "文本内容"}, ...]
            - image_paths: PDF中的图片路径列表（当前为占位，见下方注释）

        ⚠️ 占位说明:
            PDF 中内嵌图片的提取比较复杂，依赖 pdfminer 的底层 API。
            当前版本只提取文本，不提取图片。
            如需图片输入，请使用界面中的"上传补充图片"功能，
            或手动截图后上传。这是一个已知限制。
        """
        text_blocks = []

        try:
            with pdfplumber.open(file_path) as pdf:
                for i, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text()
                    if text and text.strip():
                        text_blocks.append({
                            "page": i,
                            "text": text.strip(),
                        })

            if not text_blocks:
                print(f"[提示] PDF 中未提取到文本内容，可能是扫描版 PDF")

        except Exception as e:
            print(f"[错误] PDF 解析失败: {e}")

        # ===== 占位: PDF图片提取 =====
        # pdfplumber 主要用于文本提取，对图片的支持有限。
        # 如需从 PDF 提取图片，可后续集成 pdfminer.six 的图片提取功能，
        # 或者使用 PyMuPDF (fitz) 库替代。当前返回空列表。
        image_paths = []

        return text_blocks, image_paths

    # ============================================================
    # PPT 解析
    # ============================================================
    def _parse_ppt(self, file_path: str, material_id: str
                   ) -> tuple[List[Dict], List[str]]:
        """
        解析 PPT 文件，提取每页文本和内嵌图片
        Args:
            file_path: PPT 文件路径
            material_id: 材料ID
        Returns:
            (text_blocks, image_paths) 元组

        ⚠️ 占位说明:
            1. 文本提取：正常可用，python-pptx 可提取幻灯片中的文本框文字。
            2. 内嵌图片提取：尝试从幻灯片中提取嵌入的图片文件（PNG/JPG等），
               保存到 processed 目录下。能提取就提取，不能则跳过。
            3. 幻灯片渲染为图片：这是最大的限制。由于需要系统安装 LibreOffice
               或依赖 Windows COM 组件，当前版本不自动将每页PPT渲染成图片。
               替代方案：用户可在界面中手动上传PPT截图作为图像输入。
        """
        text_blocks = []
        image_paths = []

        # 创建该材料专属的图片目录
        img_dir = os.path.join(self.processed_dir, f"{material_id}_images")
        ensure_dir(img_dir)

        try:
            prs = Presentation(file_path)

            for slide_idx, slide in enumerate(prs.slides, start=1):
                slide_texts = []
                has_text = False

                for shape in slide.shapes:
                    # ---- 提取文本 ----
                    if shape.has_text_frame:
                        for paragraph in shape.text_frame.paragraphs:
                            para_text = paragraph.text.strip()
                            if para_text:
                                slide_texts.append(para_text)
                                has_text = True

                    # ---- 尝试提取内嵌图片 ----
                    if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                        try:
                            image = shape.image
                            # 获取图片扩展名
                            ext = image.content_type.split("/")[-1]
                            if ext == "jpeg":
                                ext = "jpg"
                            img_filename = f"slide{slide_idx}_{shape.shape_id}.{ext}"
                            img_path = os.path.join(img_dir, img_filename)

                            # 保存图片
                            with open(img_path, "wb") as f:
                                f.write(image.blob)
                            image_paths.append(img_path)
                            print(f"[提取图片] {img_filename}")
                        except Exception as e:
                            # 图片提取不是核心功能，失败则跳过
                            print(f"[跳过图片] 幻灯片{slide_idx}中的图片提取失败: {e}")

                # 记录该页文本
                if has_text:
                    text_blocks.append({
                        "page": slide_idx,
                        "text": "\n".join(slide_texts),
                    })

            if not text_blocks:
                print("[提示] PPT 中未提取到文本内容（可能全是图片的PPT）")

        except Exception as e:
            print(f"[错误] PPT 解析失败: {e}")

        # ===== 占位: 幻灯片→图片渲染 =====
        # 将每页PPT渲染为整张图片需要外部工具支持（如 LibreOffice）。
        # 当前版本不支持此功能。用户可通过界面手动上传截图。
        # 如果后续想实现，可参考以下方案：
        #   - Windows: 使用 comtypes 调用 PowerPoint 应用程序导出
        #   - 跨平台: 调用 LibreOffice --headless --convert-to png

        return text_blocks, image_paths

    # ============================================================
    # 图片解析
    # ============================================================
    def _parse_image(self, file_path: str, material_id: str
                     ) -> tuple[List[Dict], List[str]]:
        """
        处理用户上传的图片文件
        图片本身不需要提取文本（由 Qwen-VL 的视觉能力直接理解），
        所以这里只保留图片路径，不做 OCR。
        Args:
            file_path: 图片文件路径
            material_id: 材料ID
        Returns:
            (text_blocks, image_paths) 元组
            - text_blocks: 空列表（图片没有可提取的文本）
            - image_paths: 包含该图片的绝对路径
        """
        # 将图片复制到处理目录
        img_dir = os.path.join(self.processed_dir, f"{material_id}_images")
        ensure_dir(img_dir)

        ext = os.path.splitext(file_path)[1]
        dest_path = os.path.join(img_dir, f"uploaded_image{ext}")
        shutil.copy2(file_path, dest_path)

        # 验证图片是否有效
        try:
            with Image.open(dest_path) as img:
                print(f"[图片信息] 尺寸={img.size}, 格式={img.format}")

            # 如果是超大图片，提示用户
            if img.width > 4000 or img.height > 4000:
                print("[提示] 图片尺寸较大，可能影响API调用速度，建议压缩后上传")

        except Exception as e:
            print(f"[错误] 图片文件无效: {e}")
            return [], []

        # 图片没有文本，返回空text_blocks
        # 图像理解由 Qwen-VL 在后续步骤中完成
        return [], [dest_path]


# ============================================================
# 简单测试入口（直接运行此文件时执行）
# ============================================================
if __name__ == "__main__":
    import sys

    processor = MaterialProcessor(
        raw_dir="../../data/raw",
        processed_dir="../../data/processed",
    )

    if len(sys.argv) > 1:
        test_file = sys.argv[1]
    else:
        print("用法: python processor.py <文件路径>")
        print("示例: python processor.py ../examples/sample.pdf")
        sys.exit(1)

    result = processor.process(test_file)
    print("\n===== 处理结果 =====")
    print(f"材料ID: {result['material_id']}")
    print(f"标题: {result['title']}")
    print(f"文本块数量: {len(result['text_blocks'])}")
    print(f"图片数量: {len(result['image_paths'])}")
    for block in result["text_blocks"]:
        print(f"  - 第{block['page']}页: {block['text'][:80]}...")
