"""
main.py - 跨模态教学辅助系统前端入口

启动方式:
    cd cross_modal_teaching_assistant
    python app/main.py
"""

import json
import os
import shutil
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

# Gradio 启动时会访问 127.0.0.1 做健康检查。部分 Windows/代理环境会把
# localhost 请求转发到代理，导致 startup-events 返回 502，这里强制绕过代理。
LOCALHOST_BYPASS = "127.0.0.1,localhost,::1"
for proxy_key in ("NO_PROXY", "no_proxy"):
    current_value = os.environ.get(proxy_key, "")
    entries = [item.strip() for item in current_value.split(",") if item.strip()]
    for local_host in LOCALHOST_BYPASS.split(","):
        if local_host not in entries:
            entries.append(local_host)
    os.environ[proxy_key] = ",".join(entries)


def _patch_huggingface_hub_for_gradio() -> None:
    """兼容新版 huggingface_hub 移除 HfFolder 后的旧版 Gradio 导入。"""
    try:
        import huggingface_hub
    except Exception:
        return

    if hasattr(huggingface_hub, "HfFolder"):
        return

    class HfFolderCompat:
        @staticmethod
        def get_token():
            get_token = getattr(huggingface_hub, "get_token", None)
            return get_token() if callable(get_token) else None

        @staticmethod
        def save_token(token):
            login = getattr(huggingface_hub, "login", None)
            if callable(login):
                return login(token=token, add_to_git_credential=False)
            return None

        @staticmethod
        def delete_token():
            logout = getattr(huggingface_hub, "logout", None)
            if callable(logout):
                return logout()
            return None

    huggingface_hub.HfFolder = HfFolderCompat


def _check_gradio_runtime_dependencies() -> None:
    """提前检查 Gradio 会导入的 pandas/numpy 二进制依赖是否可用。"""
    try:
        import numpy  # noqa: F401
        import pandas  # noqa: F401
    except ValueError as exc:
        if "numpy.dtype size changed" not in str(exc):
            raise
        message = (
            "\n当前 Python 环境中的 pandas 与 numpy 二进制版本不兼容。\n"
            "请在项目根目录执行以下命令后重新启动：\n\n"
            "    pip install --upgrade --force-reinstall \"numpy>=1.23,<2.0\" \"pandas>=2.0,<2.3\"\n\n"
            "如果你使用 conda，也可以执行：\n\n"
            "    conda install \"numpy<2\" \"pandas>=2.0,<2.3\"\n\n"
            f"原始错误：{exc}\n"
        )
        raise RuntimeError(message) from exc


_patch_huggingface_hub_for_gradio()
_check_gradio_runtime_dependencies()

import gradio as gr


def _patch_gradio_client_schema_parser() -> None:
    """兼容部分 gradio/gradio_client 组合无法解析 bool JSON schema 的问题。"""
    try:
        from gradio_client import utils as client_utils
    except Exception:
        return

    original = getattr(client_utils, "json_schema_to_python_type", None)
    if original is None or getattr(original, "_bool_schema_patched", False):
        return

    def patched_json_schema_to_python_type(schema):
        if isinstance(schema, bool):
            return "Any"
        try:
            return original(schema)
        except TypeError as exc:
            if "argument of type 'bool' is not iterable" not in str(exc):
                raise
            return "Any"

    patched_json_schema_to_python_type._bool_schema_patched = True
    client_utils.json_schema_to_python_type = patched_json_schema_to_python_type


_patch_gradio_client_schema_parser()


def _patch_starlette_template_response_for_gradio() -> None:
    """兼容 Gradio 4.x 与新版 Starlette 的 TemplateResponse 参数顺序差异。"""
    try:
        from starlette.templating import Jinja2Templates
    except Exception:
        return

    original = getattr(Jinja2Templates, "TemplateResponse", None)
    if original is None or getattr(original, "_gradio_compat_patched", False):
        return

    def compatible_template_response(self, *args, **kwargs):
        # Gradio 4.x 调用方式: TemplateResponse(template_name, context, ...)
        # Starlette 1.x 调用方式: TemplateResponse(request, template_name, context, ...)
        if len(args) >= 2 and isinstance(args[0], str) and isinstance(args[1], dict):
            name = args[0]
            context = args[1]
            request = context.get("request")
            if request is not None:
                return original(self, request, name, context, *args[2:], **kwargs)
        return original(self, *args, **kwargs)

    compatible_template_response._gradio_compat_patched = True
    Jinja2Templates.TemplateResponse = compatible_template_response


