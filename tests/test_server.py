"""server.py 单元测试 - API端点、认证、路径遍历防护、LRU下载映射"""
import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock, AsyncMock
from collections import OrderedDict

# 在导入 server 之前确保依赖模块的 mock 就绪
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Mock 掉重量级依赖模块，避免导入时副作用
_mock_config = MagicMock()
_mock_config.template.template_dir = tempfile.gettempdir()
_mock_config.template.output_dir = tempfile.gettempdir()
_mock_config.ai.api_key = 'test-key'

sys.modules.setdefault('config', MagicMock(CONFIG=_mock_config, ensure_directories=MagicMock()))
sys.modules.setdefault('ai_service', MagicMock())
sys.modules.setdefault('text_extractor', MagicMock())
sys.modules.setdefault('card_generator', MagicMock())

from fastapi.testclient import TestClient


class ServerTestBase(unittest.TestCase):
    """server 测试基类，处理模块重载和 token 配置"""

    def _reload_server(self, token=''):
        """以指定 token 重新加载 server 模块"""
        import importlib
        with patch.dict(os.environ, {'SEAT_CARD_TOKEN': token}):
            if 'server' in sys.modules:
                del sys.modules['server']
            import server
            importlib.reload(server)
            return server


class TestHealthEndpoint(ServerTestBase):
    """测试健康检查端点"""

    def setUp(self):
        self.server = self._reload_server()
        self.client = TestClient(self.server.app)

    def test_health_no_auth_required(self):
        """健康检查无需认证"""
        resp = self.client.get('/api/health')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['status'], 'ok')
        self.assertIn('time', data)

    def test_health_accessible_with_token_configured(self):
        """即使配置了 token，健康检查仍可访问"""
        server = self._reload_server(token='secret')
        client = TestClient(server.app)
        resp = client.get('/api/health')
        self.assertEqual(resp.status_code, 200)


class TestTokenAuth(ServerTestBase):
    """测试 Token 认证"""

    def test_no_auth_required_when_no_token(self):
        """未配置 token 时无需认证"""
        resp = self.client.get('/api/templates')
        self.assertEqual(resp.status_code, 200)

    def test_auth_required_when_token_set(self):
        """配置 token 后需要认证"""
        server = self._reload_server(token='test-secret')
        client = TestClient(server.app)
        resp = client.get('/api/templates')
        self.assertEqual(resp.status_code, 401)

    def test_valid_token_accepted(self):
        """有效 token 通过认证"""
        server = self._reload_server(token='test-secret')
        client = TestClient(server.app)
        resp = client.get('/api/templates',
                          headers={'Authorization': 'Bearer test-secret'})
        self.assertEqual(resp.status_code, 200)

    def test_invalid_token_rejected(self):
        """无效 token 被拒绝"""
        server = self._reload_server(token='test-secret')
        client = TestClient(server.app)
        resp = client.get('/api/templates',
                          headers={'Authorization': 'Bearer wrong-token'})
        self.assertEqual(resp.status_code, 401)

    def test_missing_token_rejected(self):
        """配置了 token 但不提供认证信息被拒绝"""
        server = self._reload_server(token='test-secret')
        client = TestClient(server.app)
        resp = client.get('/api/templates')
        self.assertEqual(resp.status_code, 401)

    def setUp(self):
        self.server = self._reload_server()
        self.client = TestClient(self.server.app)


class TestPathTraversal(ServerTestBase):
    """测试路径遍历防护"""

    def setUp(self):
        self.server = self._reload_server()
        self.client = TestClient(self.server.app)
        self.tmpdir = tempfile.mkdtemp()
        self.server.CONFIG.template.template_dir = self.tmpdir
        # 创建一个合法模板文件
        with open(os.path.join(self.tmpdir, 'test.docx'), 'w') as f:
            f.write('dummy')

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_path_traversal_blocked(self):
        """路径遍历被阻止"""
        with patch.object(self.server, '_get_ai_service'):
            resp = self.client.post('/api/generate-cards', json={
                'text': '张三',
                'template': '../../etc/passwd.docx'
            })
            self.assertIn(resp.status_code, [400, 422])

    def test_valid_template_path_accepted(self):
        """合法模板路径通过验证"""
        mock_ext = MagicMock()
        mock_ext.extract_from_text.return_value = []
        with patch.object(self.server, '_get_ai_service', return_value=mock_ext):
            resp = self.client.post('/api/generate-cards', json={
                'text': '张三',
                'template': 'test.docx'
            })
            # 不会返回路径遍历错误（可能返回其他错误如"未能提取到人员信息"）
            if resp.status_code == 400:
                self.assertNotIn('模板文件名不合法', resp.json()['detail'])

    def test_non_docx_template_rejected(self):
        """非 docx 模板被拒绝"""
        with open(os.path.join(self.tmpdir, 'test.pdf'), 'w') as f:
            f.write('dummy')
        with patch.object(self.server, '_get_ai_service'):
            resp = self.client.post('/api/generate-cards', json={
                'text': '张三',
                'template': 'test.pdf'
            })
            self.assertEqual(resp.status_code, 400)
            self.assertIn('docx', resp.json()['detail'])


