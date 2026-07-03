"""ai_service.py 单元测试"""
import os
import sys
import json
import unittest
from unittest.mock import patch, MagicMock
from dataclasses import dataclass

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ai_service import AIResponse, AIService, AIServiceError, create_ai_service


@dataclass
class MockAIConfig:
    api_key: str = "test-key-123"
    api_base_url: str = "https://api.test.com/v1"
    model: str = "test-model"
    max_tokens: int = 1000
    temperature: float = 0.7
    timeout: int = 10


class TestAIResponse(unittest.TestCase):
    """测试 AIResponse 数据类"""

    def test_success_response(self):
        resp = AIResponse(success=True, data={"content": "hello"}, error_message="", raw_response="{}")
        self.assertTrue(resp.success)
        self.assertEqual(resp.data["content"], "hello")

    def test_failure_response(self):
        resp = AIResponse(success=False, data={}, error_message="API error")
        self.assertFalse(resp.success)
        self.assertEqual(resp.error_message, "API error")


class TestAIServiceError(unittest.TestCase):
    """测试 AIServiceError 异常类"""

    def test_can_raise(self):
        with self.assertRaises(AIServiceError):
            raise AIServiceError("test error")


class TestBuildHeaders(unittest.TestCase):
    """测试 _build_headers"""

    def test_contains_auth(self):
        config = MockAIConfig(api_key="my-key")
        service = AIService(config)
        headers = service._build_headers()
        self.assertEqual(headers["Authorization"], "Bearer my-key")
        self.assertEqual(headers["Content-Type"], "application/json")


class TestBuildRequestBody(unittest.TestCase):
    """测试 _build_request_body"""

    def test_without_system_prompt(self):
        config = MockAIConfig()
        service = AIService(config)
        body = service._build_request_body("Hello")
        self.assertEqual(len(body["messages"]), 1)
        self.assertEqual(body["messages"][0]["role"], "user")
        self.assertEqual(body["messages"][0]["content"], "Hello")
        self.assertEqual(body["model"], "test-model")

    def test_with_system_prompt(self):
        config = MockAIConfig()
        service = AIService(config)
        body = service._build_request_body("Hello", system_prompt="You are helpful")
        self.assertEqual(len(body["messages"]), 2)
        self.assertEqual(body["messages"][0]["role"], "system")
        self.assertEqual(body["messages"][1]["role"], "user")


class TestRateLimit(unittest.TestCase):
    """测试 _rate_limit"""

    @patch('time.sleep')
    @patch('time.time')
    def test_sleeps_when_too_fast(self, mock_time, mock_sleep):
        config = MockAIConfig()
        service = AIService(config)
        service.last_request_time = 100.0
        service.min_request_interval = 0.5

        mock_time.side_effect = [100.1, 100.6]  # 第一次调用: elapsed=0.1, 第二次: 更新
        service._rate_limit()
        mock_sleep.assert_called_once_with(0.4)  # 0.5 - 0.1 = 0.4

    @patch('time.sleep')
    @patch('time.time')
    def test_no_sleep_when_enough_time(self, mock_time, mock_sleep):
        config = MockAIConfig()
        service = AIService(config)
        service.last_request_time = 100.0
        service.min_request_interval = 0.5

        mock_time.side_effect = [101.0, 101.0]  # elapsed=1.0 > 0.5
        service._rate_limit()
        mock_sleep.assert_not_called()


class TestProcessText(unittest.TestCase):
    """测试 process_text"""

    def test_returns_error_without_api_key(self):
        config = MockAIConfig(api_key="")
        service = AIService(config)
        response = service.process_text("Hello")
        self.assertFalse(response.success)
        self.assertIn("API key", response.error_message)

    @patch.object(AIService, '_make_request')
    @patch('time.sleep')
    def test_retries_on_failure(self, mock_sleep, mock_request):
        config = MockAIConfig()
        service = AIService(config)

        fail_response = AIResponse(success=False, data={}, error_message="timeout")
        success_response = AIResponse(success=True, data={"content": "result"})

        mock_request.side_effect = [fail_response, success_response]
        response = service.process_text("Hello", retry_count=0)
        self.assertTrue(response.success)
        self.assertEqual(mock_request.call_count, 2)

    @patch.object(AIService, '_make_request')
    def test_success_no_retry(self, mock_request):
        config = MockAIConfig()
        service = AIService(config)

        success_response = AIResponse(success=True, data={"content": "result"})
        mock_request.return_value = success_response

        response = service.process_text("Hello")
        self.assertTrue(response.success)
        mock_request.assert_called_once()


class TestExtractStructuredData(unittest.TestCase):
    """测试 extract_structured_data"""

    @patch.object(AIService, 'process_text')
    def test_parses_json_from_response(self, mock_process):
        config = MockAIConfig()
        service = AIService(config)

        mock_process.return_value = AIResponse(
            success=True,
            data={"content": '{"name": "张三", "company": "公司A"}'}
        )

        response = service.extract_structured_data("张三在公司A工作", ["name", "company"])
        self.assertTrue(response.success)
        self.assertIn("parsed", response.data)
        self.assertEqual(response.data["parsed"]["name"], "张三")

    @patch.object(AIService, 'process_text')
    def test_handles_invalid_json(self, mock_process):
        config = MockAIConfig()
        service = AIService(config)

        mock_process.return_value = AIResponse(
            success=True,
            data={"content": "not json at all"}
        )

        response = service.extract_structured_data("text", ["name"])
        self.assertTrue(response.success)
        self.assertNotIn("parsed", response.data)


class TestCreateAIService(unittest.TestCase):
    """测试 create_ai_service 工厂函数"""

    def test_creates_with_config(self):
        config = MockAIConfig()
        service = create_ai_service(config)
        self.assertIsInstance(service, AIService)
        self.assertEqual(service.config, config)


if __name__ == '__main__':
    unittest.main()