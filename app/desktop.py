# ==============================================================================
# 席卡生成系统 - 桌面版
# 基于 CustomTkinter 的现代 GUI，连接现有后端模块
# ==============================================================================

import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk

# 兼容 PyInstaller 打包后的路径
if getattr(sys, 'frozen', False):
    # PyInstaller 打包后：exe 所在目录即项目根
    _BASE = os.path.dirname(sys.executable)
else:
    # 开发模式：app/ 的上一级即项目根
    _BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 确保能导入 src/ 下的后端模块
for _p in (_BASE, os.path.join(_BASE, 'src')):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from config import CONFIG, AIConfig, TemplateConfig, ensure_directories
from ai_service import create_ai_service
from text_extractor import create_extractor
from card_generator import generate_cards


# ── 主题 & 外观 ─────────────────────────────────────────────────────────────
ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")

APP_TITLE = "席卡生成系统"
APP_VERSION = "2.0.0"
APP_SIZE = ("1000", "700")


# ── 主窗口 ──────────────────────────────────────────────────────────────────
class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(APP_TITLE)
        self.geometry(f"{APP_SIZE[0]}x{APP_SIZE[1]}")
        self.minsize(800, 550)

        # 服务实例
        self.ai_service = None
        self.ai_extractor = None
        self.current_template_path = ""

        # 初始化目录
        ensure_directories(CONFIG)

        # 构建界面
        self._build_ui()
        self._refresh_templates()

    # ── 布局 ────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # 顶栏
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=(12, 0))

        ctk.CTkLabel(
            top, text=APP_TITLE,
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(side="left")

        ctk.CTkButton(
            top, text="⚙ 设置", width=80,
            command=self._open_settings,
        ).pack(side="right")

        # 主体：左右分栏
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=16, pady=12)
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        # ── 左栏：输入 ──────────────────────────────────────────────────────
        left = ctk.CTkFrame(body)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        left.grid_rowconfigure(1, weight=1)
        left.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(left, text="人员信息输入", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, sticky="w", pady=(8, 4), padx=12
        )

        self.input_box = ctk.CTkTextbox(left, wrap="word", font=ctk.CTkFont(size=14))
        self.input_box.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 8))

        # 设置区
        settings_box = ctk.CTkFrame(left)
        settings_box.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 12))
        settings_box.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(settings_box, text="活动名称:").grid(
            row=0, column=0, sticky="w", pady=6, padx=(8, 4)
        )
        self.event_var = ctk.StringVar(value="")
        ctk.CTkEntry(settings_box, textvariable=self.event_var, placeholder_text="可选").grid(
            row=0, column=1, sticky="ew", pady=6, padx=(0, 8)
        )

        ctk.CTkLabel(settings_box, text="显示内容:").grid(
            row=1, column=0, sticky="w", pady=(0, 6), padx=(8, 4)
        )
        display_frame = ctk.CTkFrame(settings_box, fg_color="transparent")
        display_frame.grid(row=1, column=1, sticky="w", pady=(0, 6), padx=(0, 8))
        self.display_var = ctk.StringVar(value="name")
        ctk.CTkRadioButton(display_frame, text="姓名", variable=self.display_var, value="name").pack(side="left", padx=8)
        ctk.CTkRadioButton(display_frame, text="公司名", variable=self.display_var, value="company").pack(side="left", padx=8)

        # ── 右栏：输出 ──────────────────────────────────────────────────────
        right = ctk.CTkFrame(body)
        right.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        right.grid_rowconfigure(2, weight=1)
        right.grid_columnconfigure(0, weight=1)

        # 模板选择
        tpl_frame = ctk.CTkFrame(right)
        tpl_frame.grid(row=0, column=0, sticky="ew", pady=(8, 4), padx=12)
        tpl_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(tpl_frame, text="模板:").grid(row=0, column=0, padx=(0, 6))
        self.template_var = ctk.StringVar(value="")
        self.template_menu = ctk.CTkOptionMenu(
            tpl_frame, variable=self.template_var,
            command=self._on_template_selected,
        )
        self.template_menu.grid(row=0, column=1, sticky="ew", padx=(0, 6))
        ctk.CTkButton(tpl_frame, text="浏览", width=60, command=self._browse_template).grid(
            row=0, column=2
        )

        # 操作按钮
        btn_frame = ctk.CTkFrame(right, fg_color="transparent")
        btn_frame.grid(row=1, column=0, sticky="ew", pady=4, padx=12)

        self.gen_btn = ctk.CTkButton(
            btn_frame, text="生成席卡", height=38,
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self._generate,
        )
        self.gen_btn.pack(fill="x", pady=(4, 2))

        action_row = ctk.CTkFrame(btn_frame, fg_color="transparent")
        action_row.pack(fill="x", pady=(2, 4))
        ctk.CTkButton(
            action_row, text="打开输出目录", width=140,
            command=self._open_output_dir,
        ).pack(side="left", padx=(0, 6))
        ctk.CTkButton(
            action_row, text="复制结果", width=140,
            command=self._copy_result,
        ).pack(side="left")

        # 结果文本
        self.output_box = ctk.CTkTextbox(right, wrap="word", state="disabled", font=ctk.CTkFont(size=13))
        self.output_box.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 8))

        # 底部状态栏
        self.status_var = ctk.StringVar(value="就绪")
        self.status_bar = ctk.CTkLabel(
            self, textvariable=self.status_var,
            height=28, font=ctk.CTkFont(size=12),
        )
        self.status_bar.pack(fill="x", padx=16, pady=(0, 8))

        # 进度条
        self.progress = ctk.CTkProgressBar(self)
        self.progress.set(0)
        self.progress.pack(fill="x", padx=16, pady=(0, 4))

    # ── 模板 ────────────────────────────────────────────────────────────────
    def _refresh_templates(self):
        tpl_dir = CONFIG.template.template_dir
        if not os.path.isdir(tplDir := tpl_dir):
            return
        files = [f for f in os.listdir(tplDir) if f.lower().endswith(('.docx', '.txt', '.pdf'))]
        if files:
            self.template_menu.configure(values=files)
            if not self.template_var.get():
                self.template_var.set(files[0])
                self._on_template_selected(files[0])

    def _on_template_selected(self, name):
        self.current_template_path = os.path.join(CONFIG.template.template_dir, name)

    def _browse_template(self):
        path = filedialog.askopenfilename(
            title="选择模板",
            filetypes=[("支持格式", "*.docx;*.txt;*.pdf"), ("所有文件", "*.*")],
        )
        if path:
            self.current_template_path = path
            self.template_var.set(os.path.basename(path))

    # ── 生成 ────────────────────────────────────────────────────────────────
    def _check_ai(self):
        if self.ai_service is None:
            if not CONFIG.ai.api_key:
                self._open_settings()
                return False
            self.ai_service = create_ai_service()
        if self.ai_extractor is None:
            self.ai_extractor = create_extractor(self.ai_service)
        else:
            self.ai_extractor.set_ai_service(self.ai_service)
        return True

    def _generate(self):
        text = self.input_box.get("0.0", "end").strip()
        if not text:
            messagebox.showwarning("提示", "请输入人员信息文本")
            return
        if not self._check_ai():
            return
        if not self.current_template_path:
            messagebox.showwarning("提示", "请先选择模板")
            return
        if not self.current_template_path.lower().endswith('.docx'):
            messagebox.showwarning("提示", "席卡生成仅支持 .docx 模板")
            return

        self.gen_btn.configure(state="disabled", text="生成中...")
        self.progress.set(0)
        self.status_var.set("正在生成席卡...")

        event_name = self.event_var.get().strip()
        display_type = self.display_var.get()
        template_path = self.current_template_path

        def worker():
            try:
                self.after(0, lambda: self.progress.set(0.2))
                infos = self.ai_extractor.extract_from_text(text)
                if not infos:
                    self.after(0, lambda: messagebox.showwarning("提示", "未提取到人员信息"))
                    return
                self.after(0, lambda: self.progress.set(0.5))
                result = generate_cards(
                    infos=infos,
                    template_path=template_path,
                    event_name=event_name,
                    display_type=display_type,
                    output_base_dir=CONFIG.template.output_dir,
                )
                self.after(0, lambda: self.progress.set(1.0))
                self.after(0, lambda: self._show_result(result))
            except Exception as e:
                self.after(0, lambda: self._show_error(str(e)))
            finally:
                self.after(0, lambda: self.gen_btn.configure(state="normal", text="生成席卡"))

        threading.Thread(target=worker, daemon=True).start()

    def _show_result(self, result):
        self.output_box.configure(state="normal")
        self.output_box.delete("0.0", "end")
        if result.get("success"):
            valid = [f for f in result["files"] if f.get("valid")]
            invalid = [f for f in result["files"] if not f.get("valid")]
            lines = [
                f"生成完成",
                f"{'─' * 36}",
                f"输出目录: {result['output_dir']}",
                f"成功: {len(valid)} 个",
            ]
            if invalid:
                lines.append(f"验证失败: {len(invalid)} 个")
            lines.append("")
            for f in result["files"]:
                mark = "OK" if f.get("valid") else "NG"
                lines.append(f"  [{mark}] {f['filename']}")
            if result.get("failed"):
                lines.append(f"\n失败: {', '.join(result['failed'])}")
            lines.append(f"\n质量报告: {result.get('report_path', '')}")
            self.output_box.insert("end", "\n".join(lines))
            self.status_var.set(f"完成，共 {len(valid)} 个有效文件")
        else:
            self.output_box.insert("end", f"错误: {result.get('error', '未知错误')}")
            self.status_var.set("生成失败")
        self.output_box.configure(state="disabled")

    def _show_error(self, msg):
        self.output_box.configure(state="normal")
        self.output_box.delete("0.0", "end")
        self.output_box.insert("end", f"错误: {msg}")
        self.output_box.configure(state="disabled")
        self.progress.set(0)
        self.status_var.set("出错")

    # ── 辅助 ────────────────────────────────────────────────────────────────
    def _open_output_dir(self):
        d = CONFIG.template.output_dir
        if os.path.isdir(d):
            os.startfile(d)

    def _copy_result(self):
        content = self.output_box.get("0.0", "end").strip()
        if not content:
            return
        self.clipboard_clear()
        self.clipboard_append(content)
        self.status_var.set("结果已复制")

    # ── 设置对话框 ──────────────────────────────────────────────────────────
    def _open_settings(self):
        SettingsDialog(self)


