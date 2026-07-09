"""
qwen_engine.py - Qwen-VL 模型调用封装

本模块负责课程项目中的“任务3”：把输入处理模块产出的 material_data
转换为多模态大模型请求，并稳定返回前端需要的三类结果：
  1. generate_summary() - 知识点总结
  2. answer_question()  - 学生问答
  3. generate_quiz()    - 练习题生成

如果没有配置 DASHSCOPE_API_KEY，模块会自动进入 Mock 模式，返回基于
材料内容生成的假数据，便于离线开发、前端联调和 Demo 兜底展示。
"""

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional


MODEL_NAME = "qwen-vl-plus"
MAX_TEXT_CHARS = 8000
MAX_IMAGE_COUNT = 6

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)


PROMPT_SUMMARY = """你是一位专业、严谨的教学助手。请根据给定的教学材料生成知识点总结。

要求：
1. 只基于材料中的文字和图片信息，不要编造材料中没有的内容。
2. 先给出一段 250-500 字的中文总结。
3. 再提炼 3-5 个关键要点，每个要点一句话。
4. 语言要适合 K12 或大学课程学习者理解。

请严格输出 JSON，不要输出 Markdown 解释：
{
  "summary": "知识点总结正文",
  "key_points": ["关键要点1", "关键要点2", "关键要点3"]
}
"""


PROMPT_ANSWER = """你是一位专业、严谨的教学助手。请根据给定的教学材料回答学生问题。

学生问题：
{question}

要求：
1. 回答必须基于教学材料，不要编造信息。
2. 如果材料中没有相关信息，请明确说明：“根据所提供的教学材料，未找到与该问题直接相关的信息。”
3. 回答要清晰、有条理，必要时可以分点说明。
4. 语言要适合学生理解。

请直接输出回答文本，不需要 JSON。
"""


PROMPT_QUIZ = """你是一位专业、严谨的教学助手。请根据给定的教学材料生成 {num} 道单项选择题。

要求：
1. 每题 4 个选项，格式为 A/B/C/D，且只有一个正确答案。
2. 题目必须来自材料中的主要知识点。
3. 干扰项要有一定迷惑性，但不能明显荒谬。
4. 每题都要给出答案和简短解析。

请严格输出 JSON，不要输出 Markdown 解释：
{
  "questions": [
    {
      "type": "single_choice",
      "question": "题目内容？",
      "options": ["A. 选项内容", "B. 选项内容", "C. 选项内容", "D. 选项内容"],
      "answer": "A",
      "explanation": "解析内容"
    }
  ]
}
"""


