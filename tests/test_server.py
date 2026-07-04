"""test_server.py - server.py API 端点单元测试

覆盖:
  - GET /api/health 健康检查
  - GET /api/templates 模板列表
  - GET /api/output 输出目录
  - POST /api/generate-cards 席卡生成 (成功/各种错误)
  - GET /download/{file_id} 文件下载 (成功/过期/文件丢失)
"""
import os
import sys
import unittest
import tempfile
from unittest.mock import patch, MagicMock
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# 在导入 server 之前，将项目模块替换为 mock，
# 避免 server.py 模块级代码触发真实 I/O 和依赖加载。
# ---------------------------------------------------------------------------
_original_modules = {}
for _mod_name in ['config', 'ai_service', 'text_extractor', 'card_generator']:
    if _mod_name in sys.modules:
        _original_modules[_mod_name] = sys.modules.pop(_mod_name)

# -- mock config --
_mock_config = MagicMock()
_mock_config.ai.api_key = 'test-key-123'
_mock_config.ai.api_base_url = 'http://mock-api'
_mock_config.ai.model = 'mock-model'
_mock_config.ai.max_tokens = 1000
_mock_config.ai.temperature = 0.7
_mock_config.ai.timeout = 30
_mock_config.template.template_dir = tempfile.mkdtemp()
_mock_config.template.output_dir = tempfile.mkdtemp()
_mock_config.template.default_template = '席卡模板v4.docx'
_mock_config.template.supported_formats = ['.docx']

_mock_config_module = MagicMock()
_mock_config_module.CONFIG = _mock_config
_mock_config_module.ensure_directories = MagicMock()
sys.modules['config'] = _mock_config_module

# -- mock ai_service --
_mock_ai_module = MagicMock()
sys.modules['ai_service'] = _mock_ai_module

# -- mock text_extractor --
_mock_extractor_module = MagicMock()
sys.modules['text_extractor'] = _mock_extractor_module

# -- mock card_generator --
_mock_cg_module = MagicMock()
sys.modules['card_generator'] = _mock_cg_module

# 现在安全导入 server 模块
from app.server import app, file_download_map

try:
    from fastapi.testclient import TestClient
    HAS_TEST_CLIENT = True
except ImportError:
    HAS_TEST_CLIENT = False


@dataclass
class MockPersonInfo:
    """模拟 PersonInfo 数据类"""
    name: str
    company: str = ''
    position: str = ''


@unittest.skipUnless(HAS_TEST_CLIENT, '需要 fastapi[all] 或 httpx')
class TestHealthCheck(unittest.TestCase):
    """/api/health 健康检查"""

    def setUp(self):
        self.client = TestClient(app)

    def test_health_returns_ok(self):
        resp = self.client.get('/api/health')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['status'], 'ok')
        self.assertIn('time', data)


@unittest.skipUnless(HAS_TEST_CLIENT, '需要 fastapi[all] 或 httpx')
class TestGetTemplates(unittest.TestCase):
    """/api/templates 模板列表"""

    def setUp(self):
        self.client = TestClient(app)
        self._td = tempfile.mkdtemp()
        _mock_config.template.template_dir = self._td

    def test_empty_dir(self):
        resp = self.client.get('/api/templates')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['templates'], [])

    def test_filters_supported_extensions(self):
        for name in ['模板v4.docx', '模板v5.docx', 'readme.txt', 'data.pdf', 'image.png', 'script.py']:
            open(os.path.join(self._td, name), 'w').close()
        resp = self.client.get('/api/templates')
        data = resp.json()
        self.assertTrue(data['success'])
        self.assertEqual(sorted(data['templates']),
                         sorted(['模板v4.docx', '模板v5.docx', 'readme.txt', 'data.pdf']))

    def test_nonexistent_dir(self):
        _mock_config.template.template_dir = '/nonexistent/path/xyz'
        resp = self.client.get('/api/templates')
        data = resp.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['templates'], [])


