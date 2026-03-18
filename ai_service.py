# ==============================================================================
# 文件名称: ai_service.py
# 功能描述: AI服务接口模块，处理与AI API的通信，支持文本处理和数据提取
# 创建日期: 2026-03-14
# 作    者: 戒者有八
# ==============================================================================
"""
AI服务接口模块 - 处理与AI API的通信

本模块提供与AI服务API交互的核心功能，包括:
    - 构建和发送HTTP请求到AI服务
    - 处理API响应并解析结果
    - 实现请求限流和错误重试机制
    - 支持结构化数据提取

设计思路:
    使用urllib标准库实现HTTP通信，避免第三方依赖。
    通过dataclass封装响应数据，提供类型安全的接口。
    内置限流和重试机制，提高服务的稳定性和可靠性。
"""

import json
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import urllib.request
import urllib.error
from config import AIConfig


# ------------------------------------------------------------------------------
# AI响应数据类
# 功能: 封装AI服务的响应结果，统一成功和失败的处理方式
# ------------------------------------------------------------------------------
@dataclass
class AIResponse:
    """
    AI服务响应数据类
    
    属性说明:
        success: 请求是否成功
        data: 响应数据字典，包含content和usage等信息
        error_message: 错误信息，成功时为空字符串
        raw_response: 原始响应字符串，用于调试和日志
    
    设计思路:
        使用dataclass简化类的定义，自动生成__init__等方法。
        统一成功和失败的响应格式，便于调用方处理。
    """
    success: bool  # 请求成功标志
    data: Dict[str, Any]  # 响应数据
    error_message: str = ""  # 错误信息
    raw_response: str = ""  # 原始响应


# ------------------------------------------------------------------------------
# AI服务异常类
# 功能: 定义AI服务相关的自定义异常
# ------------------------------------------------------------------------------
class AIServiceError(Exception):
    """
    AI服务异常类
    
    用于封装AI服务调用过程中发生的各类错误，
    便于上层调用者捕获和处理。
    """
    pass


