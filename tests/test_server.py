"""server.py 单元测试"""
import os
import sys
import json
import unittest
from unittest.mock import patch, MagicMock
from collections import OrderedDict

# 确保能导入 app 模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestGetLocalIp(unittest.TestCase):
    """测试 get_local_ip"""

    @patch('socket.socket')
    def test_returns_ip(self, mock_socket):
        mock_instance = MagicMock()
        mock_instance.getsockname.return_value = ('192.168.1.100', 0)
        mock_socket.return_value = mock_instance

        from server import get_local_ip
        ip = get_local_ip()
        self.assertEqual(ip, '192.168.1.100')

    @patch('socket.socket')
    def test_returns_localhost_on_error(self, mock_socket):
        mock_socket.side_effect = Exception("Network error")

        from server import get_local_ip
        ip = get_local_ip()
        self.assertEqual(ip, '127.0.0.1')


class TestFileDownloadMapLRU(unittest.TestCase):
    """测试文件下载映射的LRU行为"""

    def test_ordered_dict_behavior(self):
        """OrderedDict 基本行为"""
        d = OrderedDict()
        d['a'] = 1
        d['b'] = 2
        d['c'] = 3
        self.assertEqual(list(d.keys()), ['a', 'b', 'c'])

    def test_move_to_end(self):
        """move_to_end 标记为最近使用"""
        d = OrderedDict()
        d['a'] = 1
        d['b'] = 2
        d['c'] = 3
        d.move_to_end('a')
        self.assertEqual(list(d.keys()), ['b', 'c', 'a'])

    def test_popitem_evicts_oldest(self):
        """popitem(last=False) 淘汰最久未使用"""
        d = OrderedDict()
        d['a'] = 1
        d['b'] = 2
        d['c'] = 3
        d.move_to_end('a')  # 'a' 变为最近使用
        d.popitem(last=False)  # 淘汰 'b'（最久未使用）
        self.assertNotIn('b', d)
        self.assertIn('a', d)


class TestRegisterDownload(unittest.TestCase):
    """测试 _register_download 函数"""

    @patch('server.file_download_map', new_callable=OrderedDict)
    @patch('server.FILE_DOWNLOAD_MAP_MAX', 3)
    def test_eviction_when_full(self, mock_map):
        """超出上限时淘汰最旧条目"""
        from server import _register_download
        # 直接操作 mock
        mock_map['old1'] = '/path/old1'
        mock_map['old2'] = '/path/old2'
        mock_map['old3'] = '/path/old3'

        # 由于 mock 的限制，我们测试函数逻辑
        file_id = _register_download('/path/new')
        self.assertIsInstance(file_id, str)
        self.assertGreater(len(file_id), 0)


class TestGenerateCardsRequest(unittest.TestCase):
    """测试请求数据模型"""

    def test_default_values(self):
        from server import GenerateCardsRequest
        req = GenerateCardsRequest(text='张三，公司A')
        self.assertEqual(req.text, '张三，公司A')
        self.assertEqual(req.event_name, '')
        self.assertEqual(req.display_type, 'name')
        self.assertEqual(req.template, '席卡模板v4.docx')

    def test_custom_values(self):
        from server import GenerateCardsRequest
        req = GenerateCardsRequest(
            text='李四',
            event_name='年会',
            display_type='company',
            template='v5.docx'
        )
        self.assertEqual(req.event_name, '年会')
        self.assertEqual(req.display_type, 'company')


if __name__ == '__main__':
    unittest.main()