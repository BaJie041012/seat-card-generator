# 席卡生成系统

![Flutter](https://img.shields.io/badge/Flutter-3.12+-02569B?logo=flutter)
![Python](https://img.shields.io/badge/Python-3.8+-3776AB?logo=python)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Platform](https://img.shields.io/badge/Platform-Android-green)

自动化席卡生成系统。输入自然语言文本，AI 自动解析人员信息，一键生成 A4 席卡 PDF。支持 Android APK 本地独立运行，也提供 Python 后端 + Web / GUI 多种使用方式。

## 功能特性

- **AI 智能提取** — 输入自然语言文本，AI 自动解析出姓名、公司、职位等结构化信息
- **本地 PDF 生成** — APK 端完全离线生成 A4 席卡 PDF，无需连接任何服务器
- **内置中文字体** — 打包 Noto Sans SC 字体，确保中文渲染正确
- **批量生成** — 一次生成数十张席卡，自动输出单张 PDF 与合并合集
- **多种显示** — 支持按姓名 / 公司名切换显示，两字姓名自动加全角空格
- **系统分享** — 生成的 PDF 可直接通过系统分享或调用阅读器打开
- **多种使用方式** — Android APK（推荐）、桌面 GUI、Web 界面、RESTful API
- **局域网共享** — Web 服务监听局域网，同网段设备浏览器直接访问

## 快速开始

### Android APK（推荐）

从 [Releases](https://github.com/BaJie041012/seat-card-generator/releases) 页面下载最新 APK 安装即可。

1. 安装 APK，打开应用
2. API Key 已内置，可直接使用；如需更换，点击右上角设置
3. 输入人员信息（支持多种格式），填写活动名称（可选）
4. 选择显示内容（姓名 / 公司名），点击「生成席卡」
5. 生成完成后直接打开或分享 PDF 文件

**支持的输入格式示例：**

```
张三    北京科技有限公司    高级工程师
李四，上海数据科技集团，产品经理
王五 - 深圳创新科技 - 技术总监
新疆生产建设兵团第八师副师长 欧阳伟
```

### Python 后端

```bash
git clone https://github.com/BaJie041012/seat-card-generator.git
cd seat-card-generator
pip install -r requirements.txt
```

配置环境变量：

```bash
# Windows
set MINIMAX_API_KEY=your_api_key_here

# Linux / macOS
export MINIMAX_API_KEY=your_api_key_here
```

**桌面 GUI（推荐）：**

```bash
python -m app.desktop
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
├── app/                        # 前端应用（Python）
│   ├── desktop.py              # 现代桌面版（CustomTkinter）
│   ├── gui.py                  # 经典桌面 GUI（tkinter）
│   └── server.py               # Web 服务（FastAPI）
├── scripts/                    # 启动脚本
│   ├── main.py                 # CLI 入口
│   └── start_server.py         # 服务启动脚本
├── flutter_app/                # Flutter 跨平台应用（Android APK）
│   ├── lib/
│   │   ├── main.dart           # 应用入口
│   │   ├── models/
│   │   │   └── card_models.dart    # 数据模型
│   │   ├── services/
│   │   │   ├── minimax_service.dart    # MiniMax AI 直连服务
│   │   │   ├── card_generator.dart     # 本地 PDF 生成服务
│   │   │   └── settings_service.dart   # 设置持久化服务
│   │   └── pages/
│   │       ├── home_page.dart      # 主页
│   │       ├── settings_page.dart  # 设置页
│   │       └── result_page.dart    # 结果页
│   └── assets/fonts/           # 内置中文字体
├── templates/                  # 席卡模板目录
├── releases/                   # 发布版本归档
├── output/                     # 生成文件输出目录
└── requirements.txt            # Python 依赖
```

## 技术栈

| 端 | 技术 |
|----|------|
| Android APK | Flutter 3.12+ / Dart 3.x / Material 3 |
| 后端 | Python 3.8+ / FastAPI / uvicorn |
| 桌面 GUI | CustomTkinter（现代版）/ tkinter（经典版） |
| AI | MiniMax API (MiniMax-M2.5) |
| PDF 生成 | `pdf` 包（APK 端）/ reportlab + python-docx（Python 端） |
| 中文字体 | Noto Sans SC |

## 构建

### Android APK

```bash
cd flutter_app
flutter build apk --release
```

构建产物位于 `build/app/outputs/flutter-apk/app-release.apk`。

### Python EXE

```bash
pyinstaller --onefile --windowed --add-data "templates;templates" scripts/main.py
```

## 许可证

[MIT License](LICENSE)

## 作者

戒者有八
