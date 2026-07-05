"""
qwen_engine.py - Qwen-VL 模型调用封装
基于阿里云 DashScope API，封装三个教学辅助功能：
  1. generate_summary()   - 知识点总结
  2. answer_question()    - 学生问答
  3. generate_quiz()      - 练习题生成

模型: qwen-vl-plus (支持文本+图像多模态输入)
API文档: https://help.aliyun.com/zh/dashscope/developer-reference/qwen-vl-api

使用前请设置环境变量: export DASHSCOPE_API_KEY="your-api-key"
"""

import os
import json
import re
from typing import List, Dict, Any, Optional


# ============================================================
# 常量配置
# ============================================================
MODEL_NAME = "qwen-vl-plus"  # 使用性价比最高的版本

# 提示词模板
PROMPT_SUMMARY = """你是一位专业的教学助手。请仔细分析以下教学材料，生成一份清晰的知识点总结。

要求：
1. 提炼材料的核心知识点，用简洁的语言组织
2. 列出 3-5 个关键要点
3. 总结长度控制在300-500字

请严格按照以下JSON格式输出，不要输出其他内容：
```json
{
  "summary": "知识点总结的完整内容...",
  "key_points": ["要点1", "要点2", "要点3"]
}
```"""

PROMPT_ANSWER = """你是一位专业的教学助手。请根据以下教学材料，准确回答学生提出的问题。

教学材料已在前面提供。学生的问题是：

"{question}"

要求：
1. 回答必须基于教学材料的内容，不要编造信息
2. 如果材料中没有相关信息，请如实说明："根据所提供的教学材料，未找到与您问题直接相关的信息。"
3. 回答要清晰、有条理，适合学生理解
4. 如果适用，可以适当举例说明

请直接输出你的回答，不需要JSON格式。"""

PROMPT_QUIZ = """你是一位专业的教学助手。请根据以下教学材料，生成 {num} 道单项选择题，用于检验学生对该材料的掌握程度。

要求：
1. 每题4个选项（A/B/C/D），只有一个正确答案
2. 题目应覆盖材料的主要知识点，难度适中
3. 每道题需要包含正确答案的详细解析
4. 选项要有区分度（干扰项要有一定迷惑性但不是完全无关）

请严格按照以下JSON格式输出，不要输出其他内容：
```json
{
  "questions": [
    {
      "type": "single_choice",
      "question": "题目内容？",
      "options": ["A. 选项内容", "B. 选项内容", "C. 选项内容", "D. 选项内容"],
      "answer": "A",
      "explanation": "这道题的解析，说明为什么选这个答案"
    }
  ]
}
```"""


