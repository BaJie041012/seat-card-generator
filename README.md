# 席卡生成系统

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-green)
![License](https://img.shields.io/badge/license-MIT-yellow)

自动化席卡生成系统，支持 AI 智能文本提取、多模板适配、批量生成 Word/PDF，提供 GUI / Web / API 三种使用方式。

## 功能特性

- **AI 智能提取** — 输入自然语言文本，AI 自动解析出姓名、公司、职位等结构化信息
- **多模板支持** — 内置 v4（详细占位符）和 v5（简化 `{text}`）两套模板，可按需扩展
- **批量生成** — 一次生成数十张席卡，自动转 PDF 并合并合集
- **质量验证** — 每张席卡生成后自动校验内容完整性，输出质量报告
- **三种使用方式** — 桌面 GUI（tkinter）、Web 界面（FastAPI）、RESTful API
- **局域网共享** — Web 服务监听局域网，同网段设备浏览器直接访问

## 快速开始

### 环境要求

- Python 3.8+
- Microsoft Word（用于 Word→PDF 转换，可选；无 Word 时使用 spire.doc 备选方案）

### 安装

```bash
git clone https://github.com/BaJie041012/seat-card-generator.git
cd seat-card-generator
pip install -r requirements.txt
```

### 配置 API 密钥

AI 功能需要设置环境变量 `MINIMAX_API_KEY`：

```bash
# Windows
set MINIMAX_API_KEY=your_api_key_here

# Linux / macOS
export MINIMAX_API_KEY=your_api_key_here
```

### 启动方式

**现代桌面版（推荐）：**

```bash
python -m app.desktop
```

**经典桌面 GUI：**

```bash
python scripts/main.py --gui
```

**Web 服务（端口 8000）：**

```bash
python scripts/start_server.py
```

启动后访问 `http://localhost:8000`，局域网设备用 `http://<本机IP>:8000` 访问。

## 模板说明

| 模板 | 占位符 | 字号 | 适用场景 |
|------|--------|------|----------|
| 席卡模板v4.docx | `{活动名称}` `{姓名/公司}` `{{name}}` `{{company}}` 等 | 姓名 72pt / 公司 36pt | 需要展示多字段 |
| 席卡模板v5.docx | `{text}` | 110pt 楷体 | 只需显示姓名/公司，大字号醒目 |

自定义模板：将 `.docx` 文件放入 `templates/` 目录，使用上述占位符标记替换位置即可。

## API 接口

服务启动后访问 `http://localhost:8000/docs` 查看自动生成的 Swagger 文档。

**生成席卡** — `POST /api/generate-cards`

```json
{
    "text": "张三，公司A，职位B；李四，公司C，职位D",
    "event_name": "公司年会",
    "display_type": "name",
    "template": "席卡模板v5.docx"
}
```

**获取模板列表** — `GET /api/templates`

**健康检查** — `GET /api/health`

## 项目结构

```
├── src/                        # 核心后端模块
│   ├── config.py               # 配置管理
│   ├── ai_service.py           # AI 服务（MiniMax）
│   ├── text_extractor.py       # AI 文本提取
│   ├── card_generator.py       # 席卡生成核心模块
│   └── template_processor.py   # 模板处理器
├── app/                        # 前端应用
│   ├── desktop.py              # 现代桌面版（CustomTkinter）
│   ├── gui.py                  # 经典桌面 GUI（tkinter）
│   └── server.py               # Web 服务（FastAPI）
├── scripts/                    # 启动脚本
│   ├── main.py                 # CLI 入口
│   └── start_server.py         # 服务启动脚本
├── templates/                  # 席卡模板目录
├── flutter_app/                # Flutter 跨平台应用
├── output/                     # 生成文件输出目录
└── requirements.txt            # Python 依赖
```

## 技术栈

- **后端** — Python 3.8+, FastAPI, uvicorn
- **前端** — 内嵌 HTML/CSS/JS Web 界面
- **桌面** — CustomTkinter（现代版）/ tkinter（经典版）
- **AI** — MiniMax API (MiniMax-M2.5)
- **文档处理** — python-docx, PyPDF2, reportlab
- **PDF 转换** — win32com (主) / spire.doc (备)

## 许可证

MIT License