# ------------------------------------------------------------------------------
# AI服务类
# 功能: 核心AI服务实现，处理所有与AI API的交互
# 设计思路: 封装HTTP请求细节，提供简洁的文本处理接口
# ------------------------------------------------------------------------------
class AIService:
    """
    AI服务类
    
    负责与AI API进行通信，提供文本处理和数据提取功能。
    
    属性说明:
        config: AI配置实例
        last_request_time: 上次请求时间戳，用于限流
        min_request_interval: 最小请求间隔(秒)，防止请求过于频繁
    
    主要方法:
        process_text: 处理单条文本
        process_batch: 批量处理文本
        extract_structured_data: 提取结构化数据
    """
    
    def __init__(self, config: AIConfig):
        """
        初始化AI服务实例
        
        参数:
            config: AI配置实例，包含API密钥、地址等配置信息
        """
        self.config = config
        self.last_request_time = 0  # 初始化上次请求时间为0
        self.min_request_interval = 0.5  # 最小请求间隔0.5秒
    
    # --------------------------------------------------------------------------
    # 构建HTTP请求头
    # 功能: 创建包含认证信息的请求头
    # --------------------------------------------------------------------------
    def _build_headers(self) -> Dict[str, str]:
        """
        构建HTTP请求头
        
        返回值:
            Dict[str, str]: 包含Content-Type和Authorization的请求头字典
        
        实现说明:
            Content-Type设置为application/json，表示请求体为JSON格式。
            Authorization使用Bearer Token认证方式。
        """
        return {
            "Content-Type": "application/json",  # JSON格式请求体
            "Authorization": f"Bearer {self.config.api_key}"  # Bearer Token认证
        }
    
    # --------------------------------------------------------------------------
    # 构建请求体
    # 功能: 根据提示词构建API请求体
    # --------------------------------------------------------------------------
    def _build_request_body(self, prompt: str, system_prompt: str = None) -> Dict[str, Any]:
        """
        构建API请求体
        
        参数:
            prompt: 用户提示词
            system_prompt: 系统提示词(可选)，用于设定AI角色和行为
        
        返回值:
            Dict[str, Any]: 符合OpenAI API格式的请求体字典
        
        实现说明:
            如果提供system_prompt，会作为第一条消息添加到消息列表。
            消息格式遵循OpenAI Chat API规范。
        """
        messages = []
        
        # 添加系统提示词(如果提供)
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # 添加用户消息
        messages.append({"role": "user", "content": prompt})
        
        # 构建完整请求体
        return {
            "model": self.config.model,  # 指定模型
            "messages": messages,  # 消息列表
            "max_tokens": self.config.max_tokens,  # 最大token数
            "temperature": self.config.temperature  # 温度参数
        }
    
    # --------------------------------------------------------------------------
    # 发送HTTP请求
    # 功能: 执行实际的HTTP请求并处理响应
    # --------------------------------------------------------------------------
    def _make_request(self, url: str, headers: Dict[str, str], body: Dict[str, Any]) -> AIResponse:
        """
        发送HTTP请求到AI服务
        
        参数:
            url: API端点URL
            headers: HTTP请求头
            body: 请求体字典
        
        返回值:
            AIResponse: 封装了响应结果的AIResponse对象
        
        异常处理:
            - HTTPError: HTTP状态码错误
            - URLError: 网络连接错误
            - JSONDecodeError: 响应JSON解析错误
            - 其他异常: 统一捕获并返回错误响应
        
        实现细节:
            1. 调用限流方法确保请求间隔
            2. 将请求体编码为JSON字节流
            3. 创建Request对象并发送请求
            4. 解析响应并提取内容
        """
        self._rate_limit()  # 执行限流检查
        
        try:
            # 将请求体编码为UTF-8 JSON字节流
            data = json.dumps(body).encode('utf-8')
            
            # 创建HTTP请求对象
            req = urllib.request.Request(
                url,
                data=data,
                headers=headers,
                method='POST'
            )
            
            # 发送请求并读取响应
            with urllib.request.urlopen(req, timeout=self.config.timeout) as response:
                response_data = response.read().decode('utf-8')  # 解码响应
                result = json.loads(response_data)  # 解析JSON
                
                # 检查响应格式并提取内容
                if 'choices' in result and len(result['choices']) > 0:
                    content = result['choices'][0].get('message', {}).get('content', '')
                    return AIResponse(
                        success=True,
                        data={"content": content, "usage": result.get('usage', {})},
                        raw_response=response_data
                    )
                else:
                    # 响应格式不正确
                    return AIResponse(
                        success=False,
                        data={},
                        error_message="Invalid response format from AI service",
                        raw_response=response_data
                    )
                    
        except urllib.error.HTTPError as e:
            # HTTP错误(如401、403、500等)
            error_body = e.read().decode('utf-8') if e.fp else ""
            return AIResponse(
                success=False,
                data={},
                error_message=f"HTTP Error {e.code}: {error_body}"
            )
        except urllib.error.URLError as e:
            # URL错误(如网络连接失败)
            return AIResponse(
                success=False,
                data={},
                error_message=f"URL Error: {str(e.reason)}"
            )
        except json.JSONDecodeError as e:
            # JSON解析错误
            return AIResponse(
                success=False,
                data={},
                error_message=f"JSON Decode Error: {str(e)}"
            )
        except Exception as e:
            # 其他未预期的错误
            return AIResponse(
                success=False,
                data={},
                error_message=f"Unexpected error: {str(e)}"
            )
    
    # --------------------------------------------------------------------------
    # 请求限流
    # 功能: 控制请求频率，防止请求过于频繁
    # --------------------------------------------------------------------------
    def _rate_limit(self):
        """
        请求限流控制
        
        功能说明:
            确保两次请求之间至少间隔min_request_interval秒，
            防止因请求过于频繁被API限流或封禁。
        
        实现方式:
            计算距离上次请求的时间差，如果不足间隔时间则休眠等待。
        """
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)  # 等待剩余时间
        self.last_request_time = time.time()  # 更新上次请求时间
    
    # --------------------------------------------------------------------------
    # 处理单条文本
    # 功能: 将文本发送到AI服务进行处理
    # --------------------------------------------------------------------------
    def process_text(self, text: str, system_prompt: str = None, retry_count: int = 0) -> AIResponse:
        """
        处理单条文本
        
        参数:
            text: 要处理的文本内容
            system_prompt: 系统提示词(可选)
            retry_count: 当前重试次数(内部使用)
        
        返回值:
            AIResponse: 处理结果响应对象
        
        重试机制:
            如果请求失败且重试次数小于3次，会进行指数退避重试。
            每次重试等待时间为2^retry_count秒。
        
        实现流程:
            1. 检查API密钥是否配置
            2. 构建请求URL、请求头和请求体
            3. 发送请求并获取响应
            4. 失败时自动重试
        """
        # 检查API密钥
        if not self.config.api_key:
            return AIResponse(
                success=False,
                data={},
                error_message="API key is not configured"
            )
        
        # 构建API端点URL
        url = f"{self.config.api_base_url.rstrip('/')}/chat/completions"
        headers = self._build_headers()
        body = self._build_request_body(text, system_prompt)
        
        # 发送请求
        response = self._make_request(url, headers, body)
        
        # 失败重试逻辑
        if not response.success and retry_count < 3:
            time.sleep(2 ** retry_count)  # 指数退避: 1秒、2秒、4秒
            return self.process_text(text, system_prompt, retry_count + 1)
        
        return response
    
    # --------------------------------------------------------------------------
    # 批量处理文本
    # 功能: 处理多条文本，返回所有结果
    # --------------------------------------------------------------------------
    def process_batch(self, texts: List[str], system_prompt: str = None) -> List[AIResponse]:
        """
        批量处理文本
        
        参数:
            texts: 文本列表
            system_prompt: 系统提示词(可选)，应用于所有文本
        
        返回值:
            List[AIResponse]: 响应结果列表，与输入文本一一对应
        
        实现说明:
            逐条处理文本，自动应用限流机制。
            每条文本的处理结果独立存储。
        """
        results = []
        for text in texts:
            response = self.process_text(text, system_prompt)
            results.append(response)
        return results
    
    # --------------------------------------------------------------------------
    # 提取结构化数据
    # 功能: 从文本中提取指定字段的结构化数据
    # --------------------------------------------------------------------------
    def extract_structured_data(self, text: str, fields: List[str]) -> AIResponse:
        """
        从文本中提取结构化数据
        
        参数:
            text: 要提取数据的文本
            fields: 需要提取的字段名称列表
        
        返回值:
            AIResponse: 包含提取结果的响应对象
                成功时data['parsed']包含解析后的字典数据
        
        实现原理:
            1. 构建专门的系统提示词，指导AI以JSON格式返回数据
            2. 发送请求获取AI响应
            3. 从响应中提取JSON字符串并解析
            4. 将解析结果存入data['parsed']
        
        JSON提取逻辑:
            在AI返回的内容中查找第一个'{'和最后一个'}'，
            提取中间的JSON字符串进行解析。
        """
        # 构建数据提取的系统提示词
        system_prompt = f"""你是一个数据提取助手。请从用户输入的文本中提取以下字段，并以JSON格式返回：
字段列表: {', '.join(fields)}

请严格按照以下JSON格式返回结果：
{{{', '.join([f'"{field}": "提取的值"' for field in fields])}}}

如果某个字段无法从文本中提取，请将其值设为null。只返回JSON，不要包含其他说明文字。"""
        
        # 发送请求
        response = self.process_text(text, system_prompt)
        
        # 尝试解析JSON响应
        if response.success:
            try:
                content = response.data.get('content', '')
                # 查找JSON对象的边界
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    json_str = content[json_start:json_end]  # 提取JSON字符串
                    parsed_data = json.loads(json_str)  # 解析JSON
                    response.data['parsed'] = parsed_data  # 存储解析结果
            except json.JSONDecodeError:
                pass  # 解析失败时保持原样
        
        return response


# ------------------------------------------------------------------------------
# AI服务工厂函数
# 功能: 创建AI服务实例的便捷方法
# ------------------------------------------------------------------------------
def create_ai_service(config: AIConfig = None) -> AIService:
    """
    创建AI服务实例
    
    参数:
        config: AI配置实例(可选)，未提供时使用全局配置
    
    返回值:
        AIService: 配置好的AI服务实例
    
    使用场景:
        快速创建AI服务实例，无需手动导入配置。
    
    示例:
        service = create_ai_service()  # 使用默认配置
        service = create_ai_service(custom_config)  # 使用自定义配置
    """
    if config is None:
        from config import CONFIG
        config = CONFIG.ai  # 使用全局配置中的AI配置
    return AIService(config)
