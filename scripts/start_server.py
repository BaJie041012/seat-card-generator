# ==============================================================================
# 文件名称: start_server.py
# 功能描述: 启动网络服务的脚本，检查依赖并启动FastAPI服务
# 创建日期: 2026-03-25
# 作    者: 戒者有八
# 版本: 2.0.0
# 描述: 用于启动席卡生成服务，提供HTTP接口供Flutter客户端和Web访问
# ==============================================================================
"""
启动网络服务脚本

使用方法:
    python start_server.py

服务启动后，可通过以下地址访问:
    - 本地访问: http://localhost:8000
    - 局域网访问: http://[本机IP]:8000
    - API文档: http://localhost:8000/docs
"""

import os
import sys
import subprocess


def check_dependencies():
    """检查依赖是否安装"""
    try:
        import fastapi
        import uvicorn
        import docx
        return True
    except ImportError:
        return False


def install_dependencies():
    """安装依赖"""
    print("正在安装依赖...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("依赖安装成功")
        return True
    except subprocess.CalledProcessError:
        print("依赖安装失败，请手动安装: pip install -r requirements.txt")
        return False


def start_server():
    """启动服务"""
    if not check_dependencies():
        if not install_dependencies():
            return

    print("\n=== 席卡生成服务 ===")
    print("服务将在后台运行")
    print("本地访问: http://localhost:8000")
    print("API文档: http://localhost:8000/docs")
    print("按 Ctrl+C 停止服务\n")

    try:
        from server import run_server
        run_server()
    except KeyboardInterrupt:
        print("\n服务已停止")
    except Exception as e:
        print(f"启动服务时出错: {e}")


if __name__ == "__main__":
    start_server()
