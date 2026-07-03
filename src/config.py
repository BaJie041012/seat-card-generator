# ==============================================================================
# 文件名称: config.py
# 功能描述: 配置管理模块，定义AI服务、模板和应用程序的配置参数
# 创建日期: 2026-03-14
# 作    者: 戒者有八
# 版本: 1.0.0
# 描述: 本文件负责管理应用程序的所有配置参数，包括AI服务配置、模板配置和应用配置
# ==============================================================================
"""
配置文件 - AI服务配置和模板设置

本模块负责管理应用程序的所有配置参数，包括:
    - AI服务配置: API密钥、地址、模型参数等
    - 模板配置: 模板目录、输出目录、支持的格式等
    - 应用配置: 批处理大小、重试次数等全局设置

设计思路:
    - 使用dataclass装饰器定义配置类，提供类型安全的配置管理
    - 支持默认值设置和配置的灵活组合
    - 使用绝对路径确保模板和输出目录的正确定位

使用方式:
    1. 直接导入CONFIG全局实例使用默认配置
    2. 如需自定义配置，可创建AppConfig实例并传入自定义参数
    3. 在程序启动时调用ensure_directories确保目录存在

核心配置类:
    - AIConfig: 管理AI服务的配置参数
    - TemplateConfig: 管理模板相关的配置参数
    - AppConfig: 整合所有配置，提供统一的配置访问入口

重要功能:
    - ensure_directories: 确保配置中的目录存在，不存在则创建
    - get_default_config: 创建默认的应用配置实例
"""

# 导入必要的模块
import os  # 用于文件和目录操作
import sys  # 用于 PyInstaller 冻结模式检测
from dataclasses import dataclass  # 用于创建数据类
from typing import Optional  # 用于类型注解


# ------------------------------------------------------------------------------
# AI服务配置类
# 功能: 封装AI服务API的所有配置参数
# 设计思路: 使用dataclass实现不可变配置，便于类型检查和IDE提示
# ------------------------------------------------------------------------------
@dataclass
class AIConfig:
    """
    AI服务配置类
    
    属性说明:
        api_key: API访问密钥，用于身份验证
        api_base_url: API服务基础地址
        model: 使用的AI模型名称
        max_tokens: 单次请求最大token数量
        temperature: 生成温度参数，控制输出随机性(0-1)
        timeout: 请求超时时间(秒)
    """
    # API访问密钥，优先从环境变量读取，否则使用内置默认密钥（开箱即用）
    api_key: str = os.environ.get("MINIMAX_API_KEY", "sk-api-mR_lRPZgFVmmyx7OCp83-zqdd2nlvTYM-akr0KyrDIa1ZvrZV4F0sKmKOXULeT8xP3xOYnyEh4_DJTb760jnSL_HfEU2zMOudelCxSObltogy0X0RXx5a2c")
    # API服务基础地址，指向MiniMax API服务
    api_base_url: str = "https://api.minimaxi.com/v1"  # MiniMax API服务地址
    # 使用的AI模型名称，默认使用MiniMax-M2.5
    model: str = "MiniMax-M2.5"  # 默认使用的模型
    # 单次请求最大token数量，限制响应长度，防止超出预算
    max_tokens: int = 2000  # 限制响应长度，防止超出预算
    # 生成温度参数，控制输出随机性(0-1)，0.7为中等温度
    temperature: float = 0.7  # 中等温度，平衡创造性和一致性
    # 请求超时时间(秒)，30秒适应网络延迟
    timeout: int = 30  # 30秒超时，适应网络延迟


