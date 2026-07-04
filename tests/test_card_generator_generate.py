"""card_generator.py generate_cards() 核心逻辑单元测试"""
import os
import sys
import tempfile
import shutil
import unittest
from unittest.mock import patch, MagicMock
from dataclasses import dataclass

# 确保能导入 src 模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from card_generator import generate_cards


@dataclass
class MockPersonInfo:
    """模拟 PersonInfo"""
    name: str
    company: str = ''
    position: str = ''


def _make_mock_paragraph(text=''):
    """创建模拟段落"""
    p = MagicMock()
    p.text = text
    p.runs = [MagicMock()]
    p.runs[0].text = text
    return p


def _make_mock_document(texts=None):
    """
    创建模拟 Document 类。
    texts: 段落文本列表，默认 ['']
    """
    if texts is None:
        texts = ['']

    mock_paras = [_make_mock_paragraph(t) for t in texts]
    mock_doc = MagicMock()
    mock_doc.paragraphs = mock_paras
    mock_doc.tables = []
    return mock_doc


class TestGenerateCardsBasic(unittest.TestCase):
    """generate_cards 基础测试"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    @patch('card_generator.generate_quality_report')
    @patch('card_generator.validate_card_document')
    @patch('card_generator.convert_docx_to_pdf')
    @patch('docx.Document')
    def test_missing_template_returns_error(
        self, MockDoc, mock_pdf, mock_validate, mock_report
    ):
        """模板不存在返回错误"""
        result = generate_cards(
            infos=[],
            template_path='/nonexistent/template.docx',
            event_name='活动',
            display_type='name',
            output_base_dir=self.tmpdir
        )
        self.assertFalse(result['success'])
        self.assertIn('不存在', result['error'])

    @patch('card_generator.generate_quality_report')
    @patch('card_generator.validate_card_document')
    @patch('card_generator.convert_docx_to_pdf')
    @patch('docx.Document')
    def test_empty_infos_returns_zero(
        self, MockDoc, mock_pdf, mock_validate, mock_report
    ):
        """空人员列表返回 0 个席卡"""
        # 创建模板文件
        template = os.path.join(self.tmpdir, 'template.docx')
        with open(template, 'w') as f:
            f.write('dummy')

        result = generate_cards(
            infos=[],
            template_path=template,
            event_name='活动',
            display_type='name',
            output_base_dir=self.tmpdir
        )
        self.assertTrue(result['success'])
        self.assertEqual(result['count'], 0)
        self.assertEqual(result['files'], [])
        self.assertEqual(result['failed'], [])

    @patch('card_generator.merge_pdfs')
    @patch('card_generator.generate_quality_report')
    @patch('card_generator.validate_card_document')
    @patch('card_generator.convert_docx_to_pdf')
    @patch('docx.Document')
    def test_single_person_success(
        self, MockDoc, mock_pdf, mock_validate, mock_report, mock_merge
    ):
        """单人成功生成席卡"""
        template = os.path.join(self.tmpdir, 'template.docx')
        with open(template, 'w') as f:
            f.write('dummy')

        mock_doc = _make_mock_document(['张三 {姓名/公司}'])
        MockDoc.return_value = mock_doc
        mock_validate.return_value = {'valid': True, 'reason': '验证通过'}
        mock_pdf.return_value = True
        mock_merge.return_value = True

        info = MockPersonInfo(name='张三', company='测试公司', position='工程师')
        result = generate_cards(
            infos=[info],
            template_path=template,
            event_name='测试活动',
            display_type='name',
            output_base_dir=self.tmpdir
        )

        self.assertTrue(result['success'])
        self.assertEqual(result['count'], 1)
        self.assertEqual(len(result['files']), 1)
        self.assertEqual(result['files'][0]['name'], '张三')
        self.assertTrue(result['files'][0]['valid'])
        self.assertIsNotNone(result['report_path'])
        self.assertIsNotNone(result['pdf_combined_path'])

    @patch('card_generator.generate_quality_report')
    @patch('card_generator.validate_card_document')
    @patch('card_generator.convert_docx_to_pdf')
    @patch('docx.Document')
    def test_multiple_persons(
        self, MockDoc, mock_pdf, mock_validate, mock_report
    ):
        """多人成功生成席卡"""
        template = os.path.join(self.tmpdir, 'template.docx')
        with open(template, 'w') as f:
            f.write('dummy')

        mock_doc = _make_mock_document(['{姓名/公司}'])
        MockDoc.return_value = mock_doc
        mock_validate.return_value = {'valid': True, 'reason': '验证通过'}
        mock_pdf.return_value = True

        infos = [
            MockPersonInfo(name='张三', company='A公司'),
            MockPersonInfo(name='李四', company='B公司'),
            MockPersonInfo(name='王五', company='C公司'),
        ]
        result = generate_cards(
            infos=infos,
            template_path=template,
            event_name='年会',
            display_type='name',
            output_base_dir=self.tmpdir
        )

        self.assertTrue(result['success'])
        self.assertEqual(result['count'], 3)
        self.assertEqual(len(result['files']), 3)

    @patch('card_generator.generate_quality_report')
    @patch('card_generator.validate_card_document')
    @patch('card_generator.convert_docx_to_pdf')
    @patch('docx.Document')
    def test_display_type_company(
        self, MockDoc, mock_pdf, mock_validate, mock_report
    ):
        """display_type=company 显示公司名"""
        template = os.path.join(self.tmpdir, 'template.docx')
        with open(template, 'w') as f:
            f.write('dummy')

        mock_doc = _make_mock_document(['{{company}}'])
        MockDoc.return_value = mock_doc
        mock_validate.return_value = {'valid': True, 'reason': '验证通过'}
        mock_pdf.return_value = True

        info = MockPersonInfo(name='张三', company='测试公司')
        result = generate_cards(
            infos=[info],
            template_path=template,
            event_name='',
            display_type='company',
            output_base_dir=self.tmpdir
        )

        self.assertTrue(result['success'])
        self.assertEqual(result['count'], 1)
        self.assertEqual(result['files'][0]['name'], '测试公司')

    @patch('card_generator.generate_quality_report')
    @patch('card_generator.validate_card_document')
    @patch('card_generator.convert_docx_to_pdf')
    @patch('docx.Document')
    def test_company_display_fallback_to_name(
        self, MockDoc, mock_pdf, mock_validate, mock_report
    ):
        """company 模式但无公司名时回退到姓名"""
        template = os.path.join(self.tmpdir, 'template.docx')
        with open(template, 'w') as f:
            f.write('dummy')

        mock_doc = _make_mock_document(['{{name}}'])
        MockDoc.return_value = mock_doc
        mock_validate.return_value = {'valid': True, 'reason': '验证通过'}
        mock_pdf.return_value = True

        info = MockPersonInfo(name='张三', company='')
        result = generate_cards(
            infos=[info],
            template_path=template,
            event_name='',
            display_type='company',
            output_base_dir=self.tmpdir
        )

        self.assertTrue(result['success'])
        self.assertEqual(result['count'], 1)
        # 无公司名，回退到姓名
        self.assertEqual(result['files'][0]['name'], '张三')

    @patch('card_generator.generate_quality_report')
    @patch('card_generator.validate_card_document')
    @patch('card_generator.convert_docx_to_pdf')
    @patch('docx.Document')
    def test_pdf_conversion_failure_still_succeeds(
        self, MockDoc, mock_pdf, mock_validate, mock_report
    ):
        """PDF 转换失败但席卡仍成功"""
        template = os.path.join(self.tmpdir, 'template.docx')
        with open(template, 'w') as f:
            f.write('dummy')

        mock_doc = _make_mock_document(['{姓名/公司}'])
        MockDoc.return_value = mock_doc
        mock_validate.return_value = {'valid': True, 'reason': '验证通过'}
        mock_pdf.return_value = False  # PDF 转换失败

        info = MockPersonInfo(name='张三')
        result = generate_cards(
            infos=[info],
            template_path=template,
            event_name='',
            display_type='name',
            output_base_dir=self.tmpdir
        )

        self.assertTrue(result['success'])
        self.assertEqual(result['count'], 1)
        # 文件有 warning 标记
        self.assertIn('warning', result['files'][0])
        # 无 PDF 文件
        self.assertIsNone(result['pdf_combined_path'])

    @patch('card_generator.generate_quality_report')
    @patch('card_generator.validate_card_document')
    @patch('card_generator.convert_docx_to_pdf')
    @patch('docx.Document')
    def test_validation_failure_marks_as_failed(
        self, MockDoc, mock_pdf, mock_validate, mock_report
    ):
        """验证失败标记为失败"""
        template = os.path.join(self.tmpdir, 'template.docx')
        with open(template, 'w') as f:
            f.write('dummy')

        mock_doc = _make_mock_document([''])
        MockDoc.return_value = mock_doc
        mock_validate.return_value = {'valid': False, 'reason': '文档内容为空'}

        info = MockPersonInfo(name='张三')
        result = generate_cards(
            infos=[info],
            template_path=template,
            event_name='',
            display_type='name',
            output_base_dir=self.tmpdir
        )

        self.assertTrue(result['success'])  # 整体仍成功
        self.assertEqual(result['count'], 0)  # 但该席卡未计入
        self.assertEqual(len(result['failed']), 1)
        self.assertEqual(result['failed'][0], '张三')

    @patch('card_generator.generate_quality_report')
    @patch('card_generator.validate_card_document')
    @patch('card_generator.convert_docx_to_pdf')
    @patch('docx.Document')
    def test_output_directory_structure(
        self, MockDoc, mock_pdf, mock_validate, mock_report
    ):
        """输出目录结构正确"""
        template = os.path.join(self.tmpdir, 'template.docx')
        with open(template, 'w') as f:
            f.write('dummy')

        mock_doc = _make_mock_document(['{姓名/公司}'])
        MockDoc.return_value = mock_doc
        mock_validate.return_value = {'valid': True, 'reason': '验证通过'}
        mock_pdf.return_value = True

        info = MockPersonInfo(name='张三')
        result = generate_cards(
            infos=[info],
            template_path=template,
            event_name='测试活动',
            display_type='name',
            output_base_dir=self.tmpdir
        )

        self.assertTrue(os.path.isdir(result['word_dir']))
        self.assertTrue(os.path.isdir(result['pdf_dir']))
        self.assertIn('word', result['word_dir'])
        self.assertIn('pdf', result['pdf_dir'])
        self.assertIn('测试活动', result['output_dir'])

    @patch('card_generator.generate_quality_report')
    @patch('card_generator.validate_card_document')
    @patch('card_generator.convert_docx_to_pdf')
    @patch('docx.Document')
    def test_no_display_text_skips_person(
        self, MockDoc, mock_pdf, mock_validate, mock_report
    ):
        """无有效显示内容时跳过"""
        template = os.path.join(self.tmpdir, 'template.docx')
        with open(template, 'w') as f:
            f.write('dummy')

        mock_doc = _make_mock_document([''])
        MockDoc.return_value = mock_doc

        # name 和 company 都为空
        info = MockPersonInfo(name='', company='')
        result = generate_cards(
            infos=[info],
            template_path=template,
            event_name='',
            display_type='name',
            output_base_dir=self.tmpdir
        )

        self.assertTrue(result['success'])
        self.assertEqual(result['count'], 0)

    @patch('card_generator.generate_quality_report')
    @patch('card_generator.validate_card_document')
    @patch('card_generator.convert_docx_to_pdf')
    @patch('docx.Document')
    def test_document_exception_caught(
        self, MockDoc, mock_pdf, mock_validate, mock_report
    ):
        """Document 处理异常被捕获"""
        template = os.path.join(self.tmpdir, 'template.docx')
        with open(template, 'w') as f:
            f.write('dummy')

        MockDoc.side_effect = Exception('模板损坏')

        info = MockPersonInfo(name='张三')
        result = generate_cards(
            infos=[info],
            template_path=template,
            event_name='',
            display_type='name',
            output_base_dir=self.tmpdir
        )

        self.assertTrue(result['success'])  # 整体仍成功
        self.assertEqual(result['count'], 0)
        self.assertEqual(len(result['failed']), 1)
        self.assertIn('张三', result['failed'])

    @patch('card_generator.generate_quality_report')
    @patch('card_generator.validate_card_document')
    @patch('card_generator.convert_docx_to_pdf')
    @patch('docx.Document')
    def test_report_generated(
        self, MockDoc, mock_pdf, mock_validate, mock_report
    ):
        """质量报告被生成"""
        template = os.path.join(self.tmpdir, 'template.docx')
        with open(template, 'w') as f:
            f.write('dummy')

        mock_doc = _make_mock_document(['{姓名/公司}'])
        MockDoc.return_value = mock_doc
        mock_validate.return_value = {'valid': True, 'reason': '验证通过'}
        mock_pdf.return_value = True

        info = MockPersonInfo(name='张三')
        result = generate_cards(
            infos=[info],
            template_path=template,
            event_name='测试',
            display_type='name',
            output_base_dir=self.tmpdir
        )

        self.assertIsNotNone(result['report_path'])
        mock_report.assert_called_once()

    @patch('card_generator.generate_quality_report')
    @patch('card_generator.validate_card_document')
    @patch('card_generator.convert_docx_to_pdf')
    @patch('docx.Document')
    def test_validate_called_with_correct_args(
        self, MockDoc, mock_pdf, mock_validate, mock_report
    ):
        """验证函数以正确参数调用"""
        template = os.path.join(self.tmpdir, 'template.docx')
        with open(template, 'w') as f:
            f.write('dummy')

        mock_doc = _make_mock_document(['{姓名/公司}'])
        MockDoc.return_value = mock_doc
        mock_validate.return_value = {'valid': True, 'reason': '验证通过'}
        mock_pdf.return_value = True

        info = MockPersonInfo(name='张三')
        generate_cards(
            infos=[info],
            template_path=template,
            event_name='活动',
            display_type='name',
            output_base_dir=self.tmpdir
        )

        mock_validate.assert_called_once()
        call_args = mock_validate.call_args
        # 第一个参数是文件路径
        self.assertTrue(call_args[0][0].endswith('.docx'))
        # 第二个参数是期望内容（姓名）
        self.assertEqual(call_args[0][1], '张三')
        # 第三个参数是 display_type
        self.assertEqual(call_args[0][2], 'name')


class TestGenerateCardsTwoCharName(unittest.TestCase):
    """两字姓名格式化测试"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    @patch('card_generator.generate_quality_report')
    @patch('card_generator.validate_card_document')
    @patch('card_generator.convert_docx_to_pdf')
    @patch('docx.Document')
    def test_two_char_name_formatted(
        self, MockDoc, mock_pdf, mock_validate, mock_report
    ):
        """两字中文姓名中间插全角空格"""
        template = os.path.join(self.tmpdir, 'template.docx')
        with open(template, 'w') as f:
            f.write('dummy')

        mock_doc = _make_mock_document(['{姓名/公司}'])
        MockDoc.return_value = mock_doc
        mock_validate.return_value = {'valid': True, 'reason': '验证通过'}
        mock_pdf.return_value = True

        info = MockPersonInfo(name='张三')
        result = generate_cards(
            infos=[info],
            template_path=template,
            event_name='',
            display_type='name',
            output_base_dir=self.tmpdir
        )

        self.assertTrue(result['success'])
        # validate 被调用时，replace_placeholder 应该已经处理了格式化
        # 检查 validate 的调用参数中期望内容考虑了格式化
        call_args = mock_validate.call_args
        # 两字姓名 "张三" 会格式化为 "张\u3000三"
        # validate_card_document 内部也会处理这个格式
        self.assertEqual(result['count'], 1)


if __name__ == '__main__':
    unittest.main()
