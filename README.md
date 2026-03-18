# 自动化文本处理与模板填充程序

[!\[Python\](https://img.shields.io/badge/Python-3.8+-blue.svg null)](https://www.python.org/)
[!\[License\](https://img.shields.io/badge/License-MIT-green.svg null)](LICENSE)

一款基于AI的智能文本处理与模板填充工具，支持从非结构化文本中提取人员信息，并自动生成席卡文档。

## 📋 目录

- [项目概述](#项目概述)
- [功能特性](#功能特性)
- [环境要求](#环境要求)
- [安装步骤](#安装步骤)
- [使用方法](#使用方法)
- [核心功能演示](#核心功能演示)
- [项目结构](#项目结构)
- [配置说明](#配置说明)
- [常见问题解答](#常见问题解答)
- [贡献指南](#贡献指南)
- [许可证](#许可证)

## 项目概述

本项目是一个自动化文本处理工具，主要解决以下问题：

1. **信息提取**：从格式不一的文本中智能提取姓名、单位、职位等结构化信息
2. **席卡生成**：根据提取的信息自动生成会议席卡文档
3. **模板填充**：支持多种格式的模板文件填充

### 应用场景

- 会议席卡批量生成
- 人员名单信息提取
- 模板文档自动填充
- 结构化数据导出

## 功能特性

### 🤖 AI智能提取

- 支持从非结构化文本中提取姓名、单位、职位
- 自动识别多种文本格式
- 高准确率的信息提取

### 📝 席卡生成

- 单人单文件模式，避免空白页问题
- 支持自定义活动名称
- 自动格式化两字姓名（插入全角空格）
- 字体格式自动设置（楷体）
- 字号智能调整（姓名72pt，公司名36pt）

### 📄 多格式支持

- 支持 `.docx` Word文档模板
- 支持 `.txt` 文本模板
- 支持 `.pdf` PDF模板（需安装reportlab）

### 🖥️ 图形界面

- 基于tkinter的友好界面
- 实时进度显示
- 质量验证与报告生成

### 📊 质量控制

- 自动检测空白页
- 内容完整性验证
- 详细的生成报告

## 环境要求

### 系统要求

- Windows 10/11
- macOS 10.14+
- Linux (Ubuntu 18.04+)

### Python版本

- Python 3.8 或更高版本

### 必需依赖

```
python-docx>=0.8.11
```

### 可选依赖

```
reportlab>=3.6.0  # PDF支持
```

## 安装步骤

### 1. 克隆仓库

```bash
git clone https://github.com/BaJie041012/printf.git
cd printf
```

### 2. 创建虚拟环境（推荐）

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install python-docx
```

如需PDF支持：

```bash
pip install reportlab
```

### 4. 配置API密钥

编辑 `config.py` 文件，设置您的AI服务API密钥：

```python
@dataclass
class AIConfig:
    api_key: str = "your-api-key-here"
    api_base_url: str = "https://api.minimaxi.com/v1"
    model: str = "MiniMax-M2.5"
```

## 使用方法

### 图形界面模式

```bash
python main.py --gui
```

或直接运行：

```bash
python main.py
```

### 命令行模式

```bash
# 查看帮助
python main.py --help

# 处理文本
python main.py --template template.docx --text "要处理的文本"

# 创建示例模板
python main.py --create-template sample.txt
```

### 席卡生成流程

1. **输入文本**：在左侧文本框中输入或粘贴人员名单
2. **设置活动名称**：在"席卡生成"区域输入活动名称
3. **选择显示内容**：选择显示"姓名"或"公司名"
4. **选择模板**：在右侧选择席卡模板文件（.docx格式）
5. **点击生成**：点击"生成"按钮开始生成席卡

## 核心功能演示

### 信息提取示例

**输入文本：**

```
欧阳伟    新疆生产建设兵团第八师副师长、石河子市人民政府副市长
郑鸿英    新疆生产建设兵团第八师石河子市政务服务和大数据局局长
```

**提取结果：**

| 姓名  | 单位                       | 职位              |
| --- | ------------------------ | --------------- |
| 欧阳伟 | 新疆生产建设兵团第八师              | 副师长、石河子市人民政府副市长 |
| 郑鸿英 | 新疆生产建设兵团第八师石河子市政务服务和大数据局 | 局长              |

### 席卡生成示例

**模板占位符：**

- `{活动名称}` - 显示活动名称（楷体，16pt）
- `{姓名/公司}` - 显示姓名或公司名（楷体，72pt/36pt）

**生成效果：**

- 两字姓名自动格式化为"姓　名"（中间插入全角空格）
- 公司名称使用36pt字号
- 姓名使用72pt字号

## 项目结构

```
printf/
├── __init__.py          # 包初始化模块
├── config.py            # 配置管理模块
├── ai_service.py        # AI服务接口模块
├── template_processor.py # 模板处理模块
├── text_extractor.py    # 文本提取模块
├── gui.py               # 图形界面模块
├── main.py              # 主程序入口
├── templates/           # 模板文件目录
│   └── 席卡模板v4.docx   # 席卡模板示例
└── output/              # 输出文件目录
    └── 席卡_活动名_时间戳/
        ├── 席卡_姓名_日期.docx
        ├── 席卡_姓名_日期.docx
        └── 生成报告.txt
```

## 配置说明

### AI服务配置

| 参数             | 说明       | 默认值                           |
| -------------- | -------- | ----------------------------- |
| `api_key`      | API访问密钥  | -                             |
| `api_base_url` | API服务地址  | `https://api.minimaxi.com/v1` |
| `model`        | AI模型名称   | `MiniMax-M2.5`                |
| `max_tokens`   | 最大token数 | `2000`                        |
| `temperature`  | 生成温度     | `0.7`                         |
| `timeout`      | 超时时间(秒)  | `30`                          |

### 模板配置

| 参数                  | 说明   | 默认值              |
| ------------------- | ---- | ---------------- |
| `template_dir`      | 模板目录 | `templates`      |
| `output_dir`        | 输出目录 | `output`         |
| `supported_formats` | 支持格式 | `docx, pdf, txt` |

## 常见问题解答

### Q1: 生成的席卡显示为空白页？

**A:** 请确保：

1. 模板文件中包含正确的占位符（如 `{姓名/公司}`）
2. 输入文本中包含可提取的人员信息
3. 查看生成报告中的错误信息

### Q2: 字体显示不正确？

**A:** 请确保系统中已安装相应字体：

- Windows: 检查 `C:\Windows\Fonts` 目录
- 常见中文字体：楷体(KaiTi)、宋体(SimSun)、黑体(SimHei)

### Q3: API调用失败？

**A:** 请检查：

1. API密钥是否正确配置
2. 网络连接是否正常
3. API服务是否可用

### Q4: 如何添加新的模板格式？

**A:** 参考 `template_processor.py` 中的处理器类，继承 `BaseTemplateProcessor` 并实现相应方法。

## 贡献指南

欢迎贡献代码、报告问题或提出建议！

### 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/BaJie041012/printf.git
cd printf

# 安装开发依赖
pip install -r requirements-dev.txt

# 运行测试
python -m pytest tests/
```

### 代码规范

- 遵循 PEP 8 编码规范
- 使用中文注释
- 为所有函数和类添加文档字符串

### 提交规范

```
feat: 添加新功能
fix: 修复bug
docs: 文档更新
style: 代码格式调整
refactor: 代码重构
test: 测试相关
```

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

***

**作者**: 戒者有八

**版本**: 1.0.0

**最后更新**: 2026-03-18
