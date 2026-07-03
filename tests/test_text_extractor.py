"""text_extractor.py 单元测试"""
import os
import sys
import json
import unittest
from unittest.mock import MagicMock
from dataclasses import dataclass

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from text_extractor import PersonInfo, AIExtractor, create_extractor


class TestPersonInfo(unittest.TestCase):
    """测试 PersonInfo 数据类"""

    def test_creation(self):
        info = PersonInfo(name='张三', company='公司A', position='工程师', original_line='原始行')
        self.assertEqual(info.name, '张三')
        self.assertEqual(info.company, '公司A')
        self.assertEqual(info.position, '工程师')
        self.assertEqual(info.original_line, '原始行')

    def test_default_values(self):
        info = PersonInfo(name='李四', company='', position='', original_line='')
        self.assertEqual(info.name, '李四')
        self.assertEqual(info.company, '')


class TestParseAIResponse(unittest.TestCase):
    """测试 _parse_ai_response"""

    def setUp(self):
        self.extractor = AIExtractor()

    def test_valid_json(self):
        content = '[{"name": "张三", "company": "公司A", "position": "工程师"}]'
        results = self.extractor._parse_ai_response(content)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, '张三')
        self.assertEqual(results[0].company, '公司A')

    def test_json_with_surrounding_text(self):
        content = '以下是提取结果：\n[{"name": "李四", "company": "公司B", "position": ""}]\n希望这有帮助。'
        results = self.extractor._parse_ai_response(content)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, '李四')

    def test_multiple_entries(self):
        content = '[{"name": "A", "company": "C1", "position": "P1"}, {"name": "B", "company": "C2", "position": "P2"}]'
        results = self.extractor._parse_ai_response(content)
        self.assertEqual(len(results), 2)

    def test_invalid_json(self):
        content = '这不是JSON'
        results = self.extractor._parse_ai_response(content)
        self.assertEqual(results, [])

    def test_empty_content(self):
        results = self.extractor._parse_ai_response('')
        self.assertEqual(results, [])

    def test_missing_fields(self):
        content = '[{"name": "张三"}]'
        results = self.extractor._parse_ai_response(content)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].company, '')
        self.assertEqual(results[0].position, '')


class TestFallbackParse(unittest.TestCase):
    """测试 _fallback_parse"""

    def setUp(self):
        self.extractor = AIExtractor()

    def test_comma_separated(self):
        results = self.extractor._fallback_parse('张三，李四，王五')
        names = [r.name for r in results]
        self.assertIn('张三', names)
        self.assertIn('李四', names)

    def test_newline_separated(self):
        results = self.extractor._fallback_parse('张三\n李四\n王五')
        self.assertEqual(len(results), 3)

    def test_deduplication(self):
        results = self.extractor._fallback_parse('张三，张三，李四')
        names = [r.name for r in results]
        self.assertEqual(names.count('张三'), 1)

    def test_strips_numbering(self):
        results = self.extractor._fallback_parse('1. 张三\n2. 李四')
        names = [r.name for r in results]
        self.assertIn('张三', names)
        self.assertNotIn('1.', names)

    def test_filters_short_names(self):
        results = self.extractor._fallback_parse('张，张三，李四')
        names = [r.name for r in results]
        self.assertNotIn('张', names)  # 单字名被过滤

    def test_empty_input(self):
        results = self.extractor._fallback_parse('')
        self.assertEqual(results, [])


class TestExtractFromText(unittest.TestCase):
    """测试 extract_from_text（使用 Mock AI 服务）"""

    def test_raises_without_ai_service(self):
        extractor = AIExtractor()
        with self.assertRaises(ValueError):
            extractor.extract_from_text('张三，公司A')

    def test_successful_extraction(self):
        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.success = True
        mock_response.data = {'content': '[{"name": "张三", "company": "公司A", "position": "工程师"}]'}
        mock_service.process_text.return_value = mock_response

        extractor = AIExtractor(mock_service)
        results = extractor.extract_from_text('张三，公司A，工程师')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, '张三')

    def test_fallback_on_empty_ai_result(self):
        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.success = True
        mock_response.data = {'content': '无法提取'}
        mock_service.process_text.return_value = mock_response

        extractor = AIExtractor(mock_service)
        results = extractor.extract_from_text('张三，李四')
        # 回退到 fallback_parse
        self.assertTrue(len(results) >= 1)

    def test_raises_on_ai_failure(self):
        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.success = False
        mock_response.error_message = 'API error'
        mock_service.process_text.return_value = mock_response

        extractor = AIExtractor(mock_service)
        with self.assertRaises(RuntimeError):
            extractor.extract_from_text('张三')


class TestCreateExtractor(unittest.TestCase):
    """测试 create_extractor 工厂函数"""

    def test_creates_extractor(self):
        extractor = create_extractor()
        self.assertIsInstance(extractor, AIExtractor)

    def test_creates_with_service(self):
        mock_service = MagicMock()
        extractor = create_extractor(mock_service)
        self.assertEqual(extractor.ai_service, mock_service)


if __name__ == '__main__':
    unittest.main()