class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("设置")
        self.geometry("480x380")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        pad = {"padx": 16, "pady": 8}

        # API Key
        ctk.CTkLabel(self, text="MiniMax API Key:").grid(row=0, column=0, sticky="w", **pad)
        self.api_key = ctk.CTkEntry(self, width=320, show="*")
        self.api_key.grid(row=0, column=1, sticky="ew", **pad)
        self.api_key.insert(0, CONFIG.ai.api_key)

        # API URL
        ctk.CTkLabel(self, text="API 地址:").grid(row=1, column=0, sticky="w", **pad)
        self.api_url = ctk.CTkEntry(self, width=320)
        self.api_url.grid(row=1, column=1, sticky="ew", **pad)
        self.api_url.insert(0, CONFIG.ai.api_base_url)

        # Model
        ctk.CTkLabel(self, text="模型:").grid(row=2, column=0, sticky="w", **pad)
        self.model = ctk.CTkEntry(self, width=320)
        self.model.grid(row=2, column=1, sticky="ew", **pad)
        self.model.insert(0, CONFIG.ai.model)

        # Max Tokens
        ctk.CTkLabel(self, text="Max Tokens:").grid(row=3, column=0, sticky="w", **pad)
        self.max_tokens = ctk.CTkEntry(self, width=320)
        self.max_tokens.grid(row=3, column=1, sticky="ew", **pad)
        self.max_tokens.insert(0, str(CONFIG.ai.max_tokens))

        # Temperature
        ctk.CTkLabel(self, text="Temperature:").grid(row=4, column=0, sticky="w", **pad)
        self.temperature = ctk.CTkEntry(self, width=320)
        self.temperature.grid(row=4, column=1, sticky="ew", **pad)
        self.temperature.insert(0, str(CONFIG.ai.temperature))

        # Timeout
        ctk.CTkLabel(self, text="超时(秒):").grid(row=5, column=0, sticky="w", **pad)
        self.timeout = ctk.CTkEntry(self, width=320)
        self.timeout.grid(row=5, column=1, sticky="ew", **pad)
        self.timeout.insert(0, str(CONFIG.ai.timeout))

        # 模板目录
        ctk.CTkLabel(self, text="模板目录:").grid(row=6, column=0, sticky="w", **pad)
        tpl_frame = ctk.CTkFrame(self, fg_color="transparent")
        tpl_frame.grid(row=6, column=1, sticky="ew", **pad)
        tpl_frame.grid_columnconfigure(0, weight=1)
        self.tpl_dir = ctk.CTkEntry(tpl_frame, width=260)
        self.tpl_dir.grid(row=0, column=0, sticky="ew")
        self.tpl_dir.insert(0, CONFIG.template.template_dir)
        ctk.CTkButton(tpl_frame, text="…", width=30, command=lambda: self._browse(self.tpl_dir)).grid(row=0, column=1, padx=(4, 0))

        # 输出目录
        ctk.CTkLabel(self, text="输出目录:").grid(row=7, column=0, sticky="w", **pad)
        out_frame = ctk.CTkFrame(self, fg_color="transparent")
        out_frame.grid(row=7, column=1, sticky="ew", **pad)
        out_frame.grid_columnconfigure(0, weight=1)
        self.out_dir = ctk.CTkEntry(out_frame, width=260)
        self.out_dir.grid(row=0, column=0, sticky="ew")
        self.out_dir.insert(0, CONFIG.template.output_dir)
        ctk.CTkButton(out_frame, text="…", width=30, command=lambda: self._browse(self.out_dir)).grid(row=0, column=1, padx=(4, 0))

        self.grid_columnconfigure(1, weight=1)

        # 按钮
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=8, column=0, columnspan=2, pady=16)
        ctk.CTkButton(btn_frame, text="保存", width=100, command=self._save).pack(side="left", padx=8)
        ctk.CTkButton(btn_frame, text="取消", width=100, command=self.destroy).pack(side="left", padx=8)

    def _browse(self, entry):
        d = filedialog.askdirectory()
        if d:
            entry.delete(0, "end")
            entry.insert(0, d)

    def _save(self):
        try:
            CONFIG.ai = AIConfig(
                api_key=self.api_key.get().strip(),
                api_base_url=self.api_url.get().strip(),
                model=self.model.get().strip(),
                max_tokens=int(self.max_tokens.get()),
                temperature=float(self.temperature.get()),
                timeout=int(self.timeout.get()),
            )
            CONFIG.template = TemplateConfig(
                template_dir=self.tpl_dir.get().strip(),
                output_dir=self.out_dir.get().strip(),
            )
            # 重置服务实例，下次使用时重新创建
            self.master.ai_service = None
            self.master.ai_extractor = None
            self.master._refresh_templates()
            self.destroy()
        except ValueError as e:
            messagebox.showerror("错误", f"参数无效: {e}")


# ── 入口 ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = App()
    app.mainloop()
