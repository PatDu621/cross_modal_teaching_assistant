"""
helpers.py - 公共工具函数
包含文件类型判断、JSON读写、ID生成等通用功能
"""

import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any


# 支持的文件格式
SUPPORTED_EXTENSIONS = {
    "pdf": [".pdf"],
    "ppt": [".pptx", ".ppt"],
    "image": [".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"],
}

# 所有可识别的扩展名（合并为一个列表）
ALL_SUPPORTED = []
for exts in SUPPORTED_EXTENSIONS.values():
    ALL_SUPPORTED.extend(exts)


def generate_material_id() -> str:
    """
    生成唯一的材料ID
    格式: material_YYYYMMDD_HHMMSS_短UUID
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    short_uuid = uuid.uuid4().hex[:8]
    return f"material_{timestamp}_{short_uuid}"


def get_file_type(file_path: str) -> str:
    """
    根据文件扩展名判断文件类型
    返回: "pdf" | "ppt" | "image" | "unknown"
    """
    ext = os.path.splitext(file_path)[1].lower()
    for file_type, extensions in SUPPORTED_EXTENSIONS.items():
        if ext in extensions:
            return file_type
    return "unknown"


def get_file_name_without_ext(file_path: str) -> str:
    """获取不带扩展名的文件名"""
    basename = os.path.basename(file_path)
    return os.path.splitext(basename)[0]


def ensure_dir(dir_path: str) -> None:
    """确保目录存在，不存在则创建"""
    os.makedirs(dir_path, exist_ok=True)


def save_json(data: Dict[str, Any], file_path: str) -> None:
    """
    将数据保存为JSON文件
    - 自动创建父目录
    - 使用ensure_ascii=False保留中文字符
    - 缩进2空格，方便阅读
    """
    ensure_dir(os.path.dirname(file_path))
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_json(file_path: str) -> Dict[str, Any]:
    """从JSON文件读取数据"""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def is_supported_file(file_path: str) -> bool:
    """检查文件是否为支持的格式"""
    return get_file_type(file_path) != "unknown"
