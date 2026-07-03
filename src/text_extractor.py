# ==============================================================================
# 文件名称: text_extractor.py
# 功能描述: 文本分割提取模块，使用AI从格式化文本中提取姓名、单位和职位信息
# 创建日期: 2026-03-14
# 作    者: 戒者有八
# ==============================================================================
"""
文本分割提取模块 - 使用AI从格式化文本中提取姓名、单位和职位信息

本模块提供智能文本提取功能，包括:
    - 从非结构化文本中识别人员信息
    - 提取姓名、单位、职位等结构化数据
    - 支持多种输出格式(制表符分隔、表格、打印格式)

设计思路:
    利用AI的自然语言理解能力，从格式不一的文本中提取结构化信息。
    通过精心设计的提示词引导AI返回标准JSON格式，便于解析和处理。
    提供多种格式化输出方法，满足不同使用场景需求。
"""

import json
from typing import List, Dict, Optional
from dataclasses import dataclass


# ------------------------------------------------------------------------------
# 人员信息数据类
# 功能: 封装单条人员信息的结构化数据
# ------------------------------------------------------------------------------
@dataclass
class PersonInfo:
    """
    人员信息数据类
    
    属性说明:
        name: 姓名
        company: 单位名称
        position: 职位名称
        original_line: 原始文本行(用于追溯和调试)
    
    设计思路:
        使用dataclass简化数据类的定义，
        自动生成__init__、__repr__等方法。
    """
    name: str  # 姓名
    company: str  # 单位
    position: str  # 职位
    original_line: str  # 原始文本行


