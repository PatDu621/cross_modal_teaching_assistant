# 🎓 跨模态教学辅助系统

> 基于 Qwen-VL 多模态大模型的智能教学辅助工具
>
> 多模态大模型课程 · 期末项目 · 2026年7月

---

## 📖 项目简介

跨模态教学辅助系统是一个基于阿里云 Qwen-VL 多模态大模型的 Web 应用，旨在辅助 K12 和大学课程的教师进行教学工作。系统支持上传 PPT、PDF、图片等多种格式的教学材料，通过多模态 AI 理解材料内容，自动生成：

1. **知识点总结** — 提炼材料的核心知识点和关键要点
2. **智能问答** — 学生提问，AI 基于教学材料给出准确回答
3. **练习题生成** — 自动生成单项选择题，附带答案和解析

---

## 🏗️ 项目结构

```
cross_modal_teaching_assistant/
├── app/
│   └── main.py                 # Gradio 主程序入口（Web界面）
├── modules/
│   ├── input_processor/
│   │   ├── __init__.py
│   │   └── processor.py        # 多模态输入处理（解析PPT/PDF/图片）
│   ├── model_engine/
│   │   ├── __init__.py
│   │   └── qwen_engine.py      # Qwen-VL API调用封装
│   └── utils/
│       ├── __init__.py
│       └── helpers.py          # 公共工具函数
├── data/
│   ├── raw/                    # 用户上传的原始文件
│   ├── processed/              # 处理后的结构化数据
│   └── outputs/                # 模型输出结果
├── examples/                   # 示例教学材料
├── docs/
│   └── tech_report_outline.md  # 技术报告大纲
├── requirements.txt            # Python依赖包
└── README.md                   # 本文件
```

---

## 🚀 快速开始

### 1. 环境准备

Python 3.9+ 环境（推荐使用虚拟环境）：

```bash
# 创建虚拟环境（可选）
python -m venv venv

# Windows 激活虚拟环境
venv\Scripts\activate

# Linux/Mac 激活虚拟环境
source venv/bin/activate
```

### 2. 安装依赖

```bash
cd cross_modal_teaching_assistant
pip install -r requirements.txt
```

### 3. 设置 API Key

前往 [阿里云百炼平台](https://dashscope.console.aliyun.com/) 申请 DashScope API Key。

**Windows (CMD):**
```cmd
set DASHSCOPE_API_KEY=sk-your-api-key-here
```

**Windows (PowerShell):**
```powershell
$env:DASHSCOPE_API_KEY="sk-your-api-key-here"
```

**Linux / Mac:**
```bash
export DASHSCOPE_API_KEY=sk-your-api-key-here
```

> ⚠️ **注意**: 如果不设置 API Key，系统会以 **Mock 模式** 运行，生成占位数据用于界面演示。真实的 AI 功能需要有效的 API Key。

### 4. 启动应用

```bash
python app/main.py
```

浏览器会自动打开 `http://127.0.0.1:7860`，看到系统界面即表示启动成功。

---

## 📡 数据接口规范

### 材料数据 (MaterialProcessor 输出)

```json
{
  "material_id": "material_20260705_143022_a1b2c3d4",
  "title": "教学材料文件名",
  "text_blocks": [
    {
      "page": 1,
      "text": "从第1页提取的文字内容..."
    },
    {
      "page": 2,
      "text": "从第2页提取的文字内容..."
    }
  ],
  "image_paths": [
    "data/processed/material_xxx_images/slide1_image.png",
    "data/processed/material_xxx_images/uploaded_screenshot.jpg"
  ]
}
```

### 知识点总结 (generate_summary 输出)

```json
{
  "material_id": "material_20260705_143022_a1b2c3d4",
  "summary": "该教学材料涵盖了以下核心领域...",
  "key_points": [
    "要点1：核心概念的定义和内涵",
    "要点2：关键原理的工作机制",
    "要点3：实际应用场景分析"
  ]
}
```

### 问答回复 (answer_question 输出)

```json
{
  "material_id": "material_20260705_143022_a1b2c3d4",
  "question": "学生提出的问题？",
  "answer": "基于教学材料的详细回答..."
}
```

### 练习题 (generate_quiz 输出)

```json
{
  "material_id": "material_20260705_143022_a1b2c3d4",
  "questions": [
    {
      "type": "single_choice",
      "question": "根据材料，以下哪个说法是正确的？",
      "options": [
        "A. 选项一",
        "B. 选项二",
        "C. 选项三",
        "D. 选项四"
      ],
      "answer": "B",
      "explanation": "根据材料第2页的内容，选项B是正确的，因为..."
    }
  ]
}
```

---

## 🔧 技术选型

| 组件 | 技术 | 说明 |
|------|------|------|
| 多模态模型 | Qwen-VL-Plus (DashScope) | 阿里云视觉语言模型，支持文本+图像联合推理 |
| 后端框架 | Python | 主语言，生态丰富 |
| Web界面 | Gradio 4.x | 零前端代码，Python 直接构建交互界面 |
| PDF解析 | pdfplumber | 稳定可靠的PDF文本提取 |
| PPT解析 | python-pptx | Office Open XML格式PPT解析 |
| 图像处理 | Pillow (PIL) | 图像验证和基础处理 |

---

## ⚠️ 已知限制与占位说明

> 以下功能在当前版本中使用简化方案或占位数据，详见各模块源码中的注释。

1. **PDF 内嵌图片提取** — 暂不支持。pdfplumber 主要用于文本提取，不提取图片。如需图片模态输入，请使用界面中的"补充上传图片"功能。
2. **PPT 幻灯片渲染为图片** — 暂不支持。需要外部工具（如 LibreOffice）将每页PPT导出为图片。当前可手动上传截图。
3. **Mock 模式** — 未设置 API Key 时，`qwen_engine.py` 中的三个函数返回模拟数据，内容带有 `【模拟数据】` 标记。设置 DASHSCOPE_API_KEY 后自动切换为真实API调用。
4. **长文本处理** — Qwen-VL 的上下文窗口有限，超长材料会被截断。建议将大文件拆分为多个小文件分别处理。
5. **PPT .ppt 格式** — 仅完整支持 `.pptx`（Office 2007+）。旧版 `.ppt` 格式支持有限。

---

## 👥 小组信息

| 角色 | 工作内容 |
|------|----------|
| 组员1 | 项目统筹、系统架构设计、Prompt工程 |
| 组员2 | 输入处理模块（PDF/PPT/图片解析） |
| 组员3 | Qwen-VL API封装、Gradio前端开发 |
| 组员4 | 技术报告撰写、PPT制作、Demo视频录制 |

（请根据实际情况填写具体姓名和学号）

---

## 📝 提交清单

课程作业需要提交以下材料：

- [ ] 技术报告（基于 `docs/tech_report_outline.md` 扩展）
- [ ] 项目源码（本仓库所有代码）
- [ ] 5页 PPT（项目介绍、架构、技术亮点、演示截图、总结）
- [ ] Demo 演示视频（3-5分钟，展示系统功能）
- [ ] 团队报告（分工、合作过程、个人总结）

---

## 📄 许可证

本项目仅用于课程学习目的。

---

## 🔗 参考链接

- [Qwen-VL 模型介绍](https://help.aliyun.com/zh/dashscope/developer-reference/qwen-vl-api)
- [阿里云 DashScope 控制台](https://dashscope.console.aliyun.com/)
- [Gradio 官方文档](https://www.gradio.app/docs/)
- [python-pptx 文档](https://python-pptx.readthedocs.io/)
- [pdfplumber 文档](https://github.com/jsvine/pdfplumber)
