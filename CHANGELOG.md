# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-07-03

### Added
- **完全自包含 Flutter APK**：无需服务器，AI 识别与 PDF 生成全部在手机本地完成
- **MiniMax API 直连**：Dart 端直接调用 MiniMax API，复刻 Python 端 `ai_service.py` + `text_extractor.py` 全部逻辑
- **本地 PDF 生成**：使用 `pdf` 包在设备上直接生成 A4 席卡 PDF，支持单张与合集
- **内置中文字体**：打包 Noto Sans SC 字体资源，确保 PDF 中文渲染正确
- **设置持久化**：基于 `shared_preferences` 持久存储 API Key / API 地址 / 模型名称
- **文件分享与打开**：支持系统级分享 PDF 文件、调用系统阅读器打开
- **内置默认 API Key**：首次使用无需手动配置，开箱即用

### Changed
- **架构重构**：从服务器-客户端模式转为完全本地独立运行模式
- **UI 升级**：Material 3 设计语言，支持亮色/暗色系统主题跟随
- **显示模式**：新增按姓名/公司名切换显示的分段按钮
- **版本升级**：pubspec.yaml 版本升至 2.0.0+2

### Removed
- 移除对后端服务器（`api_service.dart`）的依赖
- 移除局域网共享模式的相关引用

### Technical
- Flutter 3.12+ / Dart 3.x
- 依赖：`pdf ^3.11.1`, `http ^1.2.0`, `path_provider ^2.1.4`, `shared_preferences ^2.3.3`, `share_plus ^10.1.2`, `open_filex ^4.5.0`
- 构建产物：64MB release APK（含中文字体）
- AI 模型：MiniMax-M2.5

---

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
