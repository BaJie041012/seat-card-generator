# ==============================================================================
# 文件名称: main.py
# 功能描述: 自动化文本处理与模板填充程序的主程序入口，处理命令行参数和启动应用
# 创建日期: 2026-03-14
# 作    者: 戒者有八
# 版本: 1.0.0
# 描述: 应用程序的主入口点，负责解析命令行参数、初始化环境并启动相应的运行模式
# ==============================================================================
"""
自动化文本处理与模板填充程序 - 主程序入口

本模块是应用程序的入口点，负责:
    - 解析命令行参数，支持GUI模式和命令行模式
    - 初始化运行环境，确保必要的目录结构存在
    - 启动GUI或命令行模式，根据用户选择执行相应功能
    - 协调各模块完成文本处理和模板填充任务

使用方法:
    python main.py --gui              # 启动图形界面
    python main.py --help             # 查看命令行帮助
    python main.py --template template.txt --text "要处理的文本"
    python main.py --create-template sample.txt  # 创建示例模板

设计思路:
    - 使用argparse模块处理命令行参数，支持多种运行模式
    - GUI模式适合日常使用，提供直观的图形界面
    - 命令行模式适合自动化脚本调用，支持批处理操作
    - 延迟导入GUI模块以减少启动时间

核心功能:
    - 模板管理：创建、选择和处理模板文件
    - 文本处理：使用AI服务提取和处理文本信息
    - 席卡生成：根据模板生成席卡文档
"""

import os
import sys
import argparse
import json
from typing import Optional

from config import CONFIG, AIConfig, ensure_directories
from ai_service import create_ai_service
from template_processor import create_template_processor
from text_extractor import create_extractor


# ------------------------------------------------------------------------------
# 环境初始化函数
# 功能: 初始化应用程序运行环境
# ------------------------------------------------------------------------------
def setup_environment():
    """
    初始化运行环境
    
    功能说明:
        确保必要的目录结构存在，
        包括模板目录和输出目录。
    
    调用时机:
        在应用程序启动时首先调用。
    """
    ensure_directories(CONFIG)


# ------------------------------------------------------------------------------
# GUI模式启动函数
# 功能: 启动图形用户界面
# ------------------------------------------------------------------------------
def run_gui():
    """
    启动GUI模式
    
    功能说明:
        导入GUI模块并启动图形界面。
        GUI模块延迟导入以减少启动时间。
    
    使用场景:
        当用户指定--gui参数或未提供任何参数时调用。
    """
    from gui import run_gui
    run_gui()


# ------------------------------------------------------------------------------
# 命令行模式运行函数
# 功能: 处理命令行参数并执行相应操作
# ------------------------------------------------------------------------------
def run_cli(args):
    """
    运行命令行模式
    
    参数:
        args: 解析后的命令行参数对象
    
    返回值:
        int: 退出状态码(0表示成功，非0表示失败)
    
    处理流程:
        1. 检查并设置API配置
        2. 处理创建模板请求
        3. 处理文本处理请求
    """
    # 检查API密钥配置
    if not CONFIG.ai.api_key:
        if args.api_key:
            CONFIG.ai.api_key = args.api_key
        else:
            print("错误: 请通过 --api-key 参数或配置文件设置API密钥")
            return 1
    
    # 应用命令行配置覆盖
    if args.api_url:
        CONFIG.ai.api_url = args.api_url
    if args.model:
        CONFIG.ai.model = args.model
    
    # 创建服务实例
    ai_service = create_ai_service(CONFIG.ai)
    template_processor = create_template_processor()
    
    # 处理创建模板请求
    if args.create_template:
        template_path = template_processor.create_sample_template(args.create_template)
        print(f"示例模板已创建: {template_path}")
        return 0
    
    # 检查模板参数
    if not args.template:
        print("错误: 请指定模板文件 (--template)")
        return 1
    
    # 检查模板文件是否存在
    if not os.path.exists(args.template):
        print(f"错误: 模板文件不存在: {args.template}")
        return 1
    
    # 获取模板字段
    template_fields = template_processor.get_template_placeholders(args.template)
    print(f"检测到模板字段: {template_fields}")
    
    # 处理文本
    if args.text:
        return process_single(args, ai_service, template_processor, template_fields)
    else:
        print("错误: 请指定输入文本 (--text)")
        return 1


