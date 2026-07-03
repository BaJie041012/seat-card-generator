# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.0.0] - 2026-07-03

### Changed
- **APK 从 Flutter 迁移至原生 Kotlin**：彻底移除 Flutter 依赖，APK 从 64MB 缩减至 3.3MB（减少 95%）
- **PDF 布局复刻 Python 模板**：复刻 Python 端 Word 模板的折叠桌牌布局（A4 横向、左右对称、折痕线）
  - v4 模板：活动名称 16pt + 姓名 72pt/公司 36pt
  - v5 模板：姓名 110pt 大字体居中
  - 两字姓名自动插全角空格（复刻 Python `format_name` 逻辑）
- **新增模板选择**：支持 v4 详细模板 / v5 简洁模板切换
- **AI 集成完整**：MiniMax API 直连，3 次重试 + 指数退避 + fallback 本地解析

### Technical
- 原生 Kotlin + Android SDK，无第三方 UI 框架
- Material 3 设计语言
- PDF 生成：Android PdfDocument API
- AI：MiniMax-M2.5（OpenAI 兼容格式）
- 网络：OkHttp 4.12
- 构建：AGP 8.5.0 / Gradle 8.7 / Kotlin 2.0.0

---

## [2.0.2] - 2026-07-03

### Changed
- **APK 体积优化**：从 64MB 缩减至 21MB（减少 67%）
  - 字体子集化：Noto Sans SC 从 16.95MB 缩减至 1.78MB（保留 GB2312 常用汉字）
  - 仅打包 arm64-v8a 架构，移除 x86_64 和 armeabi-v7a
  - 启用 R8 全模式代码压缩与资源缩减

---

## [2.0.1] - 2026-07-03

### Changed
- **Python 端内置 API Key**：`config.py` 嵌入默认 API Key，EXE 开箱即用，无需手动配置环境变量
- **EXE 重新构建**：基于 v2.0.0 代码重新打包 Windows EXE

---

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
