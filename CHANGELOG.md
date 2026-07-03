# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-07-03

### Added
- 初始版本发布
- AI 智能文本提取（MiniMax API）
- 多模板支持（v4 详细版 / v5 简洁版）
- 批量生成 Word/PDF 席卡
- 质量验证与报告
- 三种使用方式：桌面 GUI、Web 界面、RESTful API
- 局域网共享支持
- Flutter 跨平台客户端（Android / Windows）

### Technical
- 后端：Python 3.8+ / FastAPI / uvicorn
- 桌面端：tkinter GUI + PyInstaller 打包
- 移动端/桌面端：Flutter 3.12+
- AI：MiniMax-M2.5
- 文档处理：python-docx / PyPDF2 / reportlab
