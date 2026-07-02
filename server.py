# ==============================================================================
# 文件名称: server.py
# 功能描述: 网络服务模块，基于FastAPI提供HTTP接口供Flutter客户端和Web访问
# 创建日期: 2026-03-25
# 作    者: 戒者有八
# 版本: 2.0.0
# 描述: 基于FastAPI的HTTP服务，提供席卡生成的API接口和Web界面
# ==============================================================================
"""
网络服务模块 - 基于FastAPI的HTTP服务

本模块提供网络服务功能，包括:
    - RESTful API接口供Flutter客户端调用
    - Web界面供浏览器直接访问
    - 文件下载功能
    - 跨域支持(CORS)

使用方式:
    1. 启动服务: python start_server.py
    2. 访问Web界面: http://localhost:8000
    3. API文档: http://localhost:8000/docs
"""

import os
import sys
import uuid
import socket
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入项目模块
from config import CONFIG, ensure_directories
from ai_service import create_ai_service
from text_extractor import create_extractor
from card_generator import generate_cards

# ------------------------------------------------------------------------------
# FastAPI应用初始化
# ------------------------------------------------------------------------------
app = FastAPI(
    title="席卡生成服务",
    description="提供席卡生成的RESTful API接口",
    version="2.0.0"
)

# CORS中间件 - 允许Flutter客户端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 服务配置
SERVER_HOST = '0.0.0.0'
SERVER_PORT = 8000
REQUEST_TIMEOUT = 60

# 文件下载映射（UUID → 文件路径）
file_download_map: dict = {}

# 延迟初始化的服务实例
ai_service = None
extractor = None

# 确保目录存在
ensure_directories(CONFIG)


# ------------------------------------------------------------------------------
# 请求数据模型
# ------------------------------------------------------------------------------
class GenerateCardsRequest(BaseModel):
    """席卡生成请求"""
    text: str
    event_name: str = ""
    display_type: str = "name"
    template: str = "席卡模板v4.docx"


