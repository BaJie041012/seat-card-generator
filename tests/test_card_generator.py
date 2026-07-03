"""card_generator.py 单元测试"""
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch, mock_open
from dataclasses import dataclass

# 确保能导入 src 模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from card_generator import sanitize_filename, generate_quality_report


class TestSanitizeFilename(unittest.TestCase):
    """测试文件名安全处理"""

    def test_removes_illegal_chars(self):
        """移除非法字符"""
        result = sanitize_filename('file<>:"/\\|?*name')
        self.assertNotIn('<', result)
        self.assertNotIn('>', result)
        self.assertNotIn(':', result)
        self.assertNotIn('"', result)
        self.assertNotIn('/', result)
        self.assertNotIn('\\', result)
        self.assertNotIn('|', result)
        self.assertNotIn('?', result)
        self.assertNotIn('*', result)

    def test_truncates_long_names(self):
        """截断超长文件名"""
        long_name = 'a' * 100
        result = sanitize_filename(long_name)
        self.assertLessEqual(len(result), 50)

    def test_preserves_normal_names(self):
        """保留正常文件名"""
        result = sanitize_filename('正常文件名')
        self.assertEqual(result, '正常文件名')

    def test_empty_string(self):
        """空字符串"""
        result = sanitize_filename('')
        self.assertEqual(result, '')

    def test_chinese_chars_preserved(self):
        """中文字符保留"""
        result = sanitize_filename('张三的席卡')
        self.assertEqual(result, '张三的席卡')


@dataclass
class MockPersonInfo:
    """模拟 PersonInfo"""
    name: str
    company: str
    position: str


class TestGenerateQualityReport(unittest.TestCase):
    """测试质量报告生成"""

    def test_report_contains_header(self):
        """报告包含标题"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            report_path = f.name

        try:
            log_data = {
                'start_time': '2026-07-03T10:00:00',
                'event_name': '测试活动',
                'display_type': 'name',
                'total_persons': 3,
                'output_dir': '/tmp/output',
                'word_dir': '/tmp/output/word',
                'pdf_dir': '/tmp/output/pdf',
                'pdf_count': 2,
                'errors': [],
                'warnings': [],
            }
            generated_files = [
                {'filename': 'test.docx', 'valid': True},
                {'filename': 'test2.docx', 'valid': False, 'reason': '内容为空'},
            ]
            generate_quality_report(report_path, log_data, generated_files, ['失败者'])

            with open(report_path, 'r', encoding='utf-8') as f:
                content = f.read()

            self.assertIn('席卡生成质量报告', content)
            self.assertIn('测试活动', content)
            self.assertIn('test.docx', content)
            self.assertIn('失败者', content)
            self.assertIn('内容为空', content)
        finally:
            os.unlink(report_path)

    def test_report_with_warnings_and_errors(self):
        """报告包含警告和错误"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            report_path = f.name

        try:
            log_data = {
                'start_time': '2026-07-03T10:00:00',
                'event_name': '',
                'display_type': 'company',
                'total_persons': 1,
                'output_dir': '/tmp/output',
                'word_dir': '/tmp/output/word',
                'pdf_dir': '/tmp/output/pdf',
                'pdf_count': 0,
                'errors': ['错误信息1'],
                'warnings': ['警告信息1'],
            }
            generate_quality_report(report_path, log_data, [], [])

            with open(report_path, 'r', encoding='utf-8') as f:
                content = f.read()

            self.assertIn('警告信息1', content)
            self.assertIn('错误信息1', content)
        finally:
            os.unlink(report_path)


if __name__ == '__main__':
    unittest.main()