# ------------------------------------------------------------------------------
# 模板配置类
# 功能: 定义模板文件的存储位置和输出设置
# 设计思路: 集中管理模板相关路径，便于统一修改和维护
# ------------------------------------------------------------------------------
@dataclass
class TemplateConfig:
    """
    模板配置类
    
    属性说明:
        template_dir: 模板文件存储目录
        output_dir: 输出文件存储目录
        default_template: 默认模板文件名
        supported_formats: 支持的模板格式元组
    """
    # 项目根目录：PyInstaller 打包后以 exe 所在目录为准，开发模式以 src/ 的父目录为准
    if getattr(sys, 'frozen', False):
        _root = os.path.dirname(sys.executable)
    else:
        _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # 模板文件存储目录，存放各类模板文件
    template_dir: str = os.path.join(_root, "templates")  # 模板目录，存放各类模板文件
    # 输出文件存储目录，存放处理后的文件
    output_dir: str = os.path.join(_root, "output")  # 输出目录，存放处理后的文件
    # 默认模板文件名，当未指定模板时使用
    default_template: str = "default_template.docx"  # 默认使用的模板
    # 支持的模板格式元组，包括docx、pdf、txt
    supported_formats: tuple = ("docx", "pdf", "txt")  # 支持的文件格式


# ------------------------------------------------------------------------------
# 应用程序配置类
# 功能: 整合所有配置，提供统一的配置访问入口
# 设计思路: 组合模式，将AI配置和模板配置聚合为应用级配置
# ------------------------------------------------------------------------------
@dataclass
class AppConfig:
    """
    应用程序配置类
    
    属性说明:
        ai: AI服务配置实例
        template: 模板配置实例
        batch_size: 批处理时每批的数量
        retry_attempts: 失败重试次数
    
    设计说明:
        __post_init__方法确保子配置在未显式设置时使用默认值，
        实现配置的懒加载初始化。
    """
    # AI服务配置实例，默认为None，会在__post_init__中自动初始化
    ai: AIConfig = None  # AI服务配置
    # 模板配置实例，默认为None，会在__post_init__中自动初始化
    template: TemplateConfig = None  # 模板配置
    # 批处理大小，平衡性能和资源消耗，默认为10
    batch_size: int = 10  # 批处理大小，平衡性能和资源消耗
    # 失败重试次数，提高容错能力，默认为3
    retry_attempts: int = 3  # 重试次数，提高容错能力
    
    def __post_init__(self):
        """
        初始化后处理
        
        功能: 确保子配置对象存在，未设置时使用默认值
        实现方式: 检查并创建缺失的配置实例
        """
        # 检查AI配置是否为None，如果是则创建默认实例
        if self.ai is None:
            self.ai = AIConfig()
        # 检查模板配置是否为None，如果是则创建默认实例
        if self.template is None:
            self.template = TemplateConfig()


# ------------------------------------------------------------------------------
# 配置工厂函数
# 功能: 创建默认的应用配置实例
# ------------------------------------------------------------------------------
def get_default_config() -> AppConfig:
    """
    获取默认配置
    
    返回值:
        AppConfig: 包含所有默认值的配置实例
    
    使用场景:
        程序启动时初始化配置，或需要重置配置时调用
    """
    # 返回一个新的AppConfig实例，使用所有默认值
    return AppConfig()


# ------------------------------------------------------------------------------
# 目录初始化函数
# 功能: 确保必要的目录存在，不存在则创建
# ------------------------------------------------------------------------------
def ensure_directories(config: AppConfig):
    """
    确保配置中的目录存在
    
    参数:
        config: 应用配置实例
    
    功能说明:
        检查模板目录和输出目录是否存在，不存在则自动创建。
        使用exist_ok=True避免目录已存在时报错。
    
    设计思路:
        在程序启动时调用，确保文件操作前目录已就绪，
        避免因目录不存在导致的文件写入失败。
    """
    # 创建模板目录，如不存在则创建，已存在则不报错
    os.makedirs(config.template.template_dir, exist_ok=True)  # 创建模板目录
    # 创建输出目录，如不存在则创建，已存在则不报错
    os.makedirs(config.template.output_dir, exist_ok=True)  # 创建输出目录


# 全局配置实例，供整个应用程序使用
# 这是应用程序的默认配置实例，其他模块可以直接导入使用
CONFIG = get_default_config()
