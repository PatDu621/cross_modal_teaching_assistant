"""
main.py - 跨模态教学辅助系统 主程序入口
基于 Gradio 构建的 Web 交互界面

启动方式:
    cd cross_modal_teaching_assistant
    python app/main.py

使用前请先安装依赖:
    pip install -r requirements.txt

设置 API Key (可选，未设置时使用Mock数据):
    Windows: set DASHSCOPE_API_KEY=your-key-here
    Linux/Mac: export DASHSCOPE_API_KEY=your-key-here
"""

import os
import sys
import json
import gradio as gr
from typing import Dict, Any, Optional

# 将项目根目录加入Python路径，确保模块导入正常
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from modules.input_processor.processor import MaterialProcessor
from modules.model_engine.qwen_engine import QwenEngine
from modules.utils.helpers import ensure_dir


# ============================================================
# 全局配置
# ============================================================
RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data", "outputs")

# 确保目录存在
for d in [RAW_DIR, PROCESSED_DIR, OUTPUT_DIR]:
    ensure_dir(d)

# 初始化全局处理器和引擎
processor = MaterialProcessor(raw_dir=RAW_DIR, processed_dir=PROCESSED_DIR)
engine = QwenEngine()  # API Key 从环境变量读取


# ============================================================
# 回调函数（Gradio 事件处理）
# ============================================================

def handle_file_upload(file_obj, extra_images):
    """
    处理用户上传的文件
    Args:
        file_obj: Gradio File 组件返回的文件路径或临时文件对象
        extra_images: 用户额外上传的图片列表
    Returns:
        (状态更新, 材料文本展示, 材料图片展示, 状态信息)
    """
    if file_obj is None:
        return None, "请先上传教学材料", "", "❌ 未检测到文件"

    # Gradio 返回的可能是路径字符串或临时文件对象
    if isinstance(file_obj, str):
        file_path = file_obj
    else:
        file_path = file_obj.name if hasattr(file_obj, 'name') else str(file_obj)

    try:
        # 解析材料
        material_data = processor.process(file_path)

        # 如果用户额外上传了图片，添加到image_paths
        if extra_images:
            for img in extra_images:
                if isinstance(img, str):
                    img_path = img
                else:
                    img_path = img.name if hasattr(img, 'name') else str(img)
                if img_path not in material_data["image_paths"]:
                    material_data["image_paths"].append(img_path)

        # 格式化材料文本用于展示
        text_display = _format_material_for_display(material_data)

        # 图片信息展示
        img_display = _format_images_for_display(material_data)

        # 状态信息
        info = (
            f"✅ 解析成功！\n"
            f"📄 文件类型: {os.path.splitext(file_path)[1]}\n"
            f"📝 文本块: {len(material_data['text_blocks'])} 页\n"
            f"🖼️ 图片: {len(material_data['image_paths'])} 张\n"
            f"🆔 材料ID: {material_data['material_id']}"
        )

        return material_data, text_display, img_display, info

    except Exception as e:
        return None, f"解析失败: {str(e)}", "", f"❌ 错误: {str(e)}"


def handle_generate_summary(material_data):
    """生成知识点总结"""
    if material_data is None:
        return "⚠️ 请先上传并解析教学材料", ""

    try:
        result = engine.generate_summary(material_data)

        if "error" in result:
            return f"❌ 生成失败: {result.get('error', '未知错误')}", ""

        # 格式化输出
        summary_text = result.get("summary", "无总结内容")
        key_points = result.get("key_points", [])

        key_points_text = ""
        if key_points:
            key_points_text = "### 📌 关键要点\n"
            for i, point in enumerate(key_points, 1):
                key_points_text += f"{i}. {point}\n"

        return summary_text, key_points_text

    except Exception as e:
        return f"❌ 生成总结时出错: {str(e)}", ""


def handle_answer_question(material_data, question):
    """回答学生问题"""
    if material_data is None:
        return "⚠️ 请先上传并解析教学材料"

    if not question or not question.strip():
        return "⚠️ 请输入你的问题"

    try:
        result = engine.answer_question(material_data, question.strip())
        answer = result.get("answer", "未能生成回答")

        return f"### ❓ 你的问题\n{question}\n\n### 💡 回答\n{answer}"

    except Exception as e:
        return f"❌ 回答问题时出错: {str(e)}"


