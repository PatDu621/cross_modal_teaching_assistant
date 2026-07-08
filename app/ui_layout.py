"""Gradio layout for the cross-modal teaching assistant frontend."""

import gradio as gr

from ui_styles import CUSTOM_CSS


def show_page(page_name):
    """Return visibility updates for the four workspace pages."""
    return (
        gr.update(visible=page_name == "upload"),
        gr.update(visible=page_name == "preview"),
        gr.update(visible=page_name == "assistant"),
        gr.update(visible=page_name == "export"),
        gr.update(variant="primary" if page_name == "upload" else "secondary"),
        gr.update(variant="primary" if page_name == "preview" else "secondary"),
        gr.update(variant="primary" if page_name == "assistant" else "secondary"),
        gr.update(variant="primary" if page_name == "export" else "secondary"),
    )


def create_ui(
    *,
    supported_upload_types,
    initial_material_meta,
    model_status,
    handle_file_upload,
    handle_generate_summary,
    handle_answer_question,
    handle_generate_quiz,
    clear_material,
    clear_results,
):
    """Build the Gradio teaching platform workspace."""
    with gr.Blocks(
        title="跨模态教学辅助系统",
        css=CUSTOM_CSS,
        theme=gr.themes.Soft(),
    ) as app:
        material_state = gr.State(None)

        gr.HTML(
            f"""
            <div class="edu-header">
                <div class="edu-brand">
                  <div class="edu-logo">AI</div>
                  <div>
                    <h1 class="edu-title">跨模态教学辅助系统</h1>
                    <p class="edu-subtitle">多模态材料解析、教学总结、问答和练习生成的一体化工作台</p>
                  </div>
                </div>
                <div class="edu-status-pill">
                  <span class="edu-status-dot"></span>
                  <span>{model_status}</span>
                </div>
            </div>
            """
        )

        with gr.Row(elem_classes=["edu-layout"]):
            with gr.Column(scale=1, min_width=238, elem_classes=["edu-sidebar"]):
                gr.HTML(
                    """
                    <div class="edu-side-label">模块导航</div>
                    <div class="edu-sidebar-note">
                      每个功能独立成页。左侧切换模块，中间区域只展示当前工作内容。
                    </div>
                    """
                )
                nav_upload = gr.Button("上传解析", variant="primary")
                nav_preview = gr.Button("材料预览")
                nav_assistant = gr.Button("AI 助教")
                nav_export = gr.Button("结果导出")
                gr.HTML(
                    """
                    <div class="edu-sidebar-note accent">
                      建议流程：上传材料 -> 检查预览 -> 生成内容 -> 导出结果。
                    </div>
                    """
                )

            with gr.Column(scale=5, elem_classes=["edu-main"]):
                with gr.Group(visible=True) as upload_page:
                    gr.HTML(
                        """
                        <div class="edu-page-head">
                          <div class="edu-page-icon green">U</div>
                          <div>
                            <h2>上传解析</h2>
                            <p>导入课程材料，系统会提取文字、图片和材料元信息。</p>
                          </div>
                          <span class="edu-dot purple"></span>
                          <span class="edu-dot blue"></span>
                          <span class="edu-dot yellow"></span>
                        </div>
                        """
                    )
                    with gr.Row(elem_classes=["edu-page-grid"]):
                        with gr.Column(scale=1, elem_classes=["edu-card", "edu-card-balanced"]):
                            gr.HTML(
                                """
                                <div class="edu-card-title">
                                  <span class="edu-mini-icon green">01</span>
                                  <div>
                                    <h3>选择教学材料</h3>
                                    <p>支持 PDF、PPT 和常见图片格式。</p>
                                  </div>
                                </div>
                                """
                            )
                            with gr.Row(elem_classes=["edu-inner-grid"]):
                                file_input = gr.File(
                                    label="教学材料",
                                    file_types=supported_upload_types,
                                    type="filepath",
                                )
                                extra_images = gr.File(
                                    label="补充图片",
                                    file_types=["image"],
                                    file_count="multiple",
                                    type="filepath",
                                )
                            with gr.Row(elem_classes=["edu-card-actions"]):
                                parse_btn = gr.Button("解析材料", variant="primary")
                                clear_material_btn = gr.Button("清空材料")

                        with gr.Column(scale=1, elem_classes=["edu-card", "edu-card-balanced"]):
                            gr.HTML(
                                """
                                <div class="edu-card-title">
                                  <span class="edu-mini-icon blue">02</span>
                                  <div>
                                    <h3>解析状态</h3>
                                    <p>解析成功后，可切换到材料预览页查看内容。</p>
                                  </div>
                                </div>
                                """
                            )
                            parse_status = gr.Textbox(
                                label="解析状态",
                                value="等待上传材料。",
                                lines=9,
                                interactive=False,
                                elem_classes=["edu-fill-textbox"],
                            )

                    with gr.Column(elem_classes=["edu-card", "edu-card-wide", "edu-assistant-card"]):
                        gr.HTML(
                            """
                            <div class="edu-card-title">
                              <span class="edu-mini-icon yellow">03</span>
                              <div>
                                <h3>材料信息</h3>
                                <p>材料 ID、页数、图片数和模型状态会在这里汇总。</p>
                              </div>
                            </div>
                            """
                        )
                        material_meta = gr.HTML(initial_material_meta)

                with gr.Group(visible=False) as preview_page:
                    gr.HTML(
                        """
                        <div class="edu-page-head">
                          <div class="edu-page-icon blue">P</div>
                          <div>
                            <h2>材料预览</h2>
                            <p>将文本和图片拆开检查，确保 AI 助教拿到的是正确材料。</p>
                          </div>
                          <span class="edu-dot green"></span>
                          <span class="edu-dot purple"></span>
                          <span class="edu-dot yellow"></span>
                        </div>
                        """
                    )
                    with gr.Column(elem_classes=["edu-card", "edu-card-wide"]):
                        gr.HTML(
                            """
                            <div class="edu-card-title">
                              <span class="edu-mini-icon green">TXT</span>
                              <div>
                                <h3>文本内容</h3>
                                <p>按页展示提取到的课程文本。</p>
                              </div>
                            </div>
                            """
                        )
                        material_display = gr.Markdown(
                            value="*等待上传材料...*",
                            elem_classes=["edu-result"],
                        )
                    with gr.Column(elem_classes=["edu-card", "edu-card-wide"]):
                        gr.HTML(
                            """
                            <div class="edu-card-title">
                              <span class="edu-mini-icon purple">IMG</span>
                              <div>
                                <h3>图片内容</h3>
                                <p>展示 PDF/PPT 中提取的图片和补充上传截图。</p>
                              </div>
                            </div>
                            """
                        )
                        image_gallery = gr.Gallery(
                            label="提取或补充的图片",
                            columns=4,
                            height=420,
                            object_fit="contain",
                        )

                with gr.Group(visible=False) as assistant_page:
                    gr.HTML(
                        """
                        <div class="edu-page-head">
                          <div class="edu-page-icon purple">A</div>
                          <div>
                            <h2>AI 助教</h2>
                            <p>基于当前材料生成课堂总结、学生问答和练习题。</p>
                          </div>
                          <span class="edu-dot green"></span>
                          <span class="edu-dot blue"></span>
                          <span class="edu-dot yellow"></span>
                        </div>
                        """
                    )
                    with gr.Column(elem_classes=["edu-card", "edu-card-wide"]):
                        with gr.Tabs():
                            with gr.Tab("知识点总结"):
                                gr.HTML(
                                    """
                                    <div class="edu-card-title">
                                      <span class="edu-mini-icon green">SUM</span>
                                      <div>
                                        <h3>知识点总结</h3>
                                        <p>提炼材料主线和关键概念。</p>
                                      </div>
                                    </div>
                                    """
                                )
                                summary_btn = gr.Button(
                                    "生成知识点总结",
                                    variant="primary",
                                )
                                with gr.Row(elem_classes=["edu-two-col"]):
                                    summary_output = gr.Markdown(
                                        value="*点击按钮生成知识点总结...*",
                                        elem_classes=["edu-result"],
                                    )
                                    key_points_output = gr.Markdown(
                                        value="",
                                        elem_classes=["edu-result"],
                                    )

                            with gr.Tab("智能问答"):
                                gr.HTML(
                                    """
                                    <div class="edu-card-title">
                                      <span class="edu-mini-icon blue">QA</span>
                                      <div>
                                        <h3>智能问答</h3>
                                        <p>围绕材料回答学生可能提出的问题。</p>
                                      </div>
                                    </div>
                                    """
                                )
                                question_input = gr.Textbox(
                                    label="学生问题",
                                    placeholder="例如：这份材料的核心概念是什么？",
                                    lines=3,
                                )
                                gr.Examples(
                                    examples=[
                                        "这份材料主要讲了哪些知识点？",
                                        "请用更容易理解的话解释第一个概念。",
                                        "材料中有没有适合作为考试题的重点？",
                                    ],
                                    inputs=question_input,
                                )
                                ask_btn = gr.Button("提交问题", variant="primary")
                                answer_output = gr.Markdown(
                                    value="*等待提问...*",
                                    elem_classes=["edu-result"],
                                )

                            with gr.Tab("练习题生成"):
                                gr.HTML(
                                    """
                                    <div class="edu-card-title">
                                      <span class="edu-mini-icon yellow">EX</span>
                                      <div>
                                        <h3>练习题生成</h3>
                                        <p>生成单项选择题、答案和解析。</p>
                                      </div>
                                    </div>
                                    """
                                )
                                with gr.Row():
                                    num_questions = gr.Dropdown(
                                        label="题目数量",
                                        choices=["1", "2", "3", "4", "5"],
                                        value="5",
                                    )
                                    quiz_btn = gr.Button("生成练习题", variant="primary")
                                quiz_output = gr.Markdown(
                                    value="*点击按钮生成练习题...*",
                                    elem_classes=["edu-result"],
                                )

                with gr.Group(visible=False) as export_page:
                    gr.HTML(
                        """
                        <div class="edu-page-head">
                          <div class="edu-page-icon yellow">D</div>
                          <div>
                            <h2>结果导出</h2>
                            <p>将模型输出保存为 JSON 和 Markdown，方便提交项目与制作 Demo。</p>
                          </div>
                          <span class="edu-dot green"></span>
                          <span class="edu-dot blue"></span>
                          <span class="edu-dot purple"></span>
                        </div>
                        """
                    )
                    with gr.Row(elem_classes=["edu-page-grid", "edu-export-grid"]):
                        with gr.Column(scale=1, elem_classes=["edu-card", "edu-card-balanced"]):
                            gr.HTML(
                                """
                                <div class="edu-card-title">
                                  <span class="edu-mini-icon green">JSON</span>
                                  <div>
                                    <h3>结构化结果</h3>
                                    <p>用于程序读取或归档。</p>
                                  </div>
                                </div>
                                """
                            )
                            json_download = gr.File(
                                label="下载 JSON 结果",
                                interactive=False,
                            )
                        with gr.Column(scale=1, elem_classes=["edu-card", "edu-card-balanced"]):
                            gr.HTML(
                                """
                                <div class="edu-card-title">
                                  <span class="edu-mini-icon purple">MD</span>
                                  <div>
                                    <h3>可读报告</h3>
                                    <p>用于截图、汇报或整理材料。</p>
                                  </div>
                                </div>
                                """
                            )
                            markdown_download = gr.File(
                                label="下载 Markdown 结果",
                                interactive=False,
                            )
                    with gr.Column(elem_classes=["edu-card", "edu-card-wide", "edu-status-card"]):
                        export_notice = gr.Textbox(
                            label="导出状态",
                            value="生成结果后会在这里显示导出文件。",
                            lines=4,
                            interactive=False,
                            elem_classes=["edu-fill-textbox"],
                        )
                        with gr.Row(elem_classes=["edu-card-actions"]):
                            clear_results_btn = gr.Button("清空生成结果")

        gr.HTML(
            """
            <footer>
                跨模态教学辅助系统 · Qwen-VL / Mock 双模式 · 课程项目演示版
            </footer>
            """
        )

        page_outputs = [
            upload_page,
            preview_page,
            assistant_page,
            export_page,
            nav_upload,
            nav_preview,
            nav_assistant,
            nav_export,
        ]
        nav_upload.click(fn=lambda: show_page("upload"), outputs=page_outputs)
        nav_preview.click(fn=lambda: show_page("preview"), outputs=page_outputs)
        nav_assistant.click(fn=lambda: show_page("assistant"), outputs=page_outputs)
        nav_export.click(fn=lambda: show_page("export"), outputs=page_outputs)

        parse_btn.click(
            fn=handle_file_upload,
            inputs=[file_input, extra_images],
            outputs=[
                material_state,
                material_display,
                image_gallery,
                material_meta,
                parse_status,
            ],
        )
        clear_material_btn.click(
            fn=clear_material,
            outputs=[
                material_state,
                material_display,
                image_gallery,
                material_meta,
                parse_status,
            ],
        )
        summary_btn.click(
            fn=handle_generate_summary,
            inputs=[material_state],
            outputs=[
                summary_output,
                key_points_output,
                json_download,
                markdown_download,
                export_notice,
            ],
        )
        ask_btn.click(
            fn=handle_answer_question,
            inputs=[material_state, question_input],
            outputs=[answer_output, json_download, markdown_download, export_notice],
        )
        quiz_btn.click(
            fn=handle_generate_quiz,
            inputs=[material_state, num_questions],
            outputs=[quiz_output, json_download, markdown_download, export_notice],
        )
        clear_results_btn.click(
            fn=clear_results,
            outputs=[
                summary_output,
                key_points_output,
                answer_output,
                quiz_output,
                json_download,
                markdown_download,
                export_notice,
            ],
        )

    return app