# ------------------------------------------------------------------------------
# 辅助函数
# ------------------------------------------------------------------------------
def get_local_ip() -> str:
    """获取本机局域网IP地址"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'


def _get_ai_service():
    """获取或初始化AI服务"""
    global ai_service, extractor
    if ai_service is None:
        if not CONFIG.ai.api_key:
            raise HTTPException(status_code=500, detail="AI服务API密钥未配置")
        ai_config = CONFIG.ai
        ai_config.timeout = REQUEST_TIMEOUT
        ai_service = create_ai_service(ai_config)
    if extractor is None:
        extractor = create_extractor(ai_service)
    return extractor


# ------------------------------------------------------------------------------
# Web界面
# ------------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def index():
    """主页面 - Web界面"""
    local_ip = get_local_ip()
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>席卡生成服务</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f5f5f5; color: #333; }}
        .header {{ background: #1976d2; color: white; padding: 20px; text-align: center; }}
        .header h1 {{ font-size: 24px; margin-bottom: 8px; }}
        .header p {{ opacity: 0.9; font-size: 14px; }}
        .container {{ max-width: 800px; margin: 20px auto; padding: 0 16px; }}
        .card {{ background: white; border-radius: 8px; padding: 20px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        .card h2 {{ font-size: 18px; margin-bottom: 16px; color: #1976d2; }}
        .form-group {{ margin-bottom: 16px; }}
        .form-group label {{ display: block; margin-bottom: 6px; font-weight: 600; font-size: 14px; }}
        .form-group input, .form-group select, .form-group textarea {{
            width: 100%; padding: 10px 12px; border: 1px solid #ddd; border-radius: 6px;
            font-size: 14px; transition: border-color 0.2s;
        }}
        .form-group input:focus, .form-group select:focus, .form-group textarea:focus {{
            outline: none; border-color: #1976d2;
        }}
        .form-group textarea {{ height: 120px; resize: vertical; font-family: inherit; }}
        .btn {{ display: inline-block; padding: 12px 32px; background: #1976d2; color: white;
                border: none; border-radius: 6px; font-size: 16px; cursor: pointer;
                transition: background 0.2s; }}
        .btn:hover {{ background: #1565c0; }}
        .btn:disabled {{ background: #bbb; cursor: not-allowed; }}
        .result {{ margin-top: 16px; padding: 16px; border-radius: 6px; }}
        .result.success {{ background: #e8f5e9; border-left: 4px solid #4caf50; }}
        .result.error {{ background: #ffebee; border-left: 4px solid #f44336; }}
        .result h3 {{ margin-bottom: 8px; }}
        .file-list {{ list-style: none; padding: 0; }}
        .file-list li {{ padding: 4px 0; }}
        .file-list a {{ color: #1976d2; text-decoration: none; }}
        .file-list a:hover {{ text-decoration: underline; }}
        .info {{ background: #e3f2fd; padding: 12px; border-radius: 6px; margin-bottom: 16px; font-size: 14px; }}
        .info code {{ background: #bbdefb; padding: 2px 6px; border-radius: 3px; }}
        .loading {{ display: inline-block; width: 20px; height: 20px; border: 3px solid rgba(0,0,0,.15);
                    border-radius: 50%; border-top-color: #1976d2; animation: spin 0.8s linear infinite;
                    vertical-align: middle; margin-left: 10px; }}
        @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
        .hidden {{ display: none; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>席卡生成服务</h1>
        <p>局域网访问: http://{local_ip}:{SERVER_PORT}</p>
    </div>
    <div class="container">
        <div class="info">
            API文档: <a href="/docs" style="color:#1976d2">/docs</a> |
            模板目录: {CONFIG.template.template_dir}
        </div>

        <div class="card">
            <h2>席卡生成</h2>
            <form id="cardForm">
                <div class="form-group">
                    <label for="text">人员信息文本</label>
                    <textarea id="text" name="text" placeholder="张三，公司A，职位B；李四，公司C，职位D"></textarea>
                </div>
                <div class="form-group">
                    <label for="event_name">活动名称</label>
                    <input type="text" id="event_name" name="event_name" placeholder="例如：公司年会">
                </div>
                <div class="form-group">
                    <label for="display_type">显示内容</label>
                    <select id="display_type" name="display_type">
                        <option value="name">姓名</option>
                        <option value="company">公司名</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="template">模板文件</label>
                    <select id="template" name="template"></select>
                </div>
                <div style="text-align:center">
                    <button type="submit" class="btn" id="submitBtn">生成席卡</button>
                    <span id="loadingIndicator" class="loading hidden"></span>
                </div>
            </form>
            <div id="result" class="hidden"></div>
        </div>
    </div>

    <script>
        // 加载模板列表
        fetch('/api/templates').then(r=>r.json()).then(data => {{
            if (data.success) {{
                const sel = document.getElementById('template');
                data.templates.forEach(t => {{
                    const opt = document.createElement('option');
                    opt.value = t; opt.textContent = t;
                    sel.appendChild(opt);
                }});
            }}
        }});

        // 表单提交
        document.getElementById('cardForm').addEventListener('submit', function(e) {{
            e.preventDefault();
            const btn = document.getElementById('submitBtn');
            const loading = document.getElementById('loadingIndicator');
            const result = document.getElementById('result');

            btn.disabled = true;
            loading.classList.remove('hidden');
            result.classList.add('hidden');

            const body = {{
                text: document.getElementById('text').value,
                event_name: document.getElementById('event_name').value,
                display_type: document.getElementById('display_type').value,
                template: document.getElementById('template').value
            }};

            fetch('/api/generate-cards', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify(body)
            }})
            .then(r => r.json())
            .then(data => {{
                btn.disabled = false;
                loading.classList.add('hidden');
                result.classList.remove('hidden');

                if (data.success) {{
                    result.className = 'result success';
                    let html = '<h3>生成成功</h3>';
                    html += '<p>共生成 ' + data.count + ' 个席卡</p>';
                    if (data.word_files && data.word_files.length) {{
                        html += '<p><strong>Word文件:</strong></p><ul class="file-list">';
                        data.word_files.forEach(f => {{
                            html += '<li><a href="/download/' + f.file_id + '" target="_blank">' + f.filename + '</a></li>';
                        }});
                        html += '</ul>';
                    }}
                    if (data.pdf_files && data.pdf_files.length) {{
                        html += '<p><strong>PDF文件:</strong></p><ul class="file-list">';
                        data.pdf_files.forEach(f => {{
                            html += '<li><a href="/download/' + f.file_id + '" target="_blank">' + f.filename + '</a></li>';
                        }});
                        html += '</ul>';
                    }}
                    if (data.pdf_combined_id) {{
                        html += '<p><a href="/download/' + data.pdf_combined_id + '" target="_blank">PDF合集</a></p>';
                    }}
                    if (data.failed && data.failed.length) {{
                        html += '<p style="color:#d32f2f">失败: ' + data.failed.join(', ') + '</p>';
                    }}
                    result.innerHTML = html;
                }} else {{
                    result.className = 'result error';
                    result.innerHTML = '<h3>生成失败</h3><p>' + (data.error || '未知错误') + '</p>';
                }}
            }})
            .catch(err => {{
                btn.disabled = false;
                loading.classList.add('hidden');
                result.classList.remove('hidden');
                result.className = 'result error';
                result.innerHTML = '<h3>请求出错</h3><p>请检查网络连接或服务状态</p>';
            }});
        }});
    </script>
</body>
</html>'''


# ------------------------------------------------------------------------------
# API路由
# ------------------------------------------------------------------------------
@app.get("/api/templates")
async def get_templates():
    """获取可用模板列表"""
    template_dir = CONFIG.template.template_dir
    templates = []
    if os.path.exists(template_dir):
        for f in os.listdir(template_dir):
            if f.endswith(('.txt', '.docx', '.pdf')):
                templates.append(f)
    return {"success": True, "templates": templates}


@app.get("/api/output")
async def get_output():
    """获取输出目录内容"""
    output_dir = CONFIG.template.output_dir
    files = []
    if os.path.exists(output_dir):
        for root, dirs, filenames in os.walk(output_dir):
            rel_path = os.path.relpath(root, output_dir)
            if rel_path == '.':
                rel_path = ''
            for filename in filenames:
                files.append({
                    "path": os.path.join(rel_path, filename),
                    "size": os.path.getsize(os.path.join(root, filename))
                })
    return {"success": True, "output_dir": output_dir, "files": files}


@app.post("/api/generate-cards")
async def api_generate_cards(req: GenerateCardsRequest):
    """生成席卡 - 核心API"""
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="请提供人员信息文本")

    # 获取AI提取器
    ext = _get_ai_service()

    # 模板路径
    template_path = os.path.join(CONFIG.template.template_dir, req.template)
    if not os.path.exists(template_path):
        raise HTTPException(status_code=404, detail=f"模板文件不存在: {req.template}")

    ext_ok = os.path.splitext(template_path)[1].lower()
    if ext_ok not in ['.docx', '.doc']:
        raise HTTPException(status_code=400, detail="席卡生成功能仅支持.docx格式的模板文件")

    try:
        # AI提取人员信息
        infos = ext.extract_from_text(req.text)
        if not infos:
            raise HTTPException(status_code=400, detail="未能提取到人员信息")

        # 调用共享模块生成席卡
        result = generate_cards(
            infos=infos,
            template_path=template_path,
            event_name=req.event_name,
            display_type=req.display_type,
            output_base_dir=CONFIG.template.output_dir
        )

        if not result.get('success'):
            raise HTTPException(status_code=500, detail=result.get('error', '生成失败'))

        # 为文件生成下载ID
        download_files = []
        pdf_files_info = []

        for file in result.get('files', []):
            file_id = str(uuid.uuid4())
            file_download_map[file_id] = file['filepath']

            file_info = {
                "filename": file['filename'],
                "file_id": file_id,
                "type": "word"
            }

            if file.get('pdf_filepath'):
                pdf_file_id = str(uuid.uuid4())
                file_download_map[pdf_file_id] = file['pdf_filepath']
                file_info["pdf_filename"] = os.path.basename(file['pdf_filepath'])
                file_info["pdf_file_id"] = pdf_file_id
                pdf_files_info.append({
                    "filename": os.path.basename(file['pdf_filepath']),
                    "file_id": pdf_file_id
                })

            download_files.append(file_info)

        # 报告和合集的下载ID
        report_id = None
        if result.get('report_path'):
            report_id = str(uuid.uuid4())
            file_download_map[report_id] = result['report_path']

        pdf_combined_id = None
        if result.get('pdf_combined_path'):
            pdf_combined_id = str(uuid.uuid4())
            file_download_map[pdf_combined_id] = result['pdf_combined_path']

        return {
            "success": True,
            "count": result['count'],
            "output_dir": result['output_dir'],
            "word_dir": result.get('word_dir', ''),
            "pdf_dir": result.get('pdf_dir', ''),
            "word_files": download_files,
            "pdf_files": pdf_files_info,
            "failed": result.get('failed', []),
            "report_id": report_id,
            "pdf_combined_id": pdf_combined_id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/download/{file_id}")
async def download_file(file_id: str):
    """下载文件"""
    if file_id not in file_download_map:
        raise HTTPException(status_code=404, detail="文件不存在或已过期")

    full_path = file_download_map[file_id]
    if not os.path.isfile(full_path):
        del file_download_map[file_id]
        raise HTTPException(status_code=404, detail="文件不存在")

    return FileResponse(full_path, filename=os.path.basename(full_path))


@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "time": datetime.now().isoformat()}


# ------------------------------------------------------------------------------
# 启动服务
# ------------------------------------------------------------------------------
def run_server(host=SERVER_HOST, port=SERVER_PORT):
    """启动FastAPI服务"""
    import uvicorn

    local_ip = get_local_ip()
    print(f"\n=== 席卡生成服务 ===")
    print(f"本地访问: http://localhost:{port}")
    print(f"局域网访问: http://{local_ip}:{port}")
    print(f"API文档: http://localhost:{port}/docs")
    print(f"\n按 Ctrl+C 停止服务\n")

    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == '__main__':
    run_server()
