"""test_card_generator.py - generate_cards() 核心流程补充测试

在已有 sanitize_filename / generate_quality_report 测试基础上，
新增对 generate_cards() 主流程的覆盖:
  - 成功生成 / 目录结构 / 返回值
  - 模板不存在
  - 空显示内容跳过
  - 重名文件处理
  - PDF 转换成功/失败
  - 验证失败
  - 公司名显示模式
  - 多人批量生成
  - python-docx 缺失
  - 单人异常不影响整体
"""
import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock, call
from dataclasses import dataclass

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from card_generator import generate_cards


@dataclass
class MockPersonInfo:
    """模拟 PersonInfo"""
    name: str
    company: str = ''
    position: str = ''


def _make_mock_doc():
    """创建一个模拟的 python-docx Document 对象"""
    mock_doc = MagicMock()
    mock_doc.paragraphs = []
    mock_doc.tables = []
    return mock_doc


class TestGenerateCardsSuccess(unittest.TestCase):
    """generate_cards 成功场景"""

    @patch('card_generator.generate_quality_report')
    @patch('card_generator.convert_docx_to_pdf', return_value=True)
    @patch('card_generator.validate_card_document', return_value={'valid': True, 'reason': 'OK'})
    @patch('card_generator.Document')
    def test_basic_success(self, MockDoc, mock_validate, mock_pdf, mock_report):
        MockDoc.return_value = _make_mock_doc()

        with tempfile.TemporaryDirectory() as td:
            tpl = os.path.join(td, 'template.docx')
            open(tpl, 'w').close()

            result = generate_cards(
                [MockPersonInfo(name='张三')],
                tpl, '测试活动', 'name', td
            )

        self.assertTrue(result['success'])
        self.assertEqual(result['count'], 1)
        self.assertTrue(os.path.isdir(result['word_dir']))
        self.assertTrue(os.path.isdir(result['pdf_dir']))
        self.assertEqual(len(result['files']), 1)
        self.assertTrue(result['files'][0]['valid'])
        self.assertIn('pdf_filepath', result['files'][0])
        self.assertIsNotNone(result['report_path'])

    @patch('card_generator.generate_quality_report')
    @patch('card_generator.convert_docx_to_pdf', return_value=True)
    @patch('card_generator.validate_card_document', return_value={'valid': True, 'reason': 'OK'})
    @patch('card_generator.Document')
    def test_output_dir_structure(self, MockDoc, mock_validate, mock_pdf, mock_report):
        """验证输出目录包含 word/ 和 pdf/ 子目录"""
        MockDoc.return_value = _make_mock_doc()

        with tempfile.TemporaryDirectory() as td:
            tpl = os.path.join(td, 'template.docx')
            open(tpl, 'w').close()

            result = generate_cards(
                [MockPersonInfo(name='李四')],
                tpl, '年会', 'name', td
            )

            self.assertIn('word', result['word_dir'])
            self.assertIn('pdf', result['pdf_dir'])
            self.assertTrue(result['output_dir'].startswith(td))

    @patch('card_generator.generate_quality_report')
    @patch('card_generator.convert_docx_to_pdf', return_value=True)
    @patch('card_generator.validate_card_document', return_value={'valid': True, 'reason': 'OK'})
    @patch('card_generator.Document')
    def test_pdf_combined_generated(self, MockDoc, mock_validate, mock_pdf, mock_report):
        """多人时生成 PDF 合集"""
        MockDoc.return_value = _make_mock_doc()

        with tempfile.TemporaryDirectory() as td:
            tpl = os.path.join(td, 'template.docx')
            open(tpl, 'w').close()

            result = generate_cards(
                [MockPersonInfo(name='张三'), MockPersonInfo(name='李四')],
                tpl, '活动', 'name', td
            )

            self.assertEqual(result['count'], 2)
            self.assertIsNotNone(result['pdf_combined_path'])


