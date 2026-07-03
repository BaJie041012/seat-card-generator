# ==============================================================================
# 文件名称: __init__.py
# 功能描述: 自动化文本处理与模板填充程序的包初始化模块，负责导出核心组件和配置
# 创建日期: 2026-03-14
# 作    者: 戒者有八
# ==============================================================================
"""
自动化文本处理与模板填充程序

功能概述:
    1. 接收用户输入的文本内容
    2. 将输入文本发送至指定的AI服务接口进行处理
    3. 获取并解析AI返回的结果数据
    4. 将处理后的结果自动填充到预设的模板文件中

项目结构:
    - src/: 核心后端模块（config、ai_service、card_generator 等）
    - app/: 前端应用（desktop 桌面版、gui 经典版、server Web 服务）
    - scripts/: 启动脚本（main CLI 入口、start_server 服务启动）
    - templates/: 席卡模板文件
"""
import os, sys

# 确保 src/ 目录在 sys.path 中，使内部 bare import 正常工作
_src_dir = os.path.dirname(os.path.abspath(__file__))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

# 核心组件导出（使用 try/except 兼容两种导入方式：包导入 和 直接导入）
try:
    from .config import CONFIG, AIConfig, TemplateConfig, AppConfig
    from .ai_service import AIService, AIResponse, create_ai_service
    from .template_processor import TemplateProcessor, TemplateResult, create_template_processor
    from .text_extractor import AIExtractor, create_extractor
except ImportError:
    from config import CONFIG, AIConfig, TemplateConfig, AppConfig
    from ai_service import AIService, AIResponse, create_ai_service
    from template_processor import TemplateProcessor, TemplateResult, create_template_processor
    from text_extractor import AIExtractor, create_extractor

# 版本号定义
__version__ = "1.0.0"

# 公开API列表，定义模块对外暴露的接口
__all__ = [
    'CONFIG',
    'AIConfig',
    'TemplateConfig', 
    'AppConfig',
    'AIService',
    'AIResponse',
    'create_ai_service',
    'TemplateProcessor',
    'TemplateResult',
    'create_template_processor',
    'AIExtractor',
    'create_extractor',
]