_patch_starlette_template_response_for_gradio()

# 将项目根目录加入 Python 路径，确保模块导入正常。
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from ui_layout import create_ui
from modules.input_processor.processor import MaterialProcessor
from modules.model_engine.qwen_engine import QwenEngine
from modules.utils.helpers import ensure_dir, save_json


# ============================================================
# 全局配置
# ============================================================
RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data", "outputs")

SUPPORTED_UPLOAD_TYPES = [
    ".pdf",
    ".pptx",
    ".ppt",
    ".png",
    ".jpg",
    ".jpeg",
    ".bmp",
    ".gif",
    ".webp",
]

for directory in (RAW_DIR, PROCESSED_DIR, OUTPUT_DIR):
    ensure_dir(directory)

processor = MaterialProcessor(raw_dir=RAW_DIR, processed_dir=PROCESSED_DIR)
engine = QwenEngine()


# ============================================================
# 前端回调
# ============================================================

def handle_file_upload(file_obj, extra_images):
    """解析用户上传的教学材料，并返回前端展示所需的全部状态。"""
    if file_obj is None:
        return (
            None,
            "*等待上传材料...*",
            [],
            _empty_material_meta(),
            "未检测到文件。请先上传 PDF、PPT 或图片材料。",
        )

    file_path = _coerce_file_path(file_obj)
    if not file_path or not os.path.exists(file_path):
        return (
            None,
            "文件路径无效，请重新上传。",
            [],
            _empty_material_meta(),
            "上传文件不可访问。",
        )

    try:
        material_data = processor.process(file_path)
        _attach_extra_images(material_data, extra_images)

        output_path = os.path.join(
            PROCESSED_DIR, f"{material_data['material_id']}.json"
        )
        save_json(material_data, output_path)

        text_display = _format_material_for_display(material_data)
        gallery_items = _gallery_items(material_data)
        meta = _format_material_meta(material_data)
        status = (
            "解析完成\n"
            f"文件：{os.path.basename(file_path)}\n"
            f"文本页数：{len(material_data.get('text_blocks', []))}\n"
            f"图片数量：{len(material_data.get('image_paths', []))}\n"
            f"材料 ID：{material_data.get('material_id')}"
        )
        return material_data, text_display, gallery_items, meta, status
    except Exception as exc:
        return (
            None,
            f"解析失败：{exc}",
            [],
            _empty_material_meta(),
            f"解析失败：{exc}",
        )


def handle_generate_summary(material_data):
    """生成知识点总结，并保存可下载结果。"""
    if material_data is None:
        return (
            "请先上传并解析教学材料。",
            "",
            None,
            None,
            "没有可导出的结果。",
        )

    try:
        result = engine.generate_summary(material_data)
        if "error" in result:
            return (
                f"生成失败：{result.get('error', '未知错误')}",
                "",
                None,
                None,
                "总结生成失败，未保存导出文件。",
            )

        summary_text = result.get("summary", "模型未返回总结内容。")
        key_points = result.get("key_points", [])
        key_points_text = _format_key_points(key_points)
        markdown = f"# 知识点总结\n\n{summary_text}\n\n{key_points_text}"
        json_path, md_path = _save_frontend_result(
            material_data, "summary", result, markdown
        )
        notice = f"已保存总结结果：{os.path.basename(md_path)}"
        return summary_text, key_points_text, json_path, md_path, notice
    except Exception as exc:
        return f"生成总结时出错：{exc}", "", None, None, "总结生成失败。"


def handle_answer_question(material_data, question):
    """回答学生问题，并保存可下载结果。"""
    if material_data is None:
        return "请先上传并解析教学材料。", None, None, "没有可导出的结果。"

    question = (question or "").strip()
    if not question:
        return "请输入你的问题。", None, None, "没有可导出的结果。"

    try:
        result = engine.answer_question(material_data, question)
        answer = result.get("answer", "未能生成回答。")
        output = f"### 问题\n{question}\n\n### 回答\n{answer}"
        json_path, md_path = _save_frontend_result(
            material_data, "answer", result, f"# 智能问答\n\n{output}"
        )
        notice = f"已保存问答结果：{os.path.basename(md_path)}"
        return output, json_path, md_path, notice
    except Exception as exc:
        return f"回答问题时出错：{exc}", None, None, "问答生成失败。"


