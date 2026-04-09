# 文本处理与席卡生成程序

![Python](https://img.shields.io/badge/python-3.7%2B-blue)
![Flask](https://img.shields.io/badge/flask-2.0%2B-green)
![License](https://img.shields.io/badge/license-MIT-yellow)
![Last Commit](https://img.shields.io/github/last-commit/BaJie041012/printf)

## 项目介绍

本项目是一个功能强大的自动化文本处理与席卡生成程序，支持从文本中提取人员信息并生成席卡文档。通过内置的网络服务模块，您可以在本地部署并允许同一网段内的其他设备访问，实现多设备协作。

### 核心功能

- **席卡生成**：根据输入的人员信息，自动生成席卡文档，支持批量处理
- **AI智能提取**：使用AI服务从文本中提取人员信息（姓名、公司、职位）
- **模板管理**：支持多种模板格式（docx、pdf、txt），可自定义模板
- **格式转换**：自动将生成的Word文档转换为PDF格式
- **PDF合并**：将多个PDF文件合并为一个合集，方便打印
- **质量报告**：生成详细的席卡生成质量报告，包含成功和失败记录
- **网络服务**：提供HTTP接口，支持同一网段内的设备访问
- **Web界面**：提供直观的Web界面，方便操作和查看
- **API接口**：支持席卡生成、模板列表获取等API
- **文件下载**：支持生成文件的在线下载

## 快速开始

### 环境要求

- Python 3.7 或更高版本
- pip 包管理工具
- （可选）Microsoft Word（用于PDF转换）

### 安装依赖

1. 克隆项目仓库：

```bash
git clone https://github.com/BaJie041012/printf.git
cd printf
```

2. 安装依赖包：

```bash
pip install -r requirements.txt
```

### 本地运行

启动图形界面：

```bash
python main.py
```

### 启动Web服务

```bash
python start_server.py
```

服务启动后，会显示以下信息：

```
=== 文本处理与席卡生成服务 ===
服务启动中...
本地访问地址: http://localhost:5000
局域网访问地址: http://192.168.2.157:5000

按 Ctrl+C 停止服务
```

### 访问服务

1. **本地访问**：在浏览器中打开 `http://localhost:5000`
2. **局域网访问**：在同一网段的其他设备上，打开浏览器访问 `http://[本机IP]:5000`

## 使用指南

### 本地GUI使用

1. **输入人员信息**：在左侧文本框中输入人员信息，每行一条
2. **设置活动信息**：填写活动名称，选择席卡显示内容（姓名或公司名）
3. **选择模板**：在右侧模板选择下拉框中选择席卡模板
4. **生成席卡**：点击「生成席卡」按钮，等待生成完成
5. **查看结果**：在输出区域查看生成结果
6. **操作文件**：使用「打开输出目录」查看生成的文件，或使用「复制结果」复制生成信息

### Web界面使用

1. **访问Web界面**：打开浏览器访问服务地址
2. **输入人员信息**：在文本框中输入人员信息
3. **设置参数**：填写活动名称，选择显示内容和模板
4. **生成席卡**：点击「生成席卡」按钮
5. **下载文件**：生成完成后，点击文件链接下载生成的席卡

## API接口

### 1. 席卡生成

**POST** `/api/generate-cards`

**请求参数**：

| 参数 | 类型 | 描述 | 必需 |
|------|------|------|------|
| text | string | 人员信息文本 | 是 |
| event_name | string | 活动名称 | 否 |
| display_type | string | 显示内容 (name/company) | 否 |
| template | string | 模板文件名 | 否 |

**示例请求**：

```json
{
    "text": "张三，公司A，职位B；李四，公司C，职位D",
    "event_name": "公司年会",
    "display_type": "name",
    "template": "席卡模板v4.docx"
}
```

**响应**：

```json
{
    "success": true,
    "count": 2,
    "output_dir": "output/席卡_公司年会_20260325_123456",
    "word_dir": "output/席卡_公司年会_20260325_123456/word",
    "pdf_dir": "output/席卡_公司年会_20260325_123456/pdf",
    "word_files": [
        {
            "filename": "席卡_张三_20260325.docx",
            "file_id": "uuid",
            "type": "word"
        },
        {
            "filename": "席卡_李四_20260325.docx",
            "file_id": "uuid",
            "type": "word"
        }
    ],
    "pdf_files": [
        {
            "filename": "席卡_张三_20260325.pdf",
            "file_id": "uuid"
        },
        {
            "filename": "席卡_李四_20260325.pdf",
            "file_id": "uuid"
        }
    ],
    "failed": [],
    "report_id": "uuid",
    "pdf_combined_id": "uuid"
}
```

### 2. 获取模板列表

**GET** `/api/templates`

**响应**：

```json
{
    "success": true,
    "templates": ["席卡模板v4.docx", "name_list_template.txt"]
}
```

### 3. 获取输出目录

**GET** `/api/output`

**响应**：

```json
{
    "success": true,
    "output_dir": "output",
    "files": [
        {
            "path": "席卡_公司年会_20260325_123456/席卡_张三_20260325.docx",
            "size": 12345
        }
    ]
}
```

## 配置说明

### AI服务配置

在 `config.py` 文件中配置AI服务参数：

```python
@dataclass
class AIConfig:
    api_key: str = "你的API密钥"  # AI服务API密钥
    api_base_url: str = "https://api.minimaxi.com/v1"  # API服务地址
    model: str = "MiniMax-M2.5"  # 使用的AI模型
    max_tokens: int = 2000  # 最大token数量
    temperature: float = 0.7  # 生成温度
    timeout: int = 30  # 请求超时时间(秒)
```

### 网络服务配置

在 `server.py` 文件中配置网络服务参数：

```python
# 服务配置
SERVER_HOST = '0.0.0.0'  # 监听所有网络接口
SERVER_PORT = 5000  # 默认端口
```

## 防火墙设置

为了确保同一网段内的设备能够访问服务，需要确保防火墙允许端口 `5000` 的入站连接。

### Windows系统

1. 打开「控制面板」→「系统和安全」→「Windows Defender 防火墙」
2. 点击「高级设置」
3. 点击「入站规则」→「新建规则」
4. 选择「端口」→「下一步」
5. 选择「TCP」，输入「5000」作为特定本地端口→「下一步」
6. 选择「允许连接」→「下一步」
7. 选择适用的网络类型→「下一步」
8. 输入规则名称（如「文本处理服务」）→「完成」

### Linux系统

```bash
sudo ufw allow 5000/tcp
```

## 常见问题

### 1. 服务无法启动

- 检查端口是否被占用：`netstat -ano | findstr :5000`
- 检查依赖是否安装：`pip install -r requirements.txt`
- 检查AI服务API密钥是否配置

### 2. 局域网设备无法访问

- 检查防火墙是否允许端口5000
- 检查设备是否在同一网段
- 检查本机IP地址是否正确

### 3. 席卡生成失败

- 检查模板文件是否存在
- 检查AI服务是否可用
- 检查输入文本是否包含有效的人员信息

### 4. PDF转换失败

- 检查是否安装了Microsoft Word
- 检查是否安装了spire.doc库
- 检查文件路径是否有特殊字符

## 项目结构

```
├── server.py          # 网络服务模块
├── start_server.py    # 启动脚本
├── main.py            # 主程序入口
├── gui.py             # GUI界面
├── config.py          # 配置管理
├── ai_service.py      # AI服务
├── template_processor.py  # 模板处理
├── text_extractor.py  # 文本提取
├── requirements.txt   # 依赖文件
├── templates/         # 模板目录
└── output/            # 输出目录
```

## 技术栈

- **后端**：Python 3.7+, Flask
- **前端**：HTML5, CSS3, JavaScript
- **AI服务**：MiniMax API
- **文档处理**：python-docx, PyPDF2
- **网络**：Flask, socket

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 贡献

欢迎提交 Issue 和 Pull Request 来改进这个项目！

## GitHub地址

[https://github.com/BaJie041012/printf](https://github.com/BaJie041012/printf)