@unittest.skipUnless(HAS_TEST_CLIENT, '需要 fastapi[all] 或 httpx')
class TestGetOutput(unittest.TestCase):
    """/api/output 输出目录"""

    def setUp(self):
        self.client = TestClient(app)
        self._td = tempfile.mkdtemp()
        _mock_config.template.output_dir = self._td

    def test_empty_output_dir(self):
        resp = self.client.get('/api/output')
        data = resp.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['files'], [])

    def test_lists_files_with_size(self):
        fp = os.path.join(self._td, 'test_output.txt')
        with open(fp, 'w') as f:
            f.write('hello world')
        resp = self.client.get('/api/output')
        data = resp.json()
        self.assertTrue(data['success'])
        self.assertEqual(len(data['files']), 1)
        self.assertEqual(data['files'][0]['path'], 'test_output.txt')
        self.assertGreater(data['files'][0]['size'], 0)

    def test_nonexistent_output_dir(self):
        _mock_config.template.output_dir = '/nonexistent/output/xyz'
        resp = self.client.get('/api/output')
        data = resp.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['files'], [])


@unittest.skipUnless(HAS_TEST_CLIENT, '需要 fastapi[all] 或 httpx')
class TestGenerateCards(unittest.TestCase):
    """/api/generate-cards 席卡生成"""

    def setUp(self):
        # 重置 server 全局状态
        import app.server as srv
        srv.ai_service = None
        srv.extractor = None
        srv.file_download_map.clear()
        self.client = TestClient(app)
        self._td = tempfile.mkdtemp()
        _mock_config.template.template_dir = self._td
        _mock_config.template.output_dir = tempfile.mkdtemp()

    # -- 参数校验 --
    def test_empty_text_returns_400(self):
        resp = self.client.post('/api/generate-cards',
                                json={'text': '', 'event_name': '测试'})
        self.assertEqual(resp.status_code, 400)
        self.assertIn('人员信息', resp.json()['detail'])

    def test_whitespace_only_text_returns_400(self):
        resp = self.client.post('/api/generate-cards',
                                json={'text': '   \n\t  '})
        self.assertEqual(resp.status_code, 400)

    def test_template_not_found_returns_404(self):
        resp = self.client.post('/api/generate-cards',
                                json={'text': '张三', 'template': '不存在的模板.docx'})
        self.assertEqual(resp.status_code, 404)
        self.assertIn('模板文件不存在', resp.json()['detail'])

    def test_invalid_template_extension_returns_400(self):
        open(os.path.join(self._td, '模板.txt'), 'w').close()
        resp = self.client.post('/api/generate-cards',
                                json={'text': '张三', 'template': '模板.txt'})
        self.assertEqual(resp.status_code, 400)
        self.assertIn('.docx', resp.json()['detail'])

    # -- AI 密钥 --
    def test_missing_api_key_returns_500(self):
        _mock_config.ai.api_key = ''
        try:
            resp = self.client.post('/api/generate-cards', json={'text': '张三'})
            self.assertEqual(resp.status_code, 500)
            self.assertIn('API密钥', resp.json()['detail'])
        finally:
            _mock_config.ai.api_key = 'test-key-123'

    # -- 成功场景 --
    @patch('app.server.generate_cards')
    @patch('app.server.create_extractor')
    @patch('app.server.create_ai_service')
    def test_successful_generation(self, mock_cas, mock_ce, mock_gc):
        mock_ext = MagicMock()
        mock_ext.extract_from_text.return_value = [MockPersonInfo(name='张三')]
        mock_ce.return_value = mock_ext

        mock_gc.return_value = {
            'success': True, 'count': 1,
            'output_dir': '/tmp/out', 'word_dir': '/tmp/out/word',
            'pdf_dir': '/tmp/out/pdf',
            'files': [{'filename': '席卡_张三.docx', 'filepath': '/tmp/out/word/席卡_张三.docx',
                        'pdf_filepath': '/tmp/out/pdf/席卡_张三.pdf', 'name': '张三', 'valid': True}],
            'failed': [], 'report_path': '/tmp/out/报告.txt',
            'pdf_combined_path': '/tmp/out/合集.pdf',
        }

        tpl = os.path.join(self._td, '席卡模板v4.docx')
        open(tpl, 'w').close()

        resp = self.client.post('/api/generate-cards',
                                json={'text': '张三 公司A 职位B', 'template': '席卡模板v4.docx'})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['count'], 1)
        self.assertEqual(len(data['word_files']), 1)
        self.assertEqual(data['word_files'][0]['filename'], '席卡_张三.docx')
        self.assertEqual(len(data['pdf_files']), 1)
        self.assertIsNotNone(data['report_id'])
        self.assertIsNotNone(data['pdf_combined_id'])

    # -- 生成失败 --
    @patch('app.server.generate_cards')
    @patch('app.server.create_extractor')
    @patch('app.server.create_ai_service')
    def test_generate_cards_failure_returns_500(self, mock_cas, mock_ce, mock_gc):
        mock_ce.return_value = MagicMock()
        mock_gc.return_value = {'success': False, 'error': '模板损坏'}

        tpl = os.path.join(self._td, '席卡模板v4.docx')
        open(tpl, 'w').close()

        resp = self.client.post('/api/generate-cards',
                                json={'text': '张三', 'template': '席卡模板v4.docx'})
        self.assertEqual(resp.status_code, 500)
        self.assertIn('模板损坏', resp.json()['detail'])

    # -- 提取失败 --
    @patch('app.server.create_extractor')
    @patch('app.server.create_ai_service')
    def test_no_persons_extracted_returns_400(self, mock_cas, mock_ce):
        mock_ext = MagicMock()
        mock_ext.extract_from_text.return_value = []
        mock_ce.return_value = mock_ext

        tpl = os.path.join(self._td, '席卡模板v4.docx')
        open(tpl, 'w').close()

        resp = self.client.post('/api/generate-cards',
                                json={'text': '无意义文本', 'template': '席卡模板v4.docx'})
        self.assertEqual(resp.status_code, 400)
        self.assertIn('未能提取', resp.json()['detail'])

    # -- 下载映射 --
    @patch('app.server.generate_cards')
    @patch('app.server.create_extractor')
    @patch('app.server.create_ai_service')
    def test_download_map_populated(self, mock_cas, mock_ce, mock_gc):
        mock_ext = MagicMock()
        mock_ext.extract_from_text.return_value = [MockPersonInfo(name='李四')]
        mock_ce.return_value = mock_ext
        mock_gc.return_value = {
            'success': True, 'count': 1,
            'output_dir': '/tmp', 'word_dir': '/tmp/w', 'pdf_dir': '/tmp/p',
            'files': [{'filename': 'f.docx', 'filepath': '/tmp/f.docx',
                        'pdf_filepath': '/tmp/f.pdf', 'name': '李四', 'valid': True}],
            'failed': [], 'report_path': None, 'pdf_combined_path': None,
        }

        tpl = os.path.join(self._td, '席卡模板v4.docx')
        open(tpl, 'w').close()

        resp = self.client.post('/api/generate-cards',
                                json={'text': '李四', 'template': '席卡模板v4.docx'})
        data = resp.json()
        # word + pdf = 2 entries
        self.assertEqual(len(file_download_map), 2)


@unittest.skipUnless(HAS_TEST_CLIENT, '需要 fastapi[all] 或 httpx')
class TestDownloadFile(unittest.TestCase):
    """/download/{file_id} 文件下载"""

    def setUp(self):
        import app.server as srv
        srv.file_download_map.clear()
        self.client = TestClient(app)

    def test_valid_download(self):
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
            f.write(b'test content')
            fp = f.name
        try:
            file_download_map['test-id-1'] = fp
            resp = self.client.get('/download/test-id-1')
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.content, b'test content')
        finally:
            os.unlink(fp)

    def test_unknown_file_id_returns_404(self):
        resp = self.client.get('/download/nonexistent-id')
        self.assertEqual(resp.status_code, 404)
        self.assertIn('不存在', resp.json()['detail'])

    def test_deleted_file_cleaned_up(self):
        file_download_map['stale-id'] = '/nonexistent/file.docx'
        resp = self.client.get('/download/stale-id')
        self.assertEqual(resp.status_code, 404)
        self.assertNotIn('stale-id', file_download_map)


if __name__ == '__main__':
    unittest.main()