# ------------------------------------------------------------------------------
# 单文本处理函数
# 功能: 处理单条文本并填充模板
# ------------------------------------------------------------------------------
def process_single(args, ai_service, template_processor, template_fields):
    """
    处理单条文本
    
    参数:
        args: 命令行参数
        ai_service: AI服务实例
        template_processor: 模板处理器实例
        template_fields: 模板字段列表
    
    返回值:
        int: 退出状态码
    
    处理流程:
        1. 显示处理进度
        2. 调用AI服务提取数据
        3. 解析AI响应
        4. 填充模板并保存
    """
    print(f"\n处理文本: {args.text[:50]}...")  # 显示文本前50个字符
    
    # 根据模板字段决定处理方式
    if template_fields:
        print("正在提取结构化数据...")
        response = ai_service.extract_structured_data(args.text, template_fields)
    else:
        print("正在处理文本...")
        response = ai_service.process_text(args.text, args.system_prompt)
    
    # 检查处理结果
    if not response.success:
        print(f"错误: {response.error_message}")
        return 1
    
    print("AI处理完成")
    
    # 解析响应数据
    if 'parsed' in response.data:
        data = response.data['parsed']
    else:
        content = response.data.get('content', '')
        try:
            # 尝试从内容中提取JSON
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                data = json.loads(content[json_start:json_end])
            else:
                data = {"content": content}
        except json.JSONDecodeError:
            data = {"content": content}
    
    print(f"提取的数据: {data}")
    
    # 处理模板
    output_filename = args.output or None
    result = template_processor.process_template(args.template, data, output_filename)
    
    # 显示结果
    if result.success:
        print(f"\n处理成功!")
        print(f"输出文件: {result.output_path}")
        return 0
    else:
        print(f"错误: {result.error_message}")
        return 1


# ------------------------------------------------------------------------------
# 主函数
# 功能: 程序入口点，解析参数并启动相应模式
# ------------------------------------------------------------------------------
def main():
    """
    主函数 - 程序入口点
    
    功能说明:
        1. 创建命令行参数解析器
        2. 解析命令行参数
        3. 初始化环境
        4. 根据参数启动GUI或命令行模式
    
    命令行参数:
        --gui: 启动图形界面
        --api-key: AI服务API密钥
        --api-url: AI服务API地址
        --model: AI模型名称
        --template: 模板文件路径
        --text: 要处理的文本内容
        --output: 输出文件名
        --system-prompt: AI系统提示词
        --create-template: 创建示例模板
    """
    # 创建参数解析器
    parser = argparse.ArgumentParser(
        description="自动化文本处理与模板填充程序",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 启动GUI界面
  python main.py --gui

  # 处理单个文本
  python main.py --api-key YOUR_KEY --template template.txt --text "要处理的文本"

  # 创建示例模板
  python main.py --create-template sample.txt
        """
    )
    
    # 定义命令行参数
    parser.add_argument('--gui', action='store_true', help='启动图形界面')
    parser.add_argument('--api-key', type=str, help='AI服务API密钥')
    parser.add_argument('--api-url', type=str, help='AI服务API地址')
    parser.add_argument('--model', type=str, help='AI模型名称')
    parser.add_argument('--template', type=str, help='模板文件路径')
    parser.add_argument('--text', type=str, help='要处理的文本内容')
    parser.add_argument('--output', type=str, help='输出文件名')
    parser.add_argument('--system-prompt', type=str, help='AI系统提示词')
    parser.add_argument('--create-template', type=str, metavar='NAME', help='创建示例模板')
    
    # 解析参数
    args = parser.parse_args()
    
    # 初始化环境
    setup_environment()
    
    # 根据参数选择运行模式
    if args.gui or len(sys.argv) == 1:
        # GUI模式或无参数时启动GUI
        run_gui()
    else:
        # 命令行模式
        sys.exit(run_cli(args))


# 程序入口
if __name__ == "__main__":
    main()
