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

使用方法:
    python main.py --gui              # 启动图形界面
    python main.py --help             # 查看命令行帮助

模块说明:
    - config.py: 配置管理模块，定义AI服务、模板和应用程序配置
    - ai_service.py: AI服务接口模块，处理与AI API的通信
    - template_processor.py: 模板处理模块，支持多种格式的模板填充
    - text_extractor.py: 文本提取模块，使用AI从文本中提取结构化信息
    - gui.py: 图形界面模块，提供基于tkinter的用户界面
    - main.py: 主程序入口，处理命令行参数和启动应用
"""

# 从各子模块导入核心组件，供外部使用
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