def handle_generate_quiz(material_data, num_questions):
    """生成练习题"""
    if material_data is None:
        return "⚠️ 请先上传并解析教学材料"

    try:
        result = engine.generate_quiz(material_data, num_questions=int(num_questions))

        if "error" in result:
            return f"❌ 生成失败: {result.get('error', '未知错误')}"

        questions = result.get("questions", [])

        if not questions:
            return "⚠️ 未能生成练习题"

        # 格式化练习题展示
        output = ""
        for i, q in enumerate(questions, 1):
            output += f"### 第{i}题\n"
            output += f"**{q.get('question', '未知题目')}**\n\n"
            for opt in q.get("options", []):
                output += f"- {opt}\n"
            output += f"\n<details><summary>👀 点击查看答案与解析</summary>\n\n"
            output += f"**正确答案**: {q.get('answer', 'N/A')}\n\n"
            output += f"**解析**: {q.get('explanation', '无')}\n"
            output += f"</details>\n\n"
            output += "---\n\n"

        return output

    except Exception as e:
        return f"❌ 生成练习题时出错: {str(e)}"


# ============================================================
# 辅助格式化函数
# ============================================================

def _format_material_for_display(material_data: Dict) -> str:
    """将材料数据格式化为展示用的Markdown文本"""
    if not material_data:
        return "无材料数据"

    lines = [f"### 📖 {material_data.get('title', '未命名材料')}", ""]

    text_blocks = material_data.get("text_blocks", [])
    if text_blocks:
        for block in text_blocks:
            page = block.get("page", "?")
            text = block.get("text", "")
            # 限制每页展示的文字长度，避免界面过长
            if len(text) > 1000:
                text = text[:1000] + "\n\n... (内容过长，已截断，完整内容已保存)"
            lines.append(f"**第{page}页:**")
            lines.append(text)
            lines.append("")
    else:
        lines.append("*（未提取到文本内容，材料可能主要为图片）*")
        lines.append("")

    return "\n".join(lines)


def _format_images_for_display(material_data: Dict) -> str:
    """格式化图片信息展示"""
    image_paths = material_data.get("image_paths", [])
    if not image_paths:
        return "无提取的图片"

    lines = []
    for i, path in enumerate(image_paths, 1):
        filename = os.path.basename(path)
        lines.append(f"🖼️ 图片{i}: `{filename}`")
    return "\n".join(lines)


# ============================================================
# Gradio 界面构建
# ============================================================