def handle_generate_quiz(material_data, num_questions):
    """生成练习题，并保存可下载结果。"""
    if material_data is None:
        return "请先上传并解析教学材料。", None, None, "没有可导出的结果。"

    try:
        result = engine.generate_quiz(material_data, num_questions=int(num_questions))
        if "error" in result:
            return (
                f"生成失败：{result.get('error', '未知错误')}",
                None,
                None,
                "练习题生成失败，未保存导出文件。",
            )

        questions = result.get("questions", [])
        if not questions:
            return "未能生成练习题。", None, None, "没有可导出的结果。"

        output = _format_quiz_for_display(questions)
        json_path, md_path = _save_frontend_result(
            material_data, "quiz", result, f"# 练习题\n\n{output}"
        )
        notice = f"已保存练习题结果：{os.path.basename(md_path)}"
        return output, json_path, md_path, notice
    except Exception as exc:
        return f"生成练习题时出错：{exc}", None, None, "练习题生成失败。"


def clear_material():
    """清空当前材料和页面预览。"""
    return (
        None,
        "*等待上传材料...*",
        [],
        _empty_material_meta(),
        "已清空当前材料。",
    )


def clear_results():
    """清空 AI 生成结果和下载文件。"""
    return (
        "*点击按钮生成知识点总结...*",
        "",
        "*等待提问...*",
        "*点击按钮生成练习题...*",
        None,
        None,
        "已清空页面中的生成结果。",
    )


# ============================================================
# 格式化与文件工具
# ============================================================

def _coerce_file_path(file_obj) -> str:
    if isinstance(file_obj, str):
        return file_obj
    return file_obj.name if hasattr(file_obj, "name") else str(file_obj)


def _attach_extra_images(material_data: Dict[str, Any], extra_images) -> None:
    """将补充图片复制到该材料目录，保证 Gallery 和导出 JSON 路径稳定。"""
    if not extra_images:
        return

    material_id = material_data["material_id"]
    img_dir = os.path.join(PROCESSED_DIR, f"{material_id}_images")
    ensure_dir(img_dir)

    image_paths = material_data.setdefault("image_paths", [])
    for index, image_obj in enumerate(extra_images, start=1):
        source = _coerce_file_path(image_obj)
        if not source or not os.path.exists(source):
            continue
        ext = os.path.splitext(source)[1].lower() or ".png"
        dest = os.path.join(img_dir, f"extra_{index}{ext}")
        shutil.copy2(source, dest)
        abs_dest = os.path.abspath(dest)
        if abs_dest not in image_paths:
            image_paths.append(abs_dest)


def _format_material_for_display(material_data: Dict[str, Any]) -> str:
    if not material_data:
        return "无材料数据。"

    lines = [f"### {material_data.get('title', '未命名材料')}", ""]
    text_blocks = material_data.get("text_blocks", [])
    if not text_blocks:
        lines.append("*未提取到文本内容，材料可能主要由图片或扫描页组成。*")
        return "\n".join(lines)

    for block in text_blocks:
        page = block.get("page", "?")
        text = str(block.get("text", "")).strip()
        if len(text) > 1200:
            text = text[:1200] + "\n\n...（预览已截断，完整内容保存在 processed JSON 中）"
        lines.append(f"**第 {page} 页**")
        lines.append(text or "*本页无可展示文本。*")
        lines.append("")
    return "\n".join(lines)


def _gallery_items(material_data: Dict[str, Any]) -> List[Tuple[str, str]]:
    items = []
    for index, path in enumerate(material_data.get("image_paths", []), start=1):
        if os.path.exists(path):
            items.append((path, f"图片 {index}: {os.path.basename(path)}"))
    return items


def _format_material_meta(material_data: Dict[str, Any]) -> str:
    title = material_data.get("title", "未命名材料")
    material_id = material_data.get("material_id", "material_unknown")
    text_count = len(material_data.get("text_blocks", []))
    image_count = len(material_data.get("image_paths", []))
    mode = "Mock 模式" if getattr(engine, "use_mock", True) else "DashScope API 模式"
    return (
        '<div class="edu-meta-panel">'
        '<div class="edu-meta-item edu-meta-wide">'
        '<div class="edu-meta-label">材料标题</div>'
        f'<div class="edu-meta-value">{title}</div>'
        "</div>"
        '<div class="edu-meta-item edu-meta-wide">'
        '<div class="edu-meta-label">材料 ID</div>'
        f'<div class="edu-meta-value">{material_id}</div>'
        "</div>"
        '<div class="edu-meta-item">'
        '<div class="edu-meta-label">文本页数</div>'
        f'<div class="edu-meta-value">{text_count}</div>'
        "</div>"
        '<div class="edu-meta-item">'
        '<div class="edu-meta-label">图片数量</div>'
        f'<div class="edu-meta-value">{image_count}</div>'
        "</div>"
        '<div class="edu-meta-item">'
        '<div class="edu-meta-label">模型状态</div>'
        f'<div class="edu-meta-value">{mode}</div>'
        "</div>"
        "</div>"
    )


