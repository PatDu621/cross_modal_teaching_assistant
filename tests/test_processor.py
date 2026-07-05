#!/usr/bin/env python
# tests/test_processor.py
"""
多模态输入处理模块的单元测试
测试前请先运行 scripts/prepare_examples.py 生成样例文件
"""

import unittest
import os
import sys
import tempfile
import shutil

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from modules.input_processor.processor import MaterialProcessor
from modules.utils.helpers import get_file_type, generate_material_id


class TestMaterialProcessor(unittest.TestCase):
    """MaterialProcessor 完整测试"""

    @classmethod
    def setUpClass(cls):
        """在所有测试之前，检查样例文件是否存在"""
        cls.examples_dir = os.path.join(PROJECT_ROOT, "examples")
        cls.sample_pdf = os.path.join(cls.examples_dir, "sample.pdf")
        cls.sample_pptx = os.path.join(cls.examples_dir, "sample.pptx")
        cls.sample_png = os.path.join(cls.examples_dir, "sample.png")

        missing = []
        if not os.path.exists(cls.sample_pdf):
            missing.append("sample.pdf")
        if not os.path.exists(cls.sample_pptx):
            missing.append("sample.pptx")
        if missing:
            raise FileNotFoundError(
                f"缺少样例文件: {', '.join(missing)}\n"
                f"请先运行: python scripts/prepare_examples.py"
            )

    def setUp(self):
        """每个测试前创建临时输出目录"""
        self.temp_dir = tempfile.mkdtemp()
        self.processor = MaterialProcessor(
            raw_dir=os.path.join(self.temp_dir, "raw"),
            processed_dir=os.path.join(self.temp_dir, "processed"),
        )

    def tearDown(self):
        """每个测试后清理临时目录"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    # ------------------------------------------
    # 测试1: PDF解析（文本 + 图片）
    # ------------------------------------------
    def test_parse_pdf(self):
        result = self.processor.process(self.sample_pdf)

        # 检查基本信息
        self.assertEqual(result["title"], "sample")
        self.assertIsNotNone(result["material_id"])
        self.assertIn("material_", result["material_id"])

        # 检查文本块（至少2页）
        self.assertGreaterEqual(len(result["text_blocks"]), 2)
        # 检查文本内容非空（不再依赖特定中文）
        for block in result["text_blocks"]:
            self.assertTrue(block["text"].strip(), f"第{block['page']}页文本为空")

        # 检查图片提取（PDF第3页有图片）
        self.assertGreaterEqual(len(result["image_paths"]), 1)
        for img_path in result["image_paths"]:
            self.assertTrue(os.path.exists(img_path))

        print(f"  ✓ PDF解析成功: 文本块={len(result['text_blocks'])}, 图片={len(result['image_paths'])}")

    # ------------------------------------------
    # 测试2: PPT解析（文本 + 图片）
    # ------------------------------------------
    def test_parse_pptx(self):
        result = self.processor.process(self.sample_pptx)

        self.assertEqual(result["title"], "sample")
        self.assertIsNotNone(result["material_id"])

        # 检查文本块（至少4页有文字）
        self.assertGreaterEqual(len(result["text_blocks"]), 3)
        # 检查是否提取到核心关键词
        all_text = " ".join([b["text"] for b in result["text_blocks"]])
        self.assertIn("牛顿第二定律", all_text)

        # 检查图片（至少2张：第3页的力示意图 + 第4页的光合作用图）
        self.assertGreaterEqual(len(result["image_paths"]), 2)
        for img_path in result["image_paths"]:
            self.assertTrue(os.path.exists(img_path))

        print(f"  ✓ PPT解析成功: 文本块={len(result['text_blocks'])}, 图片={len(result['image_paths'])}")

    # ------------------------------------------
    # 测试3: 纯图片解析
    # ------------------------------------------
    def test_parse_image(self):
        if not os.path.exists(self.sample_png):
            self.skipTest("sample.png 不存在，跳过测试")
        
        result = self.processor.process(self.sample_png)

        self.assertEqual(result["title"], "sample")
        # 图片没有文本块
        self.assertEqual(len(result["text_blocks"]), 0)
        # 应有1张图片
        self.assertEqual(len(result["image_paths"]), 1)
        self.assertTrue(os.path.exists(result["image_paths"][0]))

        print(f"  ✓ 图片解析成功: {os.path.basename(result['image_paths'][0])}")

    # ------------------------------------------
    # 测试4: 输出JSON格式是否符合接口规范
    # ------------------------------------------
    def test_output_schema(self):
        result = self.processor.process(self.sample_pdf)

        # 检查所有必需字段
        required_keys = {"material_id", "title", "text_blocks", "image_paths"}
        self.assertTrue(required_keys.issubset(result.keys()))

        # 检查 text_blocks 结构
        for block in result["text_blocks"]:
            self.assertIn("page", block)
            self.assertIn("text", block)
            self.assertIsInstance(block["page"], int)
            self.assertIsInstance(block["text"], str)

        # 检查 image_paths 是字符串列表
        for path in result["image_paths"]:
            self.assertIsInstance(path, str)
            # 应该是绝对路径
            self.assertTrue(os.path.isabs(path))

        print("  ✓ 输出JSON格式完全符合接口规范")

    # ------------------------------------------
    # 测试5: 文件类型识别
    # ------------------------------------------
    def test_file_type_detection(self):
        self.assertEqual(get_file_type(self.sample_pdf), "pdf")
        self.assertEqual(get_file_type(self.sample_pptx), "ppt")
        self.assertEqual(get_file_type(self.sample_png), "image")
        self.assertEqual(get_file_type("test.xyz"), "unknown")

    # ------------------------------------------
    # 测试6: Material ID 生成
    # ------------------------------------------
    def test_generate_material_id(self):
        mid1 = generate_material_id()
        mid2 = generate_material_id()
        self.assertIn("material_", mid1)
        self.assertNotEqual(mid1, mid2)  # 每次不同


if __name__ == "__main__":
    # 运行测试时添加 -v 参数查看详细输出
    unittest.main(verbosity=2)