class QwenEngine:
    """Qwen-VL 教学辅助引擎。"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = MODEL_NAME,
        use_mock: Optional[bool] = None,
    ):
        """
        Args:
            api_key: DashScope API Key。不传时从 DASHSCOPE_API_KEY 读取。
            model_name: DashScope 多模态模型名称。
            use_mock: True 强制使用假数据；False 强制尝试真实 API；
                None 时根据 API Key 和依赖自动判断。
        """
        self.model_name = model_name
        self.api_key = api_key if api_key is not None else os.environ.get(
            "DASHSCOPE_API_KEY", ""
        )
        self.dashscope_available = False

        if use_mock is True:
            self.use_mock = True
            return

        if not self.api_key:
            self.use_mock = True
            self._print_mock_notice("未检测到 DASHSCOPE_API_KEY")
            return

        try:
            import dashscope  # noqa: F401

            self.dashscope_available = True
            self.use_mock = False
        except ImportError:
            self.use_mock = True if use_mock is None else False
            self._print_mock_notice("未安装 dashscope，已切换为 Mock 模式")

    # ========================================================
    # Public API used by app/main.py
    # ========================================================

    def generate_summary(self, material_data: Dict[str, Any]) -> Dict[str, Any]:
        """根据教学材料生成知识点总结。"""
        material_data = self._normalize_material(material_data)
        print("\n[模型调用] 正在生成知识点总结...")

        if self.use_mock:
            return self._mock_summary(material_data)

        try:
            messages = self._build_messages(material_data, PROMPT_SUMMARY)
            raw_response = self._call_api(messages)
            parsed = self._parse_json_response(raw_response)
            return self._normalize_summary(parsed, material_data)
        except Exception as exc:
            return {
                "material_id": material_data["material_id"],
                "summary": "",
                "key_points": [],
                "error": f"知识点总结生成失败：{exc}",
            }

    def answer_question(
        self, material_data: Dict[str, Any], question: str
    ) -> Dict[str, Any]:
        """基于教学材料回答学生问题。"""
        material_data = self._normalize_material(material_data)
        question = (question or "").strip()
        print(f"\n[模型调用] 正在回答问题: {question[:50]}...")

        if not question:
            return {
                "material_id": material_data["material_id"],
                "question": question,
                "answer": "请输入需要回答的问题。",
            }

        if self.use_mock:
            return self._mock_answer(material_data, question)

        try:
            prompt = PROMPT_ANSWER.format(question=question)
            messages = self._build_messages(material_data, prompt)
            answer = self._call_api(messages).strip()
            return {
                "material_id": material_data["material_id"],
                "question": question,
                "answer": answer or "模型未返回有效回答。",
            }
        except Exception as exc:
            return {
                "material_id": material_data["material_id"],
                "question": question,
                "answer": f"模型调用失败：{exc}",
                "error": str(exc),
            }

    def generate_quiz(
        self, material_data: Dict[str, Any], num_questions: int = 5
    ) -> Dict[str, Any]:
        """根据教学材料生成单项选择题。"""
        material_data = self._normalize_material(material_data)
        num_questions = self._clamp_question_count(num_questions)
        print(f"\n[模型调用] 正在生成 {num_questions} 道练习题...")

        if self.use_mock:
            return self._mock_quiz(material_data, num_questions)

        try:
            prompt = PROMPT_QUIZ.replace("{num}", str(num_questions))
            messages = self._build_messages(material_data, prompt)
            raw_response = self._call_api(messages)
            parsed = self._parse_json_response(raw_response)
            return self._normalize_quiz(parsed, material_data, num_questions)
        except Exception as exc:
            return {
                "material_id": material_data["material_id"],
                "questions": [],
                "error": f"练习题生成失败：{exc}",
            }

    # ========================================================
    # Request construction and API calling
    # ========================================================

    def _build_messages(
        self, material_data: Dict[str, Any], prompt: str
    ) -> List[Dict[str, Any]]:
        """构建 DashScope MultiModalConversation 的 messages。"""
        material_data = self._normalize_material(material_data)
        content: List[Dict[str, str]] = []

        title = material_data.get("title", "未命名教学材料")
        text_blocks = material_data.get("text_blocks", [])
        material_text = self._format_material_text(text_blocks)

        if material_text:
            material_text = self._truncate_text(material_text, MAX_TEXT_CHARS)
            content.append(
                {
                    "text": (
                        f"教学材料标题：{title}\n\n"
                        f"以下是从材料中提取的文字内容：\n{material_text}"
                    )
                }
            )
        else:
            content.append(
                {
                    "text": (
                        f"教学材料标题：{title}\n\n"
                        "未提取到可用文字内容，请主要依据后续图片信息进行理解。"
                    )
                }
            )

        for image_path in self._valid_image_paths(material_data):
            content.append({"image": self._image_uri(image_path)})

        content.append({"text": prompt})
        return [{"role": "user", "content": content}]

    def _call_api(self, messages: List[Dict[str, Any]]) -> str:
        """调用 DashScope Qwen-VL API，并抽取文本回答。"""
        try:
            from dashscope import MultiModalConversation

            response = MultiModalConversation.call(
                model=self.model_name,
                messages=messages,
                api_key=self.api_key,
            )
        except Exception as exc:
            raise RuntimeError(f"DashScope 请求失败：{exc}") from exc

        status_code = self._get_attr(response, "status_code")
        if status_code != 200:
            message = self._get_attr(response, "message", "未知错误")
            raise RuntimeError(f"DashScope 返回异常：code={status_code}, message={message}")

        output = self._get_attr(response, "output")
        choices = self._get_attr(output, "choices", [])
        if not choices:
            raise RuntimeError("DashScope 未返回 choices")

        choice = choices[0]
        message = self._get_attr(choice, "message")
        content = self._get_attr(message, "content", [])
        if isinstance(content, str):
            return content

        if isinstance(content, list):
            texts = []
            for item in content:
                if isinstance(item, dict) and item.get("text"):
                    texts.append(str(item["text"]))
            if texts:
                return "\n".join(texts)
            return json.dumps(content, ensure_ascii=False)

        raise RuntimeError("DashScope 返回格式无法解析")

    # ========================================================
    # Parsing and normalization
    # ========================================================

    def _parse_json_response(self, raw_response: str) -> Dict[str, Any]:
        """从模型回复中解析 JSON，兼容 Markdown code fence 和前后解释文本。"""
        if not raw_response or not raw_response.strip():
            return {"error": "模型未返回有效内容"}

        candidate = self._extract_json_candidate(raw_response)
        try:
            return json.loads(candidate)
        except json.JSONDecodeError as exc:
            return {
                "error": f"模型输出不是合法 JSON：{exc}",
                "raw_output": raw_response[:1000],
            }

    def _normalize_summary(
        self, parsed: Dict[str, Any], material_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        material_id = material_data["material_id"]
        if "error" in parsed:
            parsed["material_id"] = material_id
            return parsed

        summary = str(parsed.get("summary") or parsed.get("content") or "").strip()
        key_points = parsed.get("key_points") or parsed.get("points") or []
        if isinstance(key_points, str):
            key_points = [
                item.strip(" -0123456789.、")
                for item in key_points.splitlines()
                if item.strip()
            ]
        if not isinstance(key_points, list):
            key_points = []

        return {
            "material_id": material_id,
            "summary": summary or "模型未返回总结内容。",
            "key_points": [str(point).strip() for point in key_points if str(point).strip()],
        }

    def _normalize_quiz(
        self,
        parsed: Dict[str, Any],
        material_data: Dict[str, Any],
        num_questions: int,
    ) -> Dict[str, Any]:
        material_id = material_data["material_id"]
        if "error" in parsed:
            parsed["material_id"] = material_id
            return parsed

        questions = parsed.get("questions", [])
        if not isinstance(questions, list):
            questions = []

        normalized = []
        for item in questions[:num_questions]:
            if not isinstance(item, dict):
                continue
            options = item.get("options", [])
            if not isinstance(options, list):
                options = []
            options = [str(opt).strip() for opt in options if str(opt).strip()]
            answer = str(item.get("answer", "")).strip().upper()
            answer = answer[:1] if answer else "A"
            normalized.append(
                {
                    "type": item.get("type", "single_choice"),
                    "question": str(item.get("question", "未命名题目")).strip(),
                    "options": options,
                    "answer": answer,
                    "explanation": str(item.get("explanation", "暂无解析")).strip(),
                }
            )

        return {"material_id": material_id, "questions": normalized}

    # ========================================================
    # Mock mode
    # ========================================================

    def _mock_summary(self, material_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成贴近材料内容的模拟总结。"""
        material_id = material_data["material_id"]
        title = material_data.get("title", "教学材料")
        sentences = self._material_sentences(material_data)
        images = material_data.get("image_paths", [])

        if sentences:
            preview = "；".join(sentences[:3])
            summary = (
                "【模拟数据 - 配置 DASHSCOPE_API_KEY 后将调用真实 Qwen-VL】\n\n"
                f"《{title}》主要围绕以下内容展开：{preview}。"
                "系统会把提取出的文字和图片一起交给多模态模型，用于生成更完整的教学总结。"
            )
            key_points = self._mock_key_points(sentences)
        elif images:
            summary = (
                "【模拟数据 - 配置 DASHSCOPE_API_KEY 后将调用真实 Qwen-VL】\n\n"
                f"《{title}》当前主要包含图片材料。真实模式下，Qwen-VL 会直接理解图片中的"
                "图表、公式、版面和文字信息，并据此生成知识点总结。"
            )
            key_points = [
                "识别图片中的教学内容和视觉结构",
                "提取图表、公式或课件截图中的关键信息",
                "将视觉信息转化为可阅读的学习总结",
            ]
        else:
            summary = (
                "【模拟数据 - 配置 DASHSCOPE_API_KEY 后将调用真实 Qwen-VL】\n\n"
                f"《{title}》暂未解析出文字或图片内容，请检查上传材料是否有效。"
            )
            key_points = ["等待有效教学材料输入", "完成解析后可生成总结", "可继续进行问答和出题"]

        return {
            "material_id": material_id,
            "summary": summary,
            "key_points": key_points,
        }

    def _mock_answer(self, material_data: Dict[str, Any], question: str) -> Dict[str, Any]:
        """生成基于材料片段的模拟回答。"""
        sentences = self._material_sentences(material_data)
        relevant = self._find_relevant_sentences(question, sentences)

        if relevant:
            answer = (
                "【模拟数据 - 配置 DASHSCOPE_API_KEY 后将调用真实 Qwen-VL】\n\n"
                "根据当前材料中可解析出的内容，和这个问题最相关的信息是："
                f"{'；'.join(relevant)}。\n\n"
                "真实模式下，模型会结合完整文本和图片进一步组织成更自然、准确的回答。"
            )
        elif material_data.get("image_paths"):
            answer = (
                "【模拟数据 - 配置 DASHSCOPE_API_KEY 后将调用真实 Qwen-VL】\n\n"
                "当前材料主要是图片或截图，离线 Mock 模式无法真正理解图片内容。"
                "真实模式下，Qwen-VL 会读取图片后回答该问题。"
            )
        else:
            answer = (
                "【模拟数据 - 配置 DASHSCOPE_API_KEY 后将调用真实 Qwen-VL】\n\n"
                "根据当前解析结果，暂未找到可用于回答该问题的材料内容。"
            )

        return {
            "material_id": material_data["material_id"],
            "question": question,
            "answer": answer,
        }

    def _mock_quiz(self, material_data: Dict[str, Any], num: int) -> Dict[str, Any]:
        """生成结构稳定的模拟练习题。"""
        sentences = self._material_sentences(material_data)
        if not sentences:
            sentences = [
                "多模态教学辅助系统可以同时处理文字和图片材料",
                "系统能够生成知识点总结、学生问答和练习题",
                "真实模式下会调用 Qwen-VL 完成视觉语言联合理解",
            ]

        questions = []
        for index in range(num):
            fact = sentences[index % len(sentences)]
            questions.append(
                {
                    "type": "single_choice",
                    "question": f"【模拟题目{index + 1}】根据材料，以下哪项表述最符合内容？",
                    "options": [
                        f"A. {self._shorten(fact, 42)}",
                        "B. 材料只支持纯文本，不能使用图片信息",
                        "C. 系统不会根据教学材料生成任何输出",
                        "D. 练习题内容与上传材料完全无关",
                    ],
                    "answer": "A",
                    "explanation": (
                        "A 项来自当前解析到的材料内容。真实模式下，题目和干扰项会由"
                        "Qwen-VL 根据完整材料自动生成。"
                    ),
                }
            )

        return {"material_id": material_data["material_id"], "questions": questions}

    # ========================================================
    # Utilities
    # ========================================================

    def _normalize_material(self, material_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        material_data = material_data or {}
        text_blocks = material_data.get("text_blocks") or []
        image_paths = material_data.get("image_paths") or []
        return {
            "material_id": str(material_data.get("material_id") or "material_unknown"),
            "title": str(material_data.get("title") or "未命名教学材料"),
            "text_blocks": text_blocks if isinstance(text_blocks, list) else [],
            "image_paths": image_paths if isinstance(image_paths, list) else [],
        }

    def _format_material_text(self, text_blocks: List[Dict[str, Any]]) -> str:
        lines = []
        for block in text_blocks:
            if not isinstance(block, dict):
                continue
            text = str(block.get("text") or "").strip()
            if not text:
                continue
            page = block.get("page", "?")
            lines.append(f"--- 第{page}页 ---\n{text}")
        return "\n\n".join(lines)

    def _valid_image_paths(self, material_data: Dict[str, Any]) -> List[str]:
        valid_paths = []
        for raw_path in material_data.get("image_paths", [])[:MAX_IMAGE_COUNT]:
            resolved = self._resolve_path(str(raw_path))
            if os.path.exists(resolved):
                valid_paths.append(os.path.abspath(resolved))
        return valid_paths

    def _resolve_path(self, path: str) -> str:
        if os.path.isabs(path):
            return path
        return os.path.abspath(os.path.join(PROJECT_ROOT, path))

    def _image_uri(self, path: str) -> str:
        """Return a standards-compliant file URI for DashScope local image input."""
        return Path(path).resolve().as_uri()

    def _material_sentences(self, material_data: Dict[str, Any]) -> List[str]:
        text = self._format_material_text(material_data.get("text_blocks", []))
        text = re.sub(r"--- 第.*?页 ---", "。", text)
        parts = re.split(r"[。！？!?；;\n]+", text)
        sentences = [part.strip() for part in parts if part.strip()]
        return [self._shorten(sentence, 120) for sentence in sentences]

    def _mock_key_points(self, sentences: List[str]) -> List[str]:
        key_points = []
        for sentence in sentences:
            point = self._shorten(sentence, 60)
            if point and point not in key_points:
                key_points.append(point)
            if len(key_points) >= 5:
                break
        while len(key_points) < 3:
            key_points.append("结合材料中的文字和图片信息进行理解")
        return key_points

    def _find_relevant_sentences(self, question: str, sentences: List[str]) -> List[str]:
        if not question or not sentences:
            return sentences[:1]

        question_chars = {
            ch for ch in question if ch.strip() and ch not in "，。！？；：、,.!?;:"
        }
        scored = []
        for sentence in sentences:
            sentence_chars = set(sentence)
            score = len(question_chars & sentence_chars)
            scored.append((score, sentence))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [sentence for score, sentence in scored[:2] if score > 0]

    def _extract_json_candidate(self, raw_response: str) -> str:
        fenced = re.search(r"```(?:json)?\s*(.*?)```", raw_response, re.DOTALL)
        if fenced:
            return fenced.group(1).strip()

        start = raw_response.find("{")
        end = raw_response.rfind("}")
        if start != -1 and end != -1 and end > start:
            return raw_response[start : end + 1].strip()

        return raw_response.strip()

    def _truncate_text(self, text: str, max_chars: int) -> str:
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + "\n\n...（材料内容较长，已截断用于模型输入）"

    def _shorten(self, text: str, max_chars: int) -> str:
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) <= max_chars:
            return text
        return text[: max_chars - 1] + "…"

    def _clamp_question_count(self, num_questions: Any) -> int:
        try:
            count = int(num_questions)
        except (TypeError, ValueError):
            count = 5
        return max(1, min(count, 10))

    def _get_attr(self, obj: Any, key: str, default: Any = None) -> Any:
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)

    def _print_mock_notice(self, reason: str) -> None:
        print("=" * 60)
        print(f"提示：{reason}")
        print("模型模块将使用 Mock 模式，适合离线联调和界面演示。")
        print("如需真实调用，请安装 dashscope 并设置 DASHSCOPE_API_KEY。")
        print("=" * 60)


if __name__ == "__main__":
    test_material = {
        "material_id": "test_001",
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

    engine = QwenEngine(use_mock=True)
    print(json.dumps(engine.generate_summary(test_material), ensure_ascii=False, indent=2))
    print(json.dumps(engine.answer_question(test_material, "光合作用分为哪两个阶段？"), ensure_ascii=False, indent=2))
    print(json.dumps(engine.generate_quiz(test_material, 3), ensure_ascii=False, indent=2))