class QwenEngine:
    """
    Qwen-VL 模型调用引擎
    封装 DashScope API 调用，提供教学辅助功能
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化引擎
        Args:
            api_key: DashScope API Key。如果为None，从环境变量读取
        """
        # 优先使用传入的key，否则从环境变量读取
        self.api_key = api_key or os.environ.get("DASHSCOPE_API_KEY", "")

        if not self.api_key:
            print("=" * 60)
            print("⚠️  警告: 未设置 DASHSCOPE_API_KEY 环境变量")
            print("   模型调用将返回 MOCK 数据，仅供测试界面使用")
            print("   请通过以下方式设置真实的 API Key:")
            print("   - Windows: set DASHSCOPE_API_KEY=your-key-here")
            print("   - Linux/Mac: export DASHSCOPE_API_KEY=your-key-here")
            print("   获取 Key: https://dashscope.console.aliyun.com/")
            print("=" * 60)
            self.use_mock = True
        else:
            self.use_mock = False
            # 验证 dashscope 是否已安装
            try:
                import dashscope
                self.dashscope = dashscope
            except ImportError:
                print("[错误] 未安装 dashscope，请运行: pip install dashscope")
                self.use_mock = True

    # ========================================================
    # 公开方法
    # ========================================================

    def generate_summary(self, material_data: Dict[str, Any]
                         ) -> Dict[str, Any]:
        """
        根据教学材料生成知识点总结
        Args:
            material_data: 材料数据（processor输出的格式）
        Returns:
            {"material_id": "...", "summary": "...", "key_points": [...]}
        """
        print("\n[模型调用] 正在生成知识点总结...")

        if self.use_mock:
            return self._mock_summary(material_data)

        # 构建消息
        messages = self._build_messages(material_data, PROMPT_SUMMARY)
        # 调用API
        raw_response = self._call_api(messages)
        # 解析JSON输出
        result = self._parse_json_response(raw_response)

        result["material_id"] = material_data.get("material_id", "")
        return result

    def answer_question(self, material_data: Dict[str, Any],
                        question: str) -> Dict[str, Any]:
        """
        基于教学材料回答学生问题
        Args:
            material_data: 材料数据
            question: 学生提出的问题
        Returns:
            {"material_id": "...", "question": "...", "answer": "..."}
        """
        print(f"\n[模型调用] 正在回答问题: {question[:50]}...")

        if self.use_mock:
            return self._mock_answer(material_data, question)

        # 将问题填入提示词模板
        prompt = PROMPT_ANSWER.format(question=question)
        messages = self._build_messages(material_data, prompt)
        raw_response = self._call_api(messages)

        return {
            "material_id": material_data.get("material_id", ""),
            "question": question,
            "answer": raw_response.strip(),
        }

    def generate_quiz(self, material_data: Dict[str, Any],
                      num_questions: int = 5) -> Dict[str, Any]:
        """
        根据教学材料生成练习题
        Args:
            material_data: 材料数据
            num_questions: 生成的题目数量（默认5道）
        Returns:
            {"material_id": "...", "questions": [...]}
        """
        print(f"\n[模型调用] 正在生成{num_questions}道练习题...")

        if self.use_mock:
            return self._mock_quiz(material_data, num_questions)

        prompt = PROMPT_QUIZ.format(num=num_questions)
        messages = self._build_messages(material_data, prompt)
        raw_response = self._call_api(messages)
        result = self._parse_json_response(raw_response)

        result["material_id"] = material_data.get("material_id", "")
        return result

    # ========================================================
    # 内部方法
    # ========================================================

    def _build_messages(self, material_data: Dict[str, Any],
                        prompt: str) -> List[Dict]:
        """
        构建发送给 Qwen-VL 的消息体
        将材料中的文本和图像一起打包，让模型获得完整的上下文

        Args:
            material_data: 材料数据
            prompt: 提示词文本
        Returns:
            DashScope 格式的消息列表
        """
        content = []

        # 1. 添加文本内容（材料提取的文字）
        text_blocks = material_data.get("text_blocks", [])
        if text_blocks:
            material_text = self._format_material_text(text_blocks)
            content.append({
                "text": f"以下是教学材料的内容：\n\n{material_text}"
            })
        else:
            content.append({
                "text": "（教学材料中未提取到文字内容，请主要依据图片信息）"
            })

        # 2. 添加图像内容（材料中的图片 + 用户上传的截图）
        image_paths = material_data.get("image_paths", [])
        for img_path in image_paths:
            if os.path.exists(img_path):
                # DashScope 支持 file:// 协议加载本地图片
                content.append({
                    "image": f"file://{os.path.abspath(img_path)}"
                })

        # 3. 添加提示词
        content.append({"text": prompt})

        # 4. 组装消息
        messages = [{"role": "user", "content": content}]
        return messages

    def _format_material_text(self, text_blocks: List[Dict]) -> str:
        """
        将材料文本格式化为易读的字符串
        Args:
            text_blocks: [{"page": 1, "text": "..."}, ...]
        Returns:
            格式化后的文本字符串
        """
        lines = []
        for block in text_blocks:
            page = block.get("page", "?")
            text = block.get("text", "")
            lines.append(f"--- 第{page}页 ---\n{text}")
        return "\n\n".join(lines)

    def _call_api(self, messages: List[Dict]) -> str:
        """
        调用 DashScope MultiModalConversation API
        Args:
            messages: 消息列表
        Returns:
            模型返回的文本内容
        Raises:
            RuntimeError: API调用失败时抛出
        """
        try:
            from dashscope import MultiModalConversation

            response = MultiModalConversation.call(
                model=MODEL_NAME,
                messages=messages,
                api_key=self.api_key,
            )

            # 检查响应状态
            if response.status_code == 200:
                # 提取文本内容
                output = response.output
                if output and output.choices:
                    choice = output.choices[0]
                    if choice.message and choice.message.content:
                        # content 是一个列表，取第一段的text
                        for item in choice.message.content:
                            if "text" in item:
                                return item["text"]
                        # 如果content里没有text（纯图片回复等极端情况）
                        return str(choice.message.content)

                print(f"[警告] API返回格式异常: {response.output}")
                return ""

            else:
                error_msg = f"API调用失败: code={response.status_code}, message={response.message}"
                print(f"[错误] {error_msg}")
                raise RuntimeError(error_msg)

        except ImportError:
            print("[错误] dashscope库未安装，请运行: pip install dashscope")
            raise
        except Exception as e:
            print(f"[错误] API调用异常: {e}")
            raise RuntimeError(f"Qwen-VL API调用失败: {e}")

    def _parse_json_response(self, raw_response: str) -> Dict[str, Any]:
        """
        从模型回复中解析JSON
        模型有时会在JSON外层包裹 ```json ... ``` 标记，需要处理

        Args:
            raw_response: 模型的原始文本回复
        Returns:
            解析后的字典。解析失败时返回带error字段的字典
        """
        if not raw_response:
            return {"error": "模型未返回有效内容"}

        # 尝试提取被 ```json ``` 包裹的JSON
        json_match = re.search(
            r'```(?:json)?\s*\n?(.*?)\n?```',
            raw_response, re.DOTALL
        )

        if json_match:
            json_str = json_match.group(1).strip()
        else:
            # 尝试将整个回复当作JSON解析
            json_str = raw_response.strip()

        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"[警告] JSON解析失败: {e}")
            print(f"[调试] 原始回复前500字: {raw_response[:500]}")
            # 返回一个包含原始文本的降级结果
            return {
                "error": f"模型输出格式异常，未能解析为JSON",
                "raw_output": raw_response[:1000],
            }

    # ========================================================
    # Mock 数据（API不可用时的降级方案）
    # ========================================================
    # 注意：以下所有 mock_ 方法仅在未设置 DASHSCOPE_API_KEY 时使用
    # 目的是让Demo在没有API的情况下也能展示界面功能

    def _mock_summary(self, material_data: Dict) -> Dict[str, Any]:
        """生成模拟的知识点总结"""
        title = material_data.get("title", "教学材料")
        return {
            "material_id": material_data.get("material_id", ""),
            "summary": (
                f"【模拟数据 - 请配置API Key获取真实结果】\n\n"
                f"根据《{title}》的内容分析，该教学材料涵盖了以下核心领域：\n\n"
                f"1. 基础概念与定义：材料首先介绍了相关领域的基本概念，"
                f"帮助学生建立对新知识的初步理解。\n\n"
                f"2. 核心原理与机制：深入讲解了关键原理的工作机制，"
                f"通过实例说明了抽象概念在实际中的应用。\n\n"
                f"3. 应用与实践：展示了如何将理论知识应用到实际问题中，"
                f"培养学生的分析能力和解决问题的能力。\n\n"
                f"（以上为模拟内容，配置 DashScope API Key 后将生成基于实际材料的个性化总结）"
            ),
            "key_points": [
                "掌握课程核心概念的定义和内涵（模拟）",
                "理解关键原理的工作机制和应用场景（模拟）",
                "能够运用所学知识解决实际问题（模拟）",
            ],
        }

    def _mock_answer(self, material_data: Dict, question: str) -> Dict[str, Any]:
        """生成模拟的问题回答"""
        return {
            "material_id": material_data.get("material_id", ""),
            "question": question,
            "answer": (
                f"【模拟数据 - 请配置API Key获取真实结果】\n\n"
                f"关于您的问题“{question}”，根据教学材料的内容：\n\n"
                f"这是一个很好的问题。在实际部署版本中，Qwen-VL模型会基于"
                f"教学材料的文本和图像内容，针对您的具体问题生成准确的回答。"
                f"当前为离线Demo模式，展示的是占位回答。\n\n"
                f"请设置环境变量 DASHSCOPE_API_KEY 后重启应用以启用AI问答功能。"
            ),
        }

    def _mock_quiz(self, material_data: Dict, num: int) -> Dict[str, Any]:
        """生成模拟的练习题"""
        mock_questions = []
        for i in range(1, min(num, 5) + 1):
            mock_questions.append({
                "type": "single_choice",
                "question": f"【模拟题目{i}】根据教学材料，以下哪个选项是正确的？（请配置API Key获取真实题目）",
                "options": [
                    "A. 模拟选项一（这是正确答案的占位）",
                    "B. 模拟选项二（这是一个干扰项）",
                    "C. 模拟选项三（这是另一个干扰项）",
                    "D. 模拟选项四（这也是一个干扰项）",
                ],
                "answer": "A",
                "explanation": f"【模拟解析】在实际版本中，这里会显示对正确答案的详细解析，帮助学生理解为什么选A而不是其他选项。",
            })

        return {
            "material_id": material_data.get("material_id", ""),
            "questions": mock_questions,
        }