# ------------------------------------------------------------------------------
# AI文本提取器类
# 功能: 使用AI服务从文本中提取人员信息
# 设计思路: 封装AI调用和响应解析逻辑，提供简洁的提取接口
# ------------------------------------------------------------------------------
class AIExtractor:
    """
    AI文本提取器
    
    利用AI服务从文本中智能提取姓名、单位、职位等信息。
    
    属性说明:
        ai_service: AI服务实例，用于调用AI API
        AI_PROMPT: 预定义的提示词模板，指导AI进行信息提取
    
    主要方法:
        - extract_from_text: 从文本提取人员信息列表
        - format_output: 格式化输出(制表符分隔)
        - format_as_table: 格式化为表格形式
        - format_for_print: 格式化为打印友好形式
    """
    
    # AI提示词模板
    # 功能: 指导AI如何提取信息并返回标准格式
    AI_PROMPT = """你是一个智能文本信息提取助手，擅长从各种格式的文本中自动分析和提取人员信息。

## 任务说明
请仔细分析输入文本，自动识别并提取每个人的姓名、工作单位和职位信息。

## 支持的输入格式示例

### 格式1：制表符/空格分隔
```
张三    北京科技有限公司    高级工程师
李四    上海数据科技集团    产品经理
```

### 格式2：逗号分隔
```
张三，北京科技有限公司，高级工程师；李四，上海数据科技集团，产品经理
张三，北京科技有限公司高级工程师
```

### 格式3：职务在前
```
新疆生产建设兵团第八师副师长、石河子市人民政府副市长 欧阳伟
新疆生产建设兵团第八师石河子市政务服务和大数据局局长 郑鸿英
```

### 格式4：混合格式
```
1. 张三 - 北京科技有限公司 - 高级工程师
2. 李四，上海数据科技集团，产品经理
3. 王五 广州创新科技 技术总监
```

## 智能分析规则

### 姓名识别规则：
- 通常是2-4个汉字的人名
- 位于文本开头或职务前面
- 可能包含"先生"、"女士"等称谓（需去除称谓提取纯姓名）

### 单位识别规则：
- 通常包含"公司"、"集团"、"有限公司"、"股份"、"科技"、"集团"、"部门"、"局"、"厅"、"委员会"等关键词
- 不包含职位信息
- 可能是政府机构、事业单位或企业名称

### 职位识别规则：
- 通常包含"经理"、"总监"、"工程师"、"主任"、"局长"、"部长"、"主席"、"董事长"、"总经理"、"副总"、"首席"等关键词
- 表示职责或头衔的名词

## 输出格式要求

请严格按照以下JSON格式返回结果，不要包含其他任何说明文字：
[
  {"name": "姓名", "company": "单位", "position": "职位"},
  {"name": "姓名", "company": "单位", "position": "职位"},
  ...
]

## 注意事项
1. 如果某字段无法识别或不存在，请填空字符串 ""
2. 确保每个人对应一条记录
3. 去除姓名中的称谓（如"先生"、"女士"）
4. 单位名称应完整，不包含职位
5. 职位应提取完整的职务名称

开始提取："""
    
    def __init__(self, ai_service=None):
        """
        初始化AI提取器
        
        参数:
            ai_service: AI服务实例(可选)，可后续通过set_ai_service设置
        """
        self.ai_service = ai_service
    
    def set_ai_service(self, ai_service):
        """
        设置AI服务实例
        
        参数:
            ai_service: AI服务实例
        
        使用场景:
            在创建提取器后动态更换AI服务，
            或在延迟初始化时设置服务。
        """
        self.ai_service = ai_service
    
    # --------------------------------------------------------------------------
    # 核心提取方法
    # 功能: 从文本中提取人员信息列表
    # --------------------------------------------------------------------------
    def extract_from_text(self, text: str) -> List[PersonInfo]:
        """
        从文本中提取人员信息
        
        参数:
            text: 要提取的文本内容
        
        返回值:
            List[PersonInfo]: 提取出的人员信息列表
        
        异常:
            ValueError: AI服务未配置
            RuntimeError: AI处理失败
        
        实现流程:
            1. 检查AI服务是否可用
            2. 构建完整的提示词
            3. 调用AI服务处理文本
            4. 解析AI返回的JSON数据
            5. 转换为PersonInfo对象列表
            6. 如果AI提取失败，尝试简单分割作为姓名处理（回退机制）
        """
        if not self.ai_service:
            raise ValueError("AI服务未配置，请先设置AI服务")
        
        # 构建完整提示词
        prompt = f"{self.AI_PROMPT}\n\n请提取以下文本：\n{text}"
        
        # 调用AI服务
        response = self.ai_service.process_text(prompt)
        
        if not response.success:
            raise RuntimeError(f"AI处理失败: {response.error_message}")
        
        content = response.data.get('content', '')
        
        # 解析AI响应
        results = self._parse_ai_response(content)
        
        # 如果AI未能提取到信息，尝试回退机制：直接按逗号/换行分割作为姓名
        if not results:
            results = self._fallback_parse(text)
        
        return results
    
    def _fallback_parse(self, text: str) -> List[PersonInfo]:
        """
        回退解析方法：当AI无法提取时，直接按逗号/换行分割作为姓名
        
        参数:
            text: 要提取的文本内容
        
        返回值:
            List[PersonInfo]: 提取出的人员信息列表（仅包含姓名）
        
        处理逻辑:
            1. 按逗号、分号、顿号分割文本
            2. 按换行符分割文本
            3. 去除空白字符和序号
            4. 返回仅包含姓名的PersonInfo列表
        """
        import re
        
        results = []
        
        # 按多种分隔符分割：逗号、分号、顿号、换行
        separators = r'[,，;；、\n\r]+'
        parts = re.split(separators, text)
        
        for part in parts:
            # 去除空白字符
            name = part.strip()
            
            # 去除开头的序号（如：1. 张三 -> 张三）
            name = re.sub(r'^\s*\d+[\.\uff0e、]\s*', '', name)
            
            # 去除首尾空白
            name = name.strip()
            
            # 如果姓名不为空且长度合理（2-20个字符），添加到结果
            if name and 2 <= len(name) <= 20:
                # 检查是否包含非法字符
                if not re.search(r'[<>:"/\\|?*\[\]{}]', name):
                    results.append(PersonInfo(
                        name=name,
                        company='',
                        position='',
                        original_line=part.strip()
                    ))
        
        # 去重
        unique_results = []
        seen_names = set()
        for info in results:
            if info.name not in seen_names:
                seen_names.add(info.name)
                unique_results.append(info)
        
        return unique_results
    
    # --------------------------------------------------------------------------
    # AI响应解析方法
    # 功能: 从AI返回的内容中解析JSON数据
    # --------------------------------------------------------------------------
    def _parse_ai_response(self, content: str) -> List[PersonInfo]:
        """
        解析AI响应内容
        
        参数:
            content: AI返回的文本内容
        
        返回值:
            List[PersonInfo]: 解析出的人员信息列表
        
        实现说明:
            1. 在内容中查找JSON数组边界
            2. 提取JSON字符串并解析
            3. 将字典转换为PersonInfo对象
        
        容错处理:
            - 未找到JSON边界时返回空列表
            - JSON解析失败时返回空列表
        """
        try:
            # 查找JSON数组的边界
            json_start = content.find('[')
            json_end = content.rfind(']') + 1
            
            if json_start == -1 or json_end <= json_start:
                return []  # 未找到有效JSON
            
            # 提取并解析JSON
            json_str = content[json_start:json_end]
            data = json.loads(json_str)
            
            # 转换为PersonInfo对象列表
            results = []
            for item in data:
                if isinstance(item, dict):
                    info = PersonInfo(
                        name=item.get('name', ''),
                        company=item.get('company', ''),
                        position=item.get('position', ''),
                        original_line=''
                    )
                    results.append(info)
            
            return results
            
        except json.JSONDecodeError as e:
            return []  # JSON解析失败，返回空列表
    
    # --------------------------------------------------------------------------
    # 格式化输出方法
    # 功能: 将提取结果格式化为制表符分隔的文本
    # --------------------------------------------------------------------------
    def format_output(
        self,
        text: str,
        include_name: bool = True,
        include_company: bool = True,
        include_position: bool = True,
        separator: str = "\t"
    ) -> str:
        """
        格式化输出提取结果
        
        参数:
            text: 要提取的文本
            include_name: 是否包含姓名列
            include_company: 是否包含单位列
            include_position: 是否包含职位列
            separator: 列分隔符，默认为制表符
        
        返回值:
            str: 格式化后的文本，每行一条记录
        
        使用场景:
            适合导入Excel或其他表格软件，
            制表符分隔可直接粘贴到Excel中。
        """
        infos = self.extract_from_text(text)
        lines = []
        
        for info in infos:
            parts = []
            if include_name:
                parts.append(info.name)
            if include_company:
                parts.append(info.company)
            if include_position:
                parts.append(info.position)
            
            if parts:
                lines.append(separator.join(parts))
        
        return '\n'.join(lines)
    
    # --------------------------------------------------------------------------
    # 表格格式化方法
    # 功能: 将提取结果格式化为可视化的表格形式
    # --------------------------------------------------------------------------
    def format_as_table(
        self,
        text: str,
        include_name: bool = True,
        include_company: bool = True,
        include_position: bool = True
    ) -> str:
        """
        格式化为表格形式
        
        参数:
            text: 要提取的文本
            include_name: 是否包含姓名列
            include_company: 是否包含单位列
            include_position: 是否包含职位列
        
        返回值:
            str: 表格形式的文本，使用Unicode边框字符
        
        实现说明:
            1. 计算每列的最大宽度
            2. 绘制表头边框和内容
            3. 逐行填充数据
            4. 绘制底部边框
        
        表格样式:
            使用Unicode制表符绘制边框，
            支持中文字符对齐。
        """
        infos = self.extract_from_text(text)
        if not infos:
            return ""
        
        # 构建表头
        headers = []
        if include_name:
            headers.append("姓名")
        if include_company:
            headers.append("单位")
        if include_position:
            headers.append("职位")
        
        # 计算每列宽度(考虑中文字符)
        widths = []
        if include_name:
            max_name = max(len(info.name) for info in infos)
            widths.append(max(max_name, 4) + 2)  # 至少4个字符宽度
        if include_company:
            max_company = max(len(info.company) for info in infos)
            widths.append(max(max_company, 4) + 2)
        if include_position:
            max_position = max(len(info.position) for info in infos)
            widths.append(max(max_position, 4) + 2)
        
        lines = []
        
        # 构建边框线
        border_parts = ["─" * w for w in widths]
        
        # 构建表头行
        header_parts = []
        idx = 0
        if include_name:
            header_parts.append("姓名".center(widths[idx]))
            idx += 1
        if include_company:
            header_parts.append("单位".center(widths[idx]))
            idx += 1
        if include_position:
            header_parts.append("职位".center(widths[idx]))
        
        # 绘制表格
        lines.append("┌" + "┬".join(border_parts) + "┐")  # 顶部边框
        lines.append("│" + "│".join(header_parts) + "│")  # 表头
        lines.append("├" + "┼".join(border_parts) + "┤")  # 分隔线
        
        # 数据行
        for info in infos:
            row_parts = []
            if include_name:
                row_parts.append(info.name.ljust(widths[0]))
            if include_company:
                idx = 1 if include_name else 0
                row_parts.append(info.company.ljust(widths[idx]))
            if include_position:
                idx = (1 if include_name else 0) + (1 if include_company else 0)
                row_parts.append(info.position.ljust(widths[idx]))
            lines.append("│" + "│".join(row_parts) + "│")
        
        lines.append("└" + "┴".join(border_parts) + "┘")  # 底部边框
        
        return '\n'.join(lines)
    
    # --------------------------------------------------------------------------
    # 打印格式化方法
    # 功能: 将提取结果格式化为适合打印的形式
    # --------------------------------------------------------------------------
    def format_for_print(
        self,
        text: str,
        include_name: bool = True,
        include_company: bool = True,
        include_position: bool = True,
        title: str = "人员名单"
    ) -> str:
        """
        格式化为打印友好形式
        
        参数:
            text: 要提取的文本
            include_name: 是否包含姓名
            include_company: 是否包含单位
            include_position: 是否包含职位
            title: 标题文字
        
        返回值:
            str: 打印友好格式的文本
        
        输出格式:
            ========================================
                      人员名单
            ========================================
            
            1. 姓名  单位  职位
            2. 姓名  单位  职位
            ...
            
            ========================================
                      共 N 人
            ========================================
        
        使用场景:
            适合直接打印输出或生成报告，
            格式清晰易读。
        """
        infos = self.extract_from_text(text)
        
        lines = []
        
        # 标题部分
        lines.append("=" * 60)
        lines.append(title.center(56))  # 居中显示标题
        lines.append("=" * 60)
        lines.append("")
        
        # 内容部分
        for i, info in enumerate(infos, 1):
            parts = []
            if include_name:
                parts.append(info.name)
            if include_company:
                parts.append(info.company)
            if include_position:
                parts.append(info.position)
            
            if parts:
                line_str = "  ".join(p for p in parts if p)
                lines.append(f"{i}. {line_str}")
        
        # 统计部分
        lines.append("")
        lines.append("=" * 60)
        lines.append(f"共 {len(infos)} 人".center(56))
        lines.append("=" * 60)
        
        return '\n'.join(lines)


# ------------------------------------------------------------------------------
# 提取器工厂函数
# 功能: 创建AI提取器实例的便捷方法
# ------------------------------------------------------------------------------
def create_extractor(ai_service=None) -> AIExtractor:
    """
    创建AI提取器实例
    
    参数:
        ai_service: AI服务实例(可选)
    
    返回值:
        AIExtractor: AI提取器实例
    
    使用场景:
        快速创建提取器实例，可延迟设置AI服务。
    
    示例:
        extractor = create_extractor(ai_service)
        extractor = create_extractor()  # 延迟设置服务
        extractor.set_ai_service(ai_service)  # 后续设置服务
    """
    return AIExtractor(ai_service)
