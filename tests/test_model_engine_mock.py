import unittest

from modules.model_engine.qwen_engine import QwenEngine


class TestQwenEngineMock(unittest.TestCase):
    def setUp(self):
        self.engine = QwenEngine(use_mock=True)
        self.material = {
            "material_id": "material_test_001",
            "title": "光合作用原理",
            "text_blocks": [
                {
                    "page": 1,
                    "text": (
                        "光合作用是植物利用光能将二氧化碳和水转化为有机物和氧气的过程。"
                        "光合作用发生在叶绿体中，分为光反应和暗反应两个阶段。"
                    ),
                },
                {
                    "page": 2,
                    "text": (
                        "光反应在类囊体膜上进行，将光能转化为 ATP 和 NADPH。"
                        "暗反应在叶绿体基质中进行，利用 ATP 和 NADPH 将 CO2 固定为糖类。"
                    ),
                },
            ],
            "image_paths": [],
        }

    def test_generate_summary_returns_frontend_schema(self):
        result = self.engine.generate_summary(self.material)

        self.assertEqual(result["material_id"], "material_test_001")
        self.assertIsInstance(result["summary"], str)
        self.assertIn("光合作用", result["summary"])
        self.assertIsInstance(result["key_points"], list)
        self.assertGreaterEqual(len(result["key_points"]), 3)

    def test_answer_question_returns_frontend_schema(self):
        result = self.engine.answer_question(self.material, "光合作用分为哪两个阶段？")

        self.assertEqual(result["material_id"], "material_test_001")
        self.assertEqual(result["question"], "光合作用分为哪两个阶段？")
        self.assertIsInstance(result["answer"], str)
        self.assertIn("光反应", result["answer"])

    def test_generate_quiz_returns_requested_count(self):
        result = self.engine.generate_quiz(self.material, num_questions=3)

        self.assertEqual(result["material_id"], "material_test_001")
        self.assertEqual(len(result["questions"]), 3)
        for question in result["questions"]:
            self.assertEqual(question["type"], "single_choice")
            self.assertEqual(len(question["options"]), 4)
            self.assertIn(question["answer"], ["A", "B", "C", "D"])
            self.assertTrue(question["explanation"])

    def test_parse_json_response_accepts_markdown_wrapped_json(self):
        raw = """
        下面是结果：
        ```json
        {"summary": "测试总结", "key_points": ["A", "B", "C"]}
        ```
        """
        parsed = self.engine._parse_json_response(raw)

        self.assertEqual(parsed["summary"], "测试总结")
        self.assertEqual(parsed["key_points"], ["A", "B", "C"])


if __name__ == "__main__":
    unittest.main()