# ============================================================
# 简单测试入口
# ============================================================
if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

    # 测试：使用模拟材料数据
    test_material = {
        "material_id": "test_001",
        "title": "光合作用原理",
        "text_blocks": [
            {
                "page": 1,
                "text": "光合作用是植物利用光能将二氧化碳和水转化为有机物和氧气的过程。"
                       "光合作用发生在叶绿体中，分为光反应和暗反应两个阶段。"
            },
            {
                "page": 2,
                "text": "光反应在类囊体膜上进行，将光能转化为ATP和NADPH。"
                       "暗反应在叶绿体基质中进行，利用ATP和NADPH将CO2固定为糖类。"
            },
        ],
        "image_paths": [],
    }

    engine = QwenEngine()

    print("\n" + "=" * 60)
    print("测试1: 生成知识点总结")
    print("=" * 60)
    summary = engine.generate_summary(test_material)
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    print("\n" + "=" * 60)
    print("测试2: 回答问题")
    print("=" * 60)
    answer = engine.answer_question(test_material, "光合作用分为哪两个阶段？")
    print(json.dumps(answer, ensure_ascii=False, indent=2))

    print("\n" + "=" * 60)
    print("测试3: 生成练习题")
    print("=" * 60)
    quiz = engine.generate_quiz(test_material, num_questions=3)
    print(json.dumps(quiz, ensure_ascii=False, indent=2))