class TestGenerateCardsErrors(unittest.TestCase):
    """generate_cards 错误/边界场景"""

    def test_template_not_found(self):
        result = generate_cards(
            [MockPersonInfo(name='张三')],
            '/nonexistent/template.docx', '活动', 'name', '/tmp'
        )
        self.assertFalse(result['success'])
        self.assertIn('模板文件不存在', result['error'])

    @patch('card_generator.generate_quality_report')
    @patch('card_generator.convert_docx_to_pdf', return_value=True)
    @patch('card_generator.validate_card_document', return_value={'valid': True, 'reason': 'OK'})
    @patch('card_generator.Document')
    def test_empty_display_text_skipped(self, MockDoc, mock_validate, mock_pdf, mock_report):
        """显示内容为空时跳过该记录"""
        MockDoc.return_value = _make_mock_doc()

        with tempfile.TemporaryDirectory() as td:
            tpl = os.path.join(td, 'template.docx')
            open(tpl, 'w').close()

            result = generate_cards(
                [MockPersonInfo(name='', company='')],
                tpl, '活动', 'name', td
            )

            self.assertTrue(result['success'])
            self.assertEqual(result['count'], 0)
            self.assertTrue(len(result['log']['warnings']) > 0)

    @patch('card_generator.generate_quality_report')
    @patch('card_generator.convert_docx_to_pdf', return_value=True)
    @patch('card_generator.validate_card_document', return_value={'valid': True, 'reason': 'OK'})
    @patch('card_generator.Document')
    def test_duplicate_filename_handling(self, MockDoc, mock_validate, mock_pdf, mock_report):
        """重名时自动添加序号后缀"""
        mock_doc = _make_mock_doc()
        MockDoc.return_value = mock_doc

        with tempfile.TemporaryDirectory() as td:
            tpl = os.path.join(td, 'template.docx')
            open(tpl, 'w').close()

            # 预先创建同名文件，迫使计数器递增
            word_dir_placeholder = os.path.join(td, 'placeholder')
            os.makedirs(word_dir_placeholder)

            result = generate_cards(
                [MockPersonInfo(name='张三'), MockPersonInfo(name='张三')],
                tpl, '活动', 'name', td
            )

            self.assertTrue(result['success'])
            self.assertEqual(result['count'], 2)
            names = [f['filename'] for f in result['files']]
            # 两个文件名应不同
            self.assertNotEqual(names[0], names[1])

    @patch('card_generator.generate_quality_report')
    @patch('card_generator.convert_docx_to_pdf', return_value=False)
    @patch('card_generator.validate_card_document', return_value={'valid': True, 'reason': 'OK'})
    @patch('card_generator.Document')
    def test_pdf_conversion_failure_recorded(self, MockDoc, mock_validate, mock_pdf, mock_report):
        """PDF 转换失败时文件仍标记有效，但无 pdf_filepath"""
        MockDoc.return_value = _make_mock_doc()

        with tempfile.TemporaryDirectory() as td:
            tpl = os.path.join(td, 'template.docx')
            open(tpl, 'w').close()

            result = generate_cards(
                [MockPersonInfo(name='王五')],
                tpl, '活动', 'name', td
            )

            self.assertTrue(result['success'])
            self.assertEqual(result['count'], 1)
            self.assertNotIn('pdf_filepath', result['files'][0])
            self.assertIn('warning', result['files'][0])

    @patch('card_generator.generate_quality_report')
    @patch('card_generator.convert_docx_to_pdf', return_value=True)
    @patch('card_generator.validate_card_document', return_value={'valid': False, 'reason': '文档为空'})
    @patch('card_generator.Document')
    def test_validation_failure(self, MockDoc, mock_validate, mock_pdf, mock_report):
        """文档验证失败时记录到 failed 列表"""
        MockDoc.return_value = _make_mock_doc()

        with tempfile.TemporaryDirectory() as td:
            tpl = os.path.join(td, 'template.docx')
            open(tpl, 'w').close()

            result = generate_cards(
                [MockPersonInfo(name='赵六')],
                tpl, '活动', 'name', td
            )

            self.assertTrue(result['success'])  # 整体仍成功
            self.assertEqual(result['count'], 0)
            self.assertIn('赵六', result['failed'])
            self.assertFalse(result['files'][0]['valid'])

    @patch('card_generator.generate_quality_report')
    @patch('card_generator.convert_docx_to_pdf', return_value=True)
    @patch('card_generator.validate_card_document', return_value={'valid': True, 'reason': 'OK'})
    @patch('card_generator.Document')
    def test_company_display_type(self, MockDoc, mock_validate, mock_pdf, mock_report):
        """公司名显示模式"""
        MockDoc.return_value = _make_mock_doc()

        with tempfile.TemporaryDirectory() as td:
            tpl = os.path.join(td, 'template.docx')
            open(tpl, 'w').close()

            result = generate_cards(
                [MockPersonInfo(name='张三', company='测试公司')],
                tpl, '活动', 'company', td
            )

            self.assertTrue(result['success'])
            self.assertEqual(result['count'], 1)
            self.assertIn('测试公司', result['files'][0]['filename'])

    @patch('card_generator.generate_quality_report')
    @patch('card_generator.convert_docx_to_pdf', return_value=True)
    @patch('card_generator.validate_card_document', return_value={'valid': True, 'reason': 'OK'})
    @patch('card_generator.Document')
    def test_multiple_persons(self, MockDoc, mock_validate, mock_pdf, mock_report):
        """多人批量生成"""
        MockDoc.return_value = _make_mock_doc()

        persons = [
            MockPersonInfo(name='张三', company='A公司', position='工程师'),
            MockPersonInfo(name='李四', company='B公司', position='设计师'),
            MockPersonInfo(name='王五', company='C公司', position='产品经理'),
        ]

        with tempfile.TemporaryDirectory() as td:
            tpl = os.path.join(td, 'template.docx')
            open(tpl, 'w').close()

            result = generate_cards(persons, tpl, '年会', 'name', td)

            self.assertTrue(result['success'])
            self.assertEqual(result['count'], 3)
            self.assertEqual(len(result['files']), 3)
            self.assertEqual(result['failed'], [])

    def test_import_error_handling(self):
        """python-docx 未安装时返回友好错误"""
        with patch('card_generator.Document', side_effect=ImportError('No module')):
            # generate_cards 内部 from docx import Document 会触发 ImportError
            # 但由于 Document 在函数内部 import，需要让函数内的 import 失败
            pass

        # 更准确的方式：直接 patch 内置 __import__ 过于复杂，
        # 改为验证 ImportError 分支的返回格式
        with tempfile.TemporaryDirectory() as td:
            tpl = os.path.join(td, 'template.docx')
            open(tpl, 'w').close()

            # 模拟 Document 在函数体内 import 失败
            original_import = __builtins__.__import__ if hasattr(__builtins__, '__import__') else __import__

            def selective_import(name, *args, **kwargs):
                if name == 'docx':
                    raise ImportError('No module named docx')
                return original_import(name, *args, **kwargs)

            with patch('builtins.__import__', side_effect=selective_import):
                result = generate_cards(
                    [MockPersonInfo(name='张三')],
                    tpl, '活动', 'name', td
                )

            self.assertFalse(result['success'])
            self.assertIn('python-docx', result['error'])

    @patch('card_generator.generate_quality_report')
    @patch('card_generator.convert_docx_to_pdf', return_value=True)
    @patch('card_generator.validate_card_document', return_value={'valid': True, 'reason': 'OK'})
    @patch('card_generator.Document')
    def test_single_person_exception_doesnt_crash(self, MockDoc, mock_validate, mock_pdf, mock_report):
        """单人异常不影响其他人"""
        def side_effect(*args, **kwargs):
            raise RuntimeError('模拟异常')

        call_count = [0]
        def doc_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise RuntimeError('模拟异常')
            return _make_mock_doc()

        MockDoc.side_effect = doc_side_effect

        with tempfile.TemporaryDirectory() as td:
            tpl = os.path.join(td, 'template.docx')
            open(tpl, 'w').close()

            result = generate_cards(
                [MockPersonInfo(name='张三'), MockPersonInfo(name='李四')],
                tpl, '活动', 'name', td
            )

            self.assertTrue(result['success'])
            self.assertEqual(result['count'], 1)  # 第一个失败，第二个成功
            self.assertIn('张三', result['failed'])
            self.assertEqual(len(result['files']), 1)
            self.assertEqual(result['files'][0]['name'], '李四')


if __name__ == '__main__':
    unittest.main()
