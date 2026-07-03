# ==============================================================================
# 文件名称: gui.py
# 功能描述: GUI用户界面模块，基于tkinter提供图形化操作界面
# 创建日期: 2026-03-14
# 作    者: 戒者有八
# ==============================================================================
"""
GUI用户界面 - 基于tkinter的图形界面

本模块提供完整的图形用户界面，包括:
    - 文本输入和编辑区域
    - AI智能提取功能
    - 模板选择和管理
    - 结果展示和导出
    - 系统设置对话框

设计思路:
    使用tkinter标准库构建跨平台GUI界面。
    采用面向对象设计，将界面组件和业务逻辑封装在类中。
    使用多线程处理AI请求，避免界面卡顿。
"""

import os
import threading
from typing import Optional, List
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

from config import CONFIG, AIConfig
from ai_service import AIService, create_ai_service
from template_processor import TemplateProcessor, create_template_processor
from text_extractor import AIExtractor, create_extractor
from card_generator import (
    generate_cards, replace_placeholder_in_paragraph,
    sanitize_filename, validate_card_document,
    convert_docx_to_pdf, merge_pdfs, generate_quality_report
)



# ------------------------------------------------------------------------------
# 主应用程序类
# 功能: 应用程序主窗口，整合所有功能模块
# 设计思路: MVC模式，分离界面、业务逻辑和数据
# ------------------------------------------------------------------------------
class TextProcessorApp:
    """
    文本处理应用程序主类
    
    负责创建和管理整个应用程序界面，协调各功能模块。
    
    属性说明:
        root: Tk根窗口
        ai_service: AI服务实例
        template_processor: 模板处理器实例
        ai_extractor: AI文本提取器实例
        current_template: 当前选中的模板路径
        template_fields: 当前模板的字段列表
    
    主要功能:
        - 文本输入和导入
        - AI智能信息提取
        - 模板选择和预览
        - 结果展示和导出
    """
    
    def __init__(self, root: tk.Tk):
        """
        初始化应用程序
        
        参数:
            root: Tk根窗口对象
        
        初始化流程:
            1. 配置窗口属性
            2. 初始化服务实例
            3. 创建菜单栏
            4. 创建主界面
            5. 创建状态栏
            6. 初始化目录结构
        """
        self.root = root
        self.root.title("文本处理与席卡生成程序")
        self.root.geometry("950x650")  # 初始窗口大小
        self.root.minsize(850, 550)  # 最小窗口大小
        
        # 服务实例(延迟初始化)
        self.ai_service: Optional[AIService] = None
        self.template_processor: TemplateProcessor = create_template_processor()
        self.ai_extractor: Optional[AIExtractor] = None
        
        # 当前状态
        self.current_template: str = ""  # 当前模板路径
        
        # 构建界面
        self._create_menu()  # 创建菜单栏
        self._create_main_frame()  # 创建主界面
        self._create_status_bar()  # 创建状态栏
        self._initialize_directories()  # 初始化目录
    
    # --------------------------------------------------------------------------
    # 目录初始化
    # 功能: 确保工作目录存在并刷新模板列表
    # --------------------------------------------------------------------------
    def _initialize_directories(self):
        """
        初始化工作目录
        
        功能说明:
            确保模板目录和输出目录存在，
            并刷新可用模板列表。
        """
        from config import ensure_directories
        ensure_directories(CONFIG)
        self._refresh_template_list()
    
    # --------------------------------------------------------------------------
    # 菜单栏创建
    # 功能: 创建应用程序菜单系统
    # --------------------------------------------------------------------------
    def _create_menu(self):
        """
        创建菜单栏
        
        菜单结构:
            文件菜单:
                - 新建模板
                - 打开模板
                - 导入文本文件
                - 退出
            设置菜单:
                - AI服务设置
                - 输出目录设置
            帮助菜单:
                - 使用说明
                - 关于
        """
        menubar = tk.Menu(self.root)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="新建模板", command=self._new_template)
        file_menu.add_command(label="打开模板", command=self._open_template)
        file_menu.add_separator()  # 分隔线
        file_menu.add_command(label="导入文本文件", command=self._import_text_file)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)
        menubar.add_cascade(label="文件", menu=file_menu)
        
        # 设置菜单
        settings_menu = tk.Menu(menubar, tearoff=0)
        settings_menu.add_command(label="AI服务设置", command=self._show_ai_settings)
        settings_menu.add_command(label="输出目录设置", command=self._show_output_settings)
        menubar.add_cascade(label="设置", menu=settings_menu)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="使用说明", command=self._show_help)
        help_menu.add_command(label="关于", command=self._show_about)
        menubar.add_cascade(label="帮助", menu=help_menu)
        
        self.root.config(menu=menubar)
    
    # --------------------------------------------------------------------------
    # 主界面创建
    # 功能: 创建主工作区域，包括输入区和输出区
    # --------------------------------------------------------------------------
    def _create_main_frame(self):
        """
        创建主界面布局
        
        布局结构:
            左侧 - 输入区域:
                - 文本输入框
                - 席卡生成设置
            右侧 - 输出区域:
                - 模板选择
                - 结果显示区
                - 操作按钮
        """
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # ==================== 左侧输入区域 ====================
        left_frame = ttk.LabelFrame(main_frame, text="输入区域", padding="10")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # 文本输入标签
        ttk.Label(left_frame, text="请输入人员信息文本:").pack(anchor=tk.W, pady=(0, 5))
        
        # 文本输入框(带滚动条)
        self.input_text = scrolledtext.ScrolledText(left_frame, height=15, wrap=tk.WORD)
        self.input_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 席卡生成框架
        card_settings_frame = ttk.LabelFrame(left_frame, text="席卡生成设置", padding="10")
        card_settings_frame.pack(fill=tk.X, pady=10)
        
        # 活动名称输入
        name_frame = ttk.Frame(card_settings_frame)
        name_frame.pack(fill=tk.X, pady=5)
        ttk.Label(name_frame, text="活动名称:", width=10).pack(side=tk.LEFT, padx=5, anchor=tk.W)
        self.event_name_var = tk.StringVar(value="")
        ttk.Entry(name_frame, textvariable=self.event_name_var, width=40).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 席卡显示内容选择
        display_frame = ttk.Frame(card_settings_frame)
        display_frame.pack(fill=tk.X, pady=5)
        ttk.Label(display_frame, text="显示内容:", width=10).pack(side=tk.LEFT, padx=5, anchor=tk.W)
        self.card_display_var = tk.StringVar(value="name")  # 默认显示姓名
        ttk.Radiobutton(display_frame, text="姓名", variable=self.card_display_var, value="name").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(display_frame, text="公司名", variable=self.card_display_var, value="company").pack(side=tk.LEFT, padx=10)
        
        # 生成按钮
        button_frame = ttk.Frame(card_settings_frame)
        button_frame.pack(fill=tk.X, pady=5)
        ttk.Button(button_frame, text="生成席卡", command=self._generate_cards, width=20).pack(side=tk.RIGHT, padx=5)
        
        # ==================== 右侧输出区域 ====================
        right_frame = ttk.LabelFrame(main_frame, text="输出区域", padding="10")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 模板选择框架
        template_frame = ttk.LabelFrame(right_frame, text="模板选择", padding="10")
        template_frame.pack(fill=tk.X, pady=10)
        
        # 模板下拉框
        self.template_var = tk.StringVar()
        self.template_combo = ttk.Combobox(template_frame, textvariable=self.template_var, state='readonly')
        self.template_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.template_combo.bind('<<ComboboxSelected>>', self._on_template_selected)  # 绑定选择事件
        
        # 浏览按钮
        ttk.Button(template_frame, text="浏览...", command=self._browse_template, width=10).pack(side=tk.RIGHT)
        
        # 结果显示标签
        ttk.Label(right_frame, text="处理结果:").pack(anchor=tk.W, pady=(0, 5))
        
        # 结果显示文本框(只读，带滚动条)
        self.output_text = scrolledtext.ScrolledText(right_frame, height=15, wrap=tk.WORD, state=tk.DISABLED)
        self.output_text.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 操作按钮框架
        output_button_frame = ttk.Frame(right_frame)
        output_button_frame.pack(fill=tk.X, pady=10)
        
        # 居中对齐按钮
        output_button_frame.columnconfigure(0, weight=1)
        output_button_frame.columnconfigure(1, weight=1)
        
        ttk.Button(output_button_frame, text="打开输出目录", command=self._open_output_dir, width=15).pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        ttk.Button(output_button_frame, text="复制结果", command=self._copy_result, width=15).pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
    
    # --------------------------------------------------------------------------
    # 状态栏创建
    # 功能: 创建底部状态显示区域
    # --------------------------------------------------------------------------
    def _create_status_bar(self):
        """
        创建状态栏
        
        包含:
            - 状态文本标签
            - 进度条
        """
        # 进度条
        self.progress = ttk.Progressbar(self.root, mode='determinate')
        self.progress.pack(side=tk.BOTTOM, fill=tk.X, pady=(0, 4), padx=10)
        
        # 状态文本
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, pady=(0, 8), padx=10)
    
    # --------------------------------------------------------------------------
    # 模板列表刷新
    # 功能: 扫描模板目录并更新下拉框列表
    # --------------------------------------------------------------------------
    def _refresh_template_list(self):
        """
        刷新模板列表
        
        功能说明:
            扫描模板目录中的文件，
            筛选出支持的格式(.txt, .docx, .pdf)，
            更新模板下拉框的选项。
        """
        template_dir = CONFIG.template.template_dir
        if os.path.exists(template_dir):
            templates = []
            for f in os.listdir(template_dir):
                if f.endswith(('.txt', '.docx', '.pdf')):
                    templates.append(f)
            self.template_combo['values'] = templates
            
            # 如果有模板且当前未选择，自动选择第一个
            if templates and not self.template_var.get():
                self.template_var.set(templates[0])
                self._on_template_selected(None)
    
    # --------------------------------------------------------------------------
    # 模板选择事件处理
    # 功能: 处理模板下拉框选择事件
    # --------------------------------------------------------------------------
    def _on_template_selected(self, event):
        """
        模板选择事件处理
        
        参数:
            event: 事件对象(可能为None)
        
        功能说明:
            当用户选择模板时更新当前模板路径
        """
        template_name = self.template_var.get()
        if template_name:
            self.current_template = os.path.join(CONFIG.template.template_dir, template_name)
    
    # --------------------------------------------------------------------------
    # 模板浏览
    # 功能: 打开文件选择对话框选择模板
    # --------------------------------------------------------------------------
    def _browse_template(self):
        """
        浏览选择模板文件
        
        功能说明:
            打开文件选择对话框，
            允许用户选择外部的模板文件。
        """
        file_path = filedialog.askopenfilename(
            title="选择模板文件",
            filetypes=[
                ("所有支持格式", "*.txt;*.docx;*.pdf"),
                ("文本文件", "*.txt"),
                ("Word文档", "*.docx"),
                ("PDF文件", "*.pdf")
            ]
        )
        if file_path:
            self.current_template = file_path
            self.template_var.set(os.path.basename(file_path))
            self._on_template_selected(None)
    
    # --------------------------------------------------------------------------
    # 错误显示
    # 功能: 在输出区域显示错误信息
    # --------------------------------------------------------------------------
    def _display_error(self, error_message: str):
        """
        显示错误信息
        
        参数:
            error_message: 错误信息文本
        
        功能说明:
            在输出区域显示错误信息，
            同时更新状态栏和进度条。
        """
        self.progress['value'] = 0
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, f"错误: {error_message}\n")
        self.output_text.config(state=tk.DISABLED)
        self.status_var.set("处理失败")
    
    # --------------------------------------------------------------------------
    # AI服务检查
    # 功能: 检查并初始化AI服务
    # --------------------------------------------------------------------------
    def _check_ai_service(self) -> bool:
        """
        检查AI服务是否可用
        
        返回值:
            bool: AI服务是否可用
        
        功能说明:
            1. 检查AI服务实例是否存在
            2. 检查API密钥是否配置
            3. 如果未配置，弹出设置对话框
        """
        if self.ai_service is None:
            if not CONFIG.ai.api_key:
                self._show_ai_settings()
                return False
            self.ai_service = create_ai_service()
        
        if not self.ai_service.config.api_key:
            messagebox.showwarning("警告", "请先配置AI服务API密钥")
            self._show_ai_settings()
            return False
        
        return True
    
    # --------------------------------------------------------------------------
    # AI提取器检查
    # 功能: 检查并初始化AI提取器
    # --------------------------------------------------------------------------
    def _check_ai_extractor(self) -> bool:
        """
        检查AI提取器是否可用
        
        返回值:
            bool: AI提取器是否可用
        
        功能说明:
            1. 先检查AI服务
            2. 初始化或更新AI提取器实例
        """
        if not self._check_ai_service():
            return False
        
        if self.ai_extractor is None:
            self.ai_extractor = create_extractor(self.ai_service)
        else:
            self.ai_extractor.set_ai_service(self.ai_service)
        
        return True
    

    

    
    # --------------------------------------------------------------------------
    # 席卡生成功能
    # 功能: 根据提取的人员信息生成席卡文档
    # --------------------------------------------------------------------------
    def _generate_cards(self):
        """
        生成席卡文档
        
        功能说明:
            1. 获取输入文本并提取人员信息
            2. 获取活动名称和显示内容设置
            3. 使用席卡模板生成docx文档
            4. 保存到输出目录
        
        使用场景:
            用于会议、活动等场合的席卡打印，
            支持选择显示姓名或公司名。
        """
        text = self.input_text.get(1.0, tk.END).strip()
        if not text:
            messagebox.showwarning("警告", "请输入文本内容")
            return
        
        if not self._check_ai_extractor():
            return
        
        # 获取设置
        event_name = self.event_name_var.get().strip()
        display_type = self.card_display_var.get()  # "name" 或 "company"
        
        # 检查是否选择了席卡模板
        if not self.current_template:
            messagebox.showwarning("警告", "请先选择席卡模板")
            return
        
        # 检查模板文件类型
        template_ext = os.path.splitext(self.current_template)[1].lower()
        if template_ext not in ['.docx', '.doc']:
            messagebox.showwarning("警告", "席卡生成功能仅支持.docx格式的模板文件，请选择一个Word文档模板")
            return
        
        self.status_var.set("正在生成席卡...")
        self.progress['value'] = 0
        
        def generate_thread():
            try:
                self.root.after(0, lambda: self.progress.config(value=20))
                
                # 提取人员信息
                infos = self.ai_extractor.extract_from_text(text)
                
                if not infos:
                    self.root.after(0, lambda: messagebox.showwarning("警告", "未能提取到人员信息"))
                    return
                
                self.root.after(0, lambda: self.progress.config(value=50))
                
                # 生成席卡
                result = self._create_card_document(infos, event_name, display_type)
                
                self.root.after(0, lambda: self.progress.config(value=100))
                
                if result['success']:
                    # 构建详细的结果显示
                    valid_count = len([f for f in result['files'] if f.get('valid', False)])
                    invalid_count = len([f for f in result['files'] if not f.get('valid', False)])
                    
                    display_text = f"席卡生成完成\n"
                    display_text += f"=" * 40 + "\n"
                    display_text += f"输出目录: {result['output_dir']}\n"
                    display_text += f"成功生成: {valid_count} 个文件\n"
                    if invalid_count > 0:
                        display_text += f"验证失败: {invalid_count} 个文件\n"
                    display_text += f"\n已生成文件:\n"
                    display_text += "-" * 40 + "\n"
                    
                    for f in result['files']:
                        status = "✓" if f.get('valid', False) else "✗"
                        display_text += f"{status} {f['filename']}\n"
                    
                    if result.get('failed'):
                        display_text += f"\n失败记录: {', '.join(result['failed'])}\n"
                    
                    display_text += f"\n质量报告: {result['report_path']}"
                    
                    # 直接更新输出文本
                    self.root.after(0, lambda: self._update_output_text(display_text, "席卡生成结果"))
                    self.root.after(0, lambda: self.status_var.set(f"席卡生成完成，共 {valid_count} 个有效文件"))
                else:
                    self.root.after(0, lambda: self._display_error(result['error']))
                    
            except Exception as e:
                self.root.after(0, lambda: self._display_error(str(e)))
        
        threading.Thread(target=generate_thread, daemon=True).start()
    
    # --------------------------------------------------------------------------
    # 创建席卡文档
    # 功能: 实际生成席卡docx文档（单人单文件模式）
    # --------------------------------------------------------------------------
    def _create_card_document(self, infos, event_name: str, display_type: str) -> dict:
        """
        创建席卡文档 - 委托给 card_generator 共享模块

        参数:
            infos: 人员信息列表(PersonInfo对象)
            event_name: 活动名称
            display_type: 显示类型("name"或"company")

        返回值:
            dict: 包含success、count、output_dir、files、errors的字典
        """
        return generate_cards(
            infos=infos,
            template_path=self.current_template,
            event_name=event_name,
            display_type=display_type,
            output_base_dir=CONFIG.template.output_dir
        )
    
    # --------------------------------------------------------------------------
    # 更新输出文本
    # 功能: 在输出区域显示结果文本
    # --------------------------------------------------------------------------
    def _update_output_text(self, result: str, title: str):
        """
        更新输出文本
        
        参数:
            result: 结果文本
            title: 结果标题
        """
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, f"{title}:\n")
        self.output_text.insert(tk.END, "-" * 40 + "\n")
        self.output_text.insert(tk.END, result)
        self.output_text.config(state=tk.DISABLED)
    
    # --------------------------------------------------------------------------
    # 复制结果
    # 功能: 将结果复制到剪贴板
    # --------------------------------------------------------------------------
    def _copy_result(self):
        """
        复制结果到剪贴板
        
        功能说明:
            将输出区域的内容复制到系统剪贴板。
        """
        content = self.output_text.get(1.0, tk.END)
        if not content.strip():
            messagebox.showwarning("警告", "没有可复制的内容")
            return
        
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        self.status_var.set("结果已复制到剪贴板")
    
    # --------------------------------------------------------------------------
    # 保存结果
    # 功能: 将结果保存到文件
    # --------------------------------------------------------------------------
    def _save_result(self):
        """
        保存结果到文件
        
        功能说明:
            打开文件保存对话框，
            将输出区域的内容保存为文本文件。
        """
        content = self.output_text.get(1.0, tk.END)
        if not content.strip():
            messagebox.showwarning("警告", "没有可保存的内容")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="保存结果",
            defaultextension=".txt",
            filetypes=[
                ("文本文件", "*.txt"),
                ("所有文件", "*.*")
            ]
        )
        
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            messagebox.showinfo("成功", f"结果已保存到: {file_path}")
    
    # --------------------------------------------------------------------------
    # 打开输出目录
    # 功能: 在文件管理器中打开输出目录
    # --------------------------------------------------------------------------
    def _open_output_dir(self):
        """
        打开输出目录
        
        功能说明:
            在系统文件管理器中打开输出目录。
        """
        output_dir = CONFIG.template.output_dir
        if os.path.exists(output_dir):
            os.startfile(output_dir)
    
    # --------------------------------------------------------------------------
    # 新建模板
    # 功能: 打开新建模板对话框
    # --------------------------------------------------------------------------
    def _new_template(self):
        """
        新建模板
        
        功能说明:
            打开模板创建对话框，
            创建完成后刷新模板列表。
        """
        dialog = TemplateDialog(self.root)
        self.root.wait_window(dialog.top)
        self._refresh_template_list()
    
    # --------------------------------------------------------------------------
    # 打开模板
    # 功能: 浏览选择模板文件
    # --------------------------------------------------------------------------
    def _open_template(self):
        """打开模板文件(调用浏览功能)"""
        self._browse_template()
    
    # --------------------------------------------------------------------------
    # 导入文本文件
    # 功能: 从文件导入文本到输入区域
    # --------------------------------------------------------------------------
    def _import_text_file(self):
        """
        导入文本文件
        
        功能说明:
            打开文件选择对话框，
            将选中的文本文件内容导入到输入区域。
        """
        file_path = filedialog.askopenfilename(
            title="选择文本文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if file_path:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.input_text.delete(1.0, tk.END)
            self.input_text.insert(tk.END, content)
    
    # --------------------------------------------------------------------------
    # AI设置对话框
    # 功能: 显示AI服务配置对话框
    # --------------------------------------------------------------------------
    def _show_ai_settings(self):
        """
        显示AI服务设置对话框
        
        功能说明:
            打开AI配置对话框，
            用户可以修改API密钥、地址、模型等设置。
        """
        dialog = AISettingsDialog(self.root, CONFIG.ai)
        self.root.wait_window(dialog.top)
        
        if dialog.result:
            CONFIG.ai = dialog.result
            self.ai_service = create_ai_service(CONFIG.ai)
    
    # --------------------------------------------------------------------------
    # 输出设置对话框
    # 功能: 显示输出目录配置对话框
    # --------------------------------------------------------------------------
    def _show_output_settings(self):
        """
        显示输出设置对话框
        
        功能说明:
            打开输出配置对话框，
            用户可以修改模板目录和输出目录。
        """
        dialog = OutputSettingsDialog(self.root, CONFIG.template)
        self.root.wait_window(dialog.top)
        
        if dialog.result:
            CONFIG.template = dialog.result
            self.template_processor = create_template_processor()
    
    # --------------------------------------------------------------------------
    # 帮助对话框
    # 功能: 显示使用说明
    # --------------------------------------------------------------------------
    def _show_help(self):
        """
        显示使用说明
        
        功能说明:
            在新窗口中显示详细的使用说明文档。
        """
        help_text = """
自动化文本处理与模板填充程序 - 使用说明

1. 配置AI服务
   - 在"设置"菜单中选择"AI服务设置"
   - 输入API密钥和API地址

2. 选择模板
   - 从下拉列表选择已有模板
   - 或点击"浏览"选择其他模板文件

3. 输入文本
   - 在左侧输入区域输入或粘贴文本
   - 或从文件导入文本

4. AI智能提取
   - 勾选需要提取的内容（姓名/单位/职位）
   - 点击"提取"、"表格"或"打印"按钮
   - 程序将使用AI智能提取信息

5. 席卡生成功能
   - 输入活动名称（可选）
   - 选择席卡显示内容：姓名或公司名
   - 选择席卡模板文件（.docx格式）
   - 点击"生成席卡"按钮
   - 程序将自动生成席卡文档

模板格式说明:
- 使用 {{字段名}} 作为占位符
- 例如: {{name}}, {{date}}, {{content}}
- 席卡模板支持: {{name}}, {{company}}, {{position}}, {{event}}, {{display}}, {{date}}
- {{display}} 会根据用户选择显示姓名或公司名
- 程序会自动替换占位符为实际值
        """
        
        help_window = tk.Toplevel(self.root)
        help_window.title("使用说明")
        help_window.geometry("500x400")
        
        text = scrolledtext.ScrolledText(help_window, wrap=tk.WORD)
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text.insert(tk.END, help_text)
        text.config(state=tk.DISABLED)
    
    # --------------------------------------------------------------------------
    # 关于对话框
    # 功能: 显示程序信息
    # --------------------------------------------------------------------------
    def _show_about(self):
        """显示关于对话框"""
        messagebox.showinfo(
            "关于",
            "自动化文本处理与模板填充程序\n\n"
            "版本: 1.0.0\n\n"
            "功能:\n"
            "- AI智能文本处理\n"
            "- 模板自动填充\n"
            "- 多种格式输出"
        )


# ------------------------------------------------------------------------------
# AI设置对话框类
# 功能: 提供AI服务配置界面
# ------------------------------------------------------------------------------
class AISettingsDialog:
    """
    AI服务设置对话框
    
    属性说明:
        result: 对话框结果(确认时为AIConfig对象)
        config: 当前配置
        top: 对话框窗口
    
    配置项:
        - API密钥
        - API地址
        - 模型名称
        - 最大Tokens
        - Temperature
        - 超时时间
    """
    
    def __init__(self, parent, config: AIConfig):
        """
        初始化对话框
        
        参数:
            parent: 父窗口
            config: 当前AI配置
        """
        self.result = None
        self.config = config
        
        # 创建对话框窗口
        self.top = tk.Toplevel(parent)
        self.top.title("AI服务设置")
        self.top.geometry("450x300")
        self.top.transient(parent)  # 设置为父窗口的临时窗口
        self.top.grab_set()  # 模态对话框
        
        # 创建表单
        frame = ttk.Frame(self.top, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # API密钥
        ttk.Label(frame, text="API密钥:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.api_key_var = tk.StringVar(value=config.api_key)
        self.api_key_entry = ttk.Entry(frame, textvariable=self.api_key_var, width=40, show="*")  # 密码模式
        self.api_key_entry.grid(row=0, column=1, pady=5, padx=5)
        
        # API地址
        ttk.Label(frame, text="API地址:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.api_url_var = tk.StringVar(value=config.api_base_url)
        ttk.Entry(frame, textvariable=self.api_url_var, width=40).grid(row=1, column=1, pady=5, padx=5)
        
        # 模型
        ttk.Label(frame, text="模型:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.model_var = tk.StringVar(value=config.model)
        ttk.Entry(frame, textvariable=self.model_var, width=40).grid(row=2, column=1, pady=5, padx=5)
        
        # 最大Tokens
        ttk.Label(frame, text="最大Tokens:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.max_tokens_var = tk.StringVar(value=str(config.max_tokens))
        ttk.Entry(frame, textvariable=self.max_tokens_var, width=40).grid(row=3, column=1, pady=5, padx=5)
        
        # Temperature
        ttk.Label(frame, text="Temperature:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.temperature_var = tk.StringVar(value=str(config.temperature))
        ttk.Entry(frame, textvariable=self.temperature_var, width=40).grid(row=4, column=1, pady=5, padx=5)
        
        # 超时
        ttk.Label(frame, text="超时(秒):").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.timeout_var = tk.StringVar(value=str(config.timeout))
        ttk.Entry(frame, textvariable=self.timeout_var, width=40).grid(row=5, column=1, pady=5, padx=5)
        
        # 按钮
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="确定", command=self._ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=self._cancel).pack(side=tk.LEFT, padx=5)
    
    def _ok(self):
        """
        确认按钮处理
        
        功能说明:
            验证输入并创建AIConfig对象，
            成功后关闭对话框。
        """
        try:
            self.result = AIConfig(
                api_key=self.api_key_var.get(),
                api_base_url=self.api_url_var.get(),
                model=self.model_var.get(),
                max_tokens=int(self.max_tokens_var.get()),
                temperature=float(self.temperature_var.get()),
                timeout=int(self.timeout_var.get())
            )
            self.top.destroy()
        except ValueError as e:
            messagebox.showerror("错误", f"输入值无效: {e}")
    
    def _cancel(self):
        """取消按钮处理，关闭对话框"""
        self.top.destroy()


# ------------------------------------------------------------------------------
# 输出设置对话框类
# 功能: 提供输出目录配置界面
# ------------------------------------------------------------------------------
class OutputSettingsDialog:
    """
    输出设置对话框
    
    属性说明:
        result: 对话框结果(确认时为TemplateConfig对象)
        config: 当前配置
        top: 对话框窗口
    
    配置项:
        - 模板目录
        - 输出目录
    """
    
    def __init__(self, parent, config):
        """
        初始化对话框
        
        参数:
            parent: 父窗口
            config: 当前模板配置
        """
        self.result = None
        self.config = config
        
        # 创建对话框窗口
        self.top = tk.Toplevel(parent)
        self.top.title("输出设置")
        self.top.geometry("450x150")
        self.top.transient(parent)
        self.top.grab_set()
        
        # 创建表单
        frame = ttk.Frame(self.top, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 模板目录
        ttk.Label(frame, text="模板目录:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.template_dir_var = tk.StringVar(value=config.template_dir)
        ttk.Entry(frame, textvariable=self.template_dir_var, width=30).grid(row=0, column=1, pady=5, padx=5)
        ttk.Button(frame, text="浏览...", command=lambda: self._browse_dir(self.template_dir_var)).grid(row=0, column=2)
        
        # 输出目录
        ttk.Label(frame, text="输出目录:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.output_dir_var = tk.StringVar(value=config.output_dir)
        ttk.Entry(frame, textvariable=self.output_dir_var, width=30).grid(row=1, column=1, pady=5, padx=5)
        ttk.Button(frame, text="浏览...", command=lambda: self._browse_dir(self.output_dir_var)).grid(row=1, column=2)
        
        # 按钮
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=2, column=0, columnspan=3, pady=20)
        
        ttk.Button(button_frame, text="确定", command=self._ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=self._cancel).pack(side=tk.LEFT, padx=5)
    
    def _browse_dir(self, var: tk.StringVar):
        """
        浏览目录
        
        参数:
            var: 存储目录路径的StringVar对象
        """
        dir_path = filedialog.askdirectory()
        if dir_path:
            var.set(dir_path)
    
    def _ok(self):
        """
        确认按钮处理
        
        功能说明:
            创建TemplateConfig对象并关闭对话框。
        """
        from config import TemplateConfig
        self.result = TemplateConfig(
            template_dir=self.template_dir_var.get(),
            output_dir=self.output_dir_var.get()
        )
        self.top.destroy()
    
    def _cancel(self):
        """取消按钮处理"""
        self.top.destroy()


# ------------------------------------------------------------------------------
# 模板创建对话框类
# 功能: 提供新建模板的界面
# ------------------------------------------------------------------------------
class TemplateDialog:
    """
    模板创建对话框
    
    属性说明:
        result: 对话框结果
        top: 对话框窗口
    
    功能:
        - 输入模板名称
        - 编辑模板内容
        - 创建模板文件
    """
    
    def __init__(self, parent):
        """
        初始化对话框
        
        参数:
            parent: 父窗口
        """
        self.result = None
        
        # 创建对话框窗口
        self.top = tk.Toplevel(parent)
        self.top.title("新建模板")
        self.top.geometry("500x400")
        self.top.transient(parent)
        self.top.grab_set()
        
        # 创建表单
        frame = ttk.Frame(self.top, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 模板名称
        ttk.Label(frame, text="模板名称:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.name_var = tk.StringVar(value="new_template.txt")
        ttk.Entry(frame, textvariable=self.name_var, width=40).grid(row=0, column=1, pady=5)
        
        # 模板内容
        ttk.Label(frame, text="模板内容:").grid(row=1, column=0, sticky=tk.NW, pady=5)
        self.content_text = scrolledtext.ScrolledText(frame, width=50, height=15)
        self.content_text.grid(row=1, column=1, pady=5)
        
        # 插入示例模板内容
        self.content_text.insert(tk.END, """====================================
              文档模板
====================================

标题: {{title}}
日期: {{date}}

尊敬的 {{name}}:

您好！

{{content}}

此致
敬礼！

====================================
""")
        
        # 按钮
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="创建", command=self._create).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=self.top.destroy).pack(side=tk.LEFT, padx=5)
    
    def _create(self):
        """
        创建模板文件
        
        功能说明:
            验证输入并创建模板文件。
        """
        name = self.name_var.get().strip()
        content = self.content_text.get(1.0, tk.END)
        
        if not name:
            messagebox.showwarning("警告", "请输入模板名称")
            return
        
        template_path = os.path.join(CONFIG.template.template_dir, name)
        
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        messagebox.showinfo("成功", f"模板已创建: {template_path}")
        self.top.destroy()


# ------------------------------------------------------------------------------
# GUI启动函数
# 功能: 创建并运行GUI应用程序
# ------------------------------------------------------------------------------
def run_gui():
    """
    启动GUI应用程序
    
    功能说明:
        创建Tk根窗口和应用程序实例，
        启动主事件循环。
    """
    root = tk.Tk()
    app = TextProcessorApp(root)
    root.mainloop()


# 模块入口
if __name__ == "__main__":
    run_gui()
