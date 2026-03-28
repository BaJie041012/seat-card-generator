# ==============================================================================
# 文件名称: start_server.py
# 功能描述: 启动网络服务的脚本
# 创建日期: 2026-03-25
# 作    者: 戒者有八
# ==============================================================================
"""
启动网络服务脚本

本脚本用于启动文本处理与模板填充服务，提供HTTP接口供同一网段内的其他设备访问。
"""

import os
import sys
import subprocess
import time

def check_dependencies():
    """
    检查依赖是否安装
    """
    try:
        import flask
        import docx
        return True
    except ImportError:
        return False

def install_dependencies():
    """
    安装依赖
    """
    print("正在安装依赖...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("依赖安装成功")
        return True
    except subprocess.CalledProcessError:
        print("依赖安装失败，请手动安装:")
        print("pip install -r requirements.txt")
        return False

def start_server():
    """
    启动服务
    """
    # 检查依赖
    if not check_dependencies():
        if not install_dependencies():
            return
    
    # 启动服务
    print("\n启动文本处理与模板填充服务...")
    print("服务将在后台运行，可通过 http://localhost:5000 访问")
    print("按 Ctrl+C 停止服务\n")
    
    try:
        # 导入并运行服务
        from server import run_server
        run_server()
    except KeyboardInterrupt:
        print("\n服务已停止")
    except Exception as e:
        print(f"启动服务时出错: {e}")

if __name__ == "__main__":
    start_server()