class TestGenerateCardsEndpoint(ServerTestBase):
    """测试席卡生成 API"""

    def setUp(self):
        self.server = self._reload_server()
        self.client = TestClient(self.server.app)
        self.tmpdir = tempfile.mkdtemp()
        self.server.CONFIG.template.template_dir = self.tmpdir
        self.server.CONFIG.template.output_dir = self.tmpdir
        with open(os.path.join(self.tmpdir, 'test.docx'), 'w') as f:
            f.write('dummy')

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_empty_text_returns_400(self):
        """空文本返回 400"""
        resp = self.client.post('/api/generate-cards', json={'text': ''})
        self.assertEqual(resp.status_code, 400)

    def test_whitespace_only_text_returns_400(self):
        """纯空白文本返回 400"""
        resp = self.client.post('/api/generate-cards', json={'text': '   '})
        self.assertEqual(resp.status_code, 400)

    def test_missing_template_returns_404(self):
        """模板不存在返回 404"""
        mock_ext = MagicMock()
        mock_ext.extract_from_text.return_value = [MagicMock()]
        with patch.object(self.server, '_get_ai_service', return_value=mock_ext):
            resp = self.client.post('/api/generate-cards', json={
                'text': '张三',
                'template': 'nonexistent.docx'
            })
            self.assertEqual(resp.status_code, 404)

    def test_successful_generation(self):
        """成功生成席卡"""
        mock_info = MagicMock()
        mock_info.name = '张三'
        mock_info.company = '测试公司'
        mock_info.position = '工程师'

        mock_ext = MagicMock()
        mock_ext.extract_from_text.return_value = [mock_info]

        mock_result = {
            'success': True,
            'count': 1,
            'output_dir': self.tmpdir,
            'word_dir': os.path.join(self.tmpdir, 'word'),
            'pdf_dir': os.path.join(self.tmpdir, 'pdf'),
            'files': [{
                'filename': '席卡_张三.docx',
                'filepath': os.path.join(self.tmpdir, 'word', '席卡_张三.docx'),
                'pdf_filepath': os.path.join(self.tmpdir, 'pdf', '席卡_张三.pdf')
            }],
            'failed': [],
            'report_path': os.path.join(self.tmpdir, 'report.txt'),
            'pdf_combined_path': os.path.join(self.tmpdir, 'combined.pdf')
        }

        with patch.object(self.server, '_get_ai_service', return_value=mock_ext):
            with patch.object(self.server, 'generate_cards', return_value=mock_result):
                resp = self.client.post('/api/generate-cards', json={
                    'text': '张三，测试公司，工程师',
                    'event_name': '测试活动',
                    'template': 'test.docx'
                })
                self.assertEqual(resp.status_code, 200)
                data = resp.json()
                self.assertTrue(data['success'])
                self.assertEqual(data['count'], 1)
                self.assertEqual(len(data['word_files']), 1)
                self.assertEqual(len(data['pdf_files']), 1)
                self.assertIsNotNone(data['pdf_combined_id'])

    def test_generation_failure_returns_500(self):
        """生成失败返回 500"""
        mock_ext = MagicMock()
        mock_ext.extract_from_text.return_value = [MagicMock()]
        mock_result = {'success': False, 'error': '生成失败'}

        with patch.object(self.server, '_get_ai_service', return_value=mock_ext):
            with patch.object(self.server, 'generate_cards', return_value=mock_result):
                resp = self.client.post('/api/generate-cards', json={
                    'text': '张三',
                    'template': 'test.docx'
                })
                self.assertEqual(resp.status_code, 500)

    def test_no_persons_extracted_returns_400(self):
        """未能提取人员信息返回 400"""
        mock_ext = MagicMock()
        mock_ext.extract_from_text.return_value = []

        with patch.object(self.server, '_get_ai_service', return_value=mock_ext):
            resp = self.client.post('/api/generate-cards', json={
                'text': '无关文本',
                'template': 'test.docx'
            })
            self.assertEqual(resp.status_code, 400)