def create_ui():
    """构建Gradio Web界面"""

    # 自定义CSS
    custom_css = """
    .main-title {
        text-align: center;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .main-title h1 {
        margin: 0;
        font-size: 2em;
    }
    .main-title p {
        margin: 5px 0 0 0;
        opacity: 0.9;
    }
    .section-title {
        border-left: 4px solid #667eea;
        padding-left: 12px;
        margin-top: 10px;
        margin-bottom: 10px;
    }
    footer {
        text-align: center;
        color: #999;
        padding: 20px;
        font-size: 0.85em;
    }
    """

    with gr.Blocks(
        css=custom_css,
        title="跨模态教学辅助系统",
        theme=gr.themes.Soft(),
    ) as app:

        # ---- 状态变量 ----
        # 在页面内共享当前的材料数据
        material_state = gr.State(None)

        # ---- 页头 ----
        gr.HTML("""
        <div class="main-title">
            <h1>🎓 跨模态教学辅助系统</h1>
            <p>基于 Qwen-VL 多模态大模型 | 支持 PPT / PDF / 图片 | 知识点总结 · 智能问答 · 题目生成</p>
        </div>
        """)

        # ================================================
        # 第一行：文件上传区
        # ================================================
        with gr.Row():
            with gr.Column(scale=1):
                gr.HTML('<h3 class="section-title">📤 上传教学材料</h3>')
                file_input = gr.File(
                    label="选择教学材料文件",
                    file_types=[".pdf", ".pptx", ".ppt", ".png", ".jpg", ".jpeg", ".bmp"],
                    type="filepath",
                )
                extra_images = gr.File(
                    label="📷 补充上传图片（可选，如PPT截图）",
                    file_types=["image"],
                    file_count="multiple",
                    type="filepath",
                )
                parse_btn = gr.Button("🔍 解析材料", variant="primary", size="lg")
                parse_status = gr.Textbox(
                    label="解析状态",
                    lines=3,
                    interactive=False,
                )

            with gr.Column(scale=2):
                gr.HTML('<h3 class="section-title">📋 材料内容预览</h3>')
                material_display = gr.Markdown(
                    value="*等待上传材料...*",
                    label="提取的文字内容",
                )
                image_display = gr.Textbox(
                    label="提取的图片",
                    lines=4,
                    interactive=False,
                    visible=True,
                )

        # 绑定解析按钮事件
        parse_btn.click(
            fn=handle_file_upload,
            inputs=[file_input, extra_images],
            outputs=[material_state, material_display, image_display, parse_status],
        )

        gr.Markdown("---")

        # ================================================
        # 第二行：知识点总结
        # ================================================
        with gr.Row():
            gr.HTML('<h3 class="section-title">📝 知识点总结</h3>')

        with gr.Row():
            with gr.Column(scale=1):
                summary_btn = gr.Button(
                    "🤖 生成知识点总结",
                    variant="secondary",
                    size="lg",
                )
            with gr.Column(scale=3):
                pass  # 占位，让按钮左对齐

        with gr.Row():
            with gr.Column(scale=2):
                summary_output = gr.Markdown(
                    value="*点击按钮生成知识点总结...*",
                    label="总结内容",
                )
            with gr.Column(scale=1):
                key_points_output = gr.Markdown(
                    value="",
                    label="关键要点",
                )

        summary_btn.click(
            fn=handle_generate_summary,
            inputs=[material_state],
            outputs=[summary_output, key_points_output],
        )

        gr.Markdown("---")

        # ================================================
        # 第三行：学生问答
        # ================================================
        with gr.Row():
            gr.HTML('<h3 class="section-title">💬 学生问答</h3>')

        with gr.Row():
            question_input = gr.Textbox(
                label="输入你的问题",
                placeholder="例如：光合作用分为哪两个阶段？请详细说明。",
                lines=2,
                scale=4,
            )
            ask_btn = gr.Button("📨 提问", variant="primary", scale=1)

        answer_output = gr.Markdown(
            value="*等待提问...*",
            label="回答内容",
        )

        ask_btn.click(
            fn=handle_answer_question,
            inputs=[material_state, question_input],
            outputs=[answer_output],
        )

        gr.Markdown("---")

        # ================================================
        # 第四行：练习题生成
        # ================================================
        with gr.Row():
            gr.HTML('<h3 class="section-title">📝 练习题生成</h3>')

        with gr.Row():
            num_questions = gr.Dropdown(
                label="题目数量",
                choices=["1", "2", "3", "4", "5"],
                value="5",
                scale=1,
            )
            quiz_btn = gr.Button(
                "🎯 生成练习题",
                variant="secondary",
                size="lg",
                scale=1,
            )
            # 用空白列让控件紧凑排列
            with gr.Column(scale=3):
                pass

        quiz_output = gr.Markdown(
            value="*点击按钮生成练习题...*",
            label="练习题",
        )

        quiz_btn.click(
            fn=handle_generate_quiz,
            inputs=[material_state, num_questions],
            outputs=[quiz_output],
        )

        gr.Markdown("---")

        # ---- 页脚 ----
        gr.HTML("""
        <footer>
            <p>跨模态教学辅助系统 · 基于 Qwen-VL (qwen-vl-plus) · 多模态大模型课程期末项目</p>
            <p>上传的材料仅用于本次会话，不会保存到服务器</p>
        </footer>
        """)

    return app


# ============================================================
# 程序入口
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("🎓 跨模态教学辅助系统")
    print("   基于 Qwen-VL 多模态大模型")
    print("=" * 60)

    # 检查API Key状态
    if not os.environ.get("DASHSCOPE_API_KEY"):
        print("\n⚠️  未检测到 DASHSCOPE_API_KEY 环境变量")
        print("   应用将以 Mock 模式运行（展示占位数据）")
        print("   设置方法:")
        print("   - Windows CMD:  set DASHSCOPE_API_KEY=your-key")
        print("   - Windows PowerShell: $env:DASHSCOPE_API_KEY='your-key'")
        print("   - 或在 .env 文件中设置后通过 python-dotenv 加载")
        print()
        print("   获取 API Key: https://dashscope.console.aliyun.com/")
        print()

    app_ui = create_ui()
    app_ui.queue()  # 启用请求队列，防止并发问题

    app_ui.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,       # 如需外网访问可设为True（生成临时公网链接）
        inbrowser=True,    # 自动打开浏览器
        show_error=True,
    )