def _empty_material_meta() -> str:
    mode = "Mock 模式" if getattr(engine, "use_mock", True) else "DashScope API 模式"
    return (
        '<div class="edu-meta-panel">'
        '<div class="edu-meta-item edu-meta-wide">'
        '<div class="edu-meta-label">材料标题</div>'
        '<div class="edu-meta-value">未选择</div>'
        "</div>"
        '<div class="edu-meta-item edu-meta-wide">'
        '<div class="edu-meta-label">材料 ID</div>'
        '<div class="edu-meta-value">-</div>'
        "</div>"
        '<div class="edu-meta-item">'
        '<div class="edu-meta-label">文本页数</div>'
        '<div class="edu-meta-value">0</div>'
        "</div>"
        '<div class="edu-meta-item">'
        '<div class="edu-meta-label">图片数量</div>'
        '<div class="edu-meta-value">0</div>'
        "</div>"
        '<div class="edu-meta-item">'
        '<div class="edu-meta-label">模型状态</div>'
        f'<div class="edu-meta-value">{mode}</div>'
        "</div>"
        "</div>"
    )


def _format_key_points(key_points: List[Any]) -> str:
    if not key_points:
        return "### 关键要点\n暂无关键要点。"
    lines = ["### 关键要点"]
    for index, point in enumerate(key_points, start=1):
        lines.append(f"{index}. {point}")
    return "\n".join(lines)


def _format_quiz_for_display(questions: List[Dict[str, Any]]) -> str:
    lines = []
    for index, question in enumerate(questions, start=1):
        lines.append(f"### 第 {index} 题")
        lines.append(f"**{question.get('question', '未命名题目')}**")
        lines.append("")
        for option in question.get("options", []):
            lines.append(f"- {option}")
        lines.append("")
        lines.append("<details><summary>查看答案与解析</summary>")
        lines.append("")
        lines.append(f"**正确答案**：{question.get('answer', 'N/A')}")
        lines.append("")
        lines.append(f"**解析**：{question.get('explanation', '暂无解析')}")
        lines.append("")
        lines.append("</details>")
        lines.append("")
        lines.append("---")
        lines.append("")
    return "\n".join(lines)


def _save_frontend_result(
    material_data: Dict[str, Any],
    result_type: str,
    payload: Dict[str, Any],
    markdown: str,
) -> Tuple[str, str]:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    material_id = material_data.get("material_id", "material_unknown")
    base_name = f"{material_id}_{result_type}_{timestamp}"
    json_path = os.path.join(OUTPUT_DIR, f"{base_name}.json")
    md_path = os.path.join(OUTPUT_DIR, f"{base_name}.md")

    export_payload = {
        "material_id": material_id,
        "title": material_data.get("title", "未命名材料"),
        "result_type": result_type,
        "created_at": timestamp,
        "engine_mode": "mock" if getattr(engine, "use_mock", True) else "api",
        "result": payload,
    }
    save_json(export_payload, json_path)
    with open(md_path, "w", encoding="utf-8") as file:
        file.write(markdown.strip() + "\n")
    return json_path, md_path


def launch_ui(app_ui):
    """启动 Gradio。"""
    app_ui.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        inbrowser=True,
        show_error=True,
    )


# ============================================================
# 程序入口
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("跨模态教学辅助系统")
    print("基于 Qwen-VL 多模态大模型")
    print("=" * 60)

    if not os.environ.get("DASHSCOPE_API_KEY"):
        print("\n未检测到 DASHSCOPE_API_KEY，应用将以 Mock 模式运行。")
        print("设置后可切换为真实 DashScope API 调用。")
        print()

    model_status = (
        "Mock 模式 · 离线演示"
        if getattr(engine, "use_mock", True)
        else "DashScope API 模式"
    )
    app_ui = create_ui(
        supported_upload_types=SUPPORTED_UPLOAD_TYPES,
        initial_material_meta=_empty_material_meta(),
        model_status=model_status,
        handle_file_upload=handle_file_upload,
        handle_generate_summary=handle_generate_summary,
        handle_answer_question=handle_answer_question,
        handle_generate_quiz=handle_generate_quiz,
        clear_material=clear_material,
        clear_results=clear_results,
    )
    app_ui.queue()
    launch_ui(app_ui)