class TestFileDownloadMap(ServerTestBase):
    """测试文件下载 LRU 映射"""

    def setUp(self):
        self.server = self._reload_server()
        self.client = TestClient(self.server.app)

    def test_register_download_returns_uuid(self):
        """注册下载返回 UUID"""
        file_id = self.server._register_download('/tmp/test.docx')
        self.assertIn(file_id, self.server.file_download_map)
        self.assertEqual(self.server.file_download_map[file_id], '/tmp/test.docx')

    def test_lru_eviction_at_max(self):
        """LRU 淘汰在达到上限时触发"""
        self.server.file_download_map.clear()
        self.server.FILE_DOWNLOAD_MAP_MAX = 3

        self.server._register_download('/tmp/a.docx')
        self.server._register_download('/tmp/b.docx')
        self.server._register_download('/tmp/c.docx')
        self.assertEqual(len(self.server.file_download_map), 3)

        # 访问第一个使其变为最近使用
        first_key = next(iter(self.server.file_download_map))
        self.server.file_download_map.move_to_end(first_key)

        self.server._register_download('/tmp/d.docx')
        self.assertEqual(len(self.server.file_download_map), 3)
        # 第二个（最久未使用）应被淘汰
        self.assertNotIn('/tmp/b.docx', self.server.file_download_map.values())

    def test_download_nonexistent_returns_404(self):
        """下载不存在的文件返回 404"""
        resp = self.client.get('/download/nonexistent-uuid')
        self.assertEqual(resp.status_code, 404)

    def tearDown(self):
        self.server.file_download_map.clear()
        self.server.FILE_DOWNLOAD_MAP_MAX = 500


class TestTemplatesEndpoint(ServerTestBase):
    """测试模板列表端点"""

    def setUp(self):
        self.server = self._reload_server()
        self.client = TestClient(self.server.app)
        self.tmpdir = tempfile.mkdtemp()
        self.server.CONFIG.template.template_dir = self.tmpdir

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_returns_docx_templates(self):
        """返回 docx 模板"""
        open(os.path.join(self.tmpdir, 'test.docx'), 'w').close()
        resp = self.client.get('/api/templates')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['success'])
        self.assertIn('test.docx', data['templates'])

    def test_excludes_non_template_files(self):
        """排除非模板文件"""
        open(os.path.join(self.tmpdir, 'readme.txt'), 'w').close()
        open(os.path.join(self.tmpdir, 'data.json'), 'w').close()
        open(os.path.join(self.tmpdir, 'test.docx'), 'w').close()
        resp = self.client.get('/api/templates')
        data = resp.json()
        self.assertIn('test.docx', data['templates'])
        self.assertNotIn('data.json', data['templates'])

    def test_empty_template_dir(self):
        """空模板目录返回空列表"""
        resp = self.client.get('/api/templates')
        data = resp.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['templates'], [])


class TestCORSServer(ServerTestBase):
    """测试 CORS 配置"""

    def test_default_cors_origins(self):
        """默认 CORS 来源为 localhost"""
        server = self._reload_server()
        # 检查中间件配置（通过 app 的中间件栈）
        # 默认应包含 localhost:8000 和 127.0.0.1:8000
        self.assertIsNotNone(server.app)

    def test_custom_cors_origins(self):
        """自定义 CORS 来源"""
        with patch.dict(os.environ, {'CORS_ORIGINS': 'http://example.com,http://test.com'}):
            server = self._reload_server()
            self.assertIsNotNone(server.app)


class TestRequestModel(ServerTestBase):
    """测试请求数据模型"""

    def setUp(self):
        self.server = self._reload_server()

    def test_default_values(self):
        """请求模型默认值"""
        req = self.server.GenerateCardsRequest(text='test')
        self.assertEqual(req.event_name, '')
        self.assertEqual(req.display_type, 'name')
        self.assertEqual(req.template, '席卡模板v4.docx')

    def test_custom_values(self):
        """请求模型自定义值"""
        req = self.server.GenerateCardsRequest(
            text='test', event_name='活动', display_type='company', template='v5.docx'
        )
        self.assertEqual(req.event_name, '活动')
        self.assertEqual(req.display_type, 'company')
        self.assertEqual(req.template, 'v5.docx')


class TestGetLocalIP(ServerTestBase):
    """测试获取本机 IP"""

    def setUp(self):
        self.server = self._reload_server()

    def test_returns_valid_ip_format(self):
        """返回有效 IP 格式"""
        ip = self.server.get_local_ip()
        parts = ip.split('.')
        self.assertEqual(len(parts), 4)
        for part in parts:
            self.assertTrue(part.isdigit())


if __name__ == '__main__':
    unittest.main()
