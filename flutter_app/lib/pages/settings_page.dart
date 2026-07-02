import 'package:flutter/material.dart';
import '../services/api_service.dart';

class SettingsPage extends StatefulWidget {
  final ApiService apiService;

  const SettingsPage({super.key, required this.apiService});

  @override
  State<SettingsPage> createState() => _SettingsPageState();
}

class _SettingsPageState extends State<SettingsPage> {
  late TextEditingController _urlController;
  bool _isChecking = false;
  bool? _isConnected;

  @override
  void initState() {
    super.initState();
    _urlController = TextEditingController(text: widget.apiService.baseUrl);
  }

  @override
  void dispose() {
    _urlController.dispose();
    super.dispose();
  }

  Future<void> _testConnection() async {
    setState(() {
      _isChecking = true;
      _isConnected = null;
    });

    // 先保存 URL
    widget.apiService.baseUrl = _urlController.text.trim();

    final connected = await widget.apiService.healthCheck();

    if (!mounted) return;
    setState(() {
      _isChecking = false;
      _isConnected = connected;
    });
  }

  void _save() {
    widget.apiService.baseUrl = _urlController.text.trim();
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('服务器地址已保存')),
    );
    Navigator.pop(context, 'refresh');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('服务器设置'),
        actions: [
          TextButton(
            onPressed: _save,
            child: const Text('保存'),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 600),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('API 服务器地址',
                          style: Theme.of(context).textTheme.titleMedium),
                      const SizedBox(height: 12),
                      TextField(
                        controller: _urlController,
                        decoration: const InputDecoration(
                          hintText: 'http://localhost:8000',
                          labelText: '服务器 URL',
                          helperText: '输入 Python 后端服务的地址',
                        ),
                        keyboardType: TextInputType.url,
                        onSubmitted: (_) => _testConnection(),
                      ),
                      const SizedBox(height: 16),
                      Row(
                        children: [
                          Expanded(
                            child: FilledButton.icon(
                              onPressed: _isChecking ? null : _testConnection,
                              icon: _isChecking
                                  ? const SizedBox(
                                      width: 16,
                                      height: 16,
                                      child: CircularProgressIndicator(
                                        strokeWidth: 2,
                                        color: Colors.white,
                                      ),
                                    )
                                  : const Icon(Icons.wifi),
                              label: const Text('测试连接'),
                            ),
                          ),
                        ],
                      ),
                      if (_isConnected != null) ...[
                        const SizedBox(height: 12),
                        Row(
                          children: [
                            Icon(
                              _isConnected!
                                  ? Icons.check_circle
                                  : Icons.error,
                              color: _isConnected! ? Colors.green : Colors.red,
                              size: 20,
                            ),
                            const SizedBox(width: 8),
                            Text(
                              _isConnected! ? '连接成功' : '连接失败',
                              style: TextStyle(
                                color:
                                    _isConnected! ? Colors.green : Colors.red,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ],
                        ),
                      ],
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('使用说明',
                          style: Theme.of(context).textTheme.titleMedium),
                      const SizedBox(height: 12),
                      const Text(
                        '1. 确保 Python 后端服务已启动\n'
                        '2. 桌面端默认地址: http://localhost:8000\n'
                        '3. 局域网访问: http://<电脑IP>:8000\n'
                        '4. 启动后端: python start_server.py',
                        style: TextStyle(height: 1.6),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
