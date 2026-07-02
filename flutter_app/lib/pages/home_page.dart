import 'package:flutter/material.dart';
import '../models/card_models.dart';
import '../services/api_service.dart';
import 'result_page.dart';
import 'settings_page.dart';

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  final _textController = TextEditingController();
  final _eventNameController = TextEditingController();
  final _apiService = ApiService();

  String _displayType = 'name';
  String? _selectedTemplate;
  List<String> _templates = [];
  bool _isLoading = false;
  bool _isConnected = false;

  @override
  void initState() {
    super.initState();
    _checkConnection();
  }

  Future<void> _checkConnection() async {
    final connected = await _apiService.healthCheck();
    if (!mounted) return;
    setState(() => _isConnected = connected);
    if (connected) {
      _loadTemplates();
    }
  }

  Future<void> _loadTemplates() async {
    final info = await _apiService.getTemplates();
    if (!mounted) return;
    setState(() {
      _templates = info.templates;
      // 优先选择 v5 模板
      if (_templates.contains('席卡模板v5.docx')) {
        _selectedTemplate = '席卡模板v5.docx';
      } else if (_templates.isNotEmpty) {
        _selectedTemplate = _templates.first;
      }
    });
  }

  Future<void> _generateCards() async {
    if (_textController.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('请输入人员信息')),
      );
      return;
    }
    if (_selectedTemplate == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('请选择模板文件')),
      );
      return;
    }

    setState(() => _isLoading = true);

    final request = GenerateCardsRequest(
      text: _textController.text,
      eventName: _eventNameController.text,
      displayType: _displayType,
      template: _selectedTemplate!,
    );

    final response = await _apiService.generateCards(request);

    if (!mounted) return;
    setState(() => _isLoading = false);

    if (response.success) {
      if (!mounted) return;
      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (_) => ResultPage(
            response: response,
            apiService: _apiService,
          ),
        ),
      );
    } else {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(response.error ?? '生成失败'),
          backgroundColor: Theme.of(context).colorScheme.error,
        ),
      );
    }
  }

  @override
  void dispose() {
    _textController.dispose();
    _eventNameController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return Scaffold(
      appBar: AppBar(
        title: const Text('席卡生成系统'),
        actions: [
          IconButton(
            icon: Icon(_isConnected ? Icons.cloud_done : Icons.cloud_off),
            tooltip: _isConnected ? '服务器已连接' : '服务器未连接',
            onPressed: _checkConnection,
          ),
          IconButton(
            icon: const Icon(Icons.settings),
            tooltip: '服务器设置',
            onPressed: () async {
              final result = await Navigator.push<String>(
                context,
                MaterialPageRoute(
                  builder: (_) => SettingsPage(apiService: _apiService),
                ),
              );
              if (result == 'refresh') {
                _checkConnection();
              }
            },
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
              // 连接状态提示
              if (!_isConnected)
                Card(
                  color: colorScheme.errorContainer,
                  child: Padding(
                    padding: const EdgeInsets.all(12),
                    child: Row(
                      children: [
                        Icon(Icons.warning_amber,
                            color: colorScheme.onErrorContainer),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            '无法连接到服务器，请确认服务已启动',
                            style: TextStyle(color: colorScheme.onErrorContainer),
                          ),
                        ),
                        TextButton(
                          onPressed: _checkConnection,
                          child: const Text('重试'),
                        ),
                      ],
                    ),
                  ),
                ),

              const SizedBox(height: 16),

              // 人员信息输入
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('人员信息',
                          style: Theme.of(context).textTheme.titleMedium),
                      const SizedBox(height: 12),
                      TextField(
                        controller: _textController,
                        maxLines: 6,
                        minLines: 4,
                        decoration: const InputDecoration(
                          hintText:
                              '请输入人员信息，每行一条\n例如：\n张三，公司A，职位B\n李四，公司C，职位D',
                          alignLabelWithHint: true,
                        ),
                      ),
                    ],
                  ),
                ),
              ),

              const SizedBox(height: 16),

              // 参数设置
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('参数设置',
                          style: Theme.of(context).textTheme.titleMedium),
                      const SizedBox(height: 12),
                      TextField(
                        controller: _eventNameController,
                        decoration: const InputDecoration(
                          labelText: '活动名称',
                          hintText: '例如：公司年会（可选）',
                        ),
                      ),
                      const SizedBox(height: 16),
                      // 显示内容选择
                      DropdownButtonFormField<String>(
                        initialValue: _displayType,
                        decoration: const InputDecoration(
                          labelText: '显示内容',
                        ),
                        items: const [
                          DropdownMenuItem(
                            value: 'name',
                            child: Text('姓名'),
                          ),
                          DropdownMenuItem(
                            value: 'company',
                            child: Text('公司名'),
                          ),
                        ],
                        onChanged: (value) {
                          if (value != null) {
                            setState(() => _displayType = value);
                          }
                        },
                      ),
                      const SizedBox(height: 16),
                      // 模板选择
                      DropdownButtonFormField<String>(
                        initialValue: _selectedTemplate,
                        decoration: const InputDecoration(
                          labelText: '模板文件',
                        ),
                        items: _templates
                            .map((t) => DropdownMenuItem(
                                  value: t,
                                  child: Text(t),
                                ))
                            .toList(),
                        onChanged: _templates.isEmpty
                            ? null
                            : (value) {
                                if (value != null) {
                                  setState(() => _selectedTemplate = value);
                                }
                              },
                      ),
                    ],
                  ),
                ),
              ),

              const SizedBox(height: 24),

              // 生成按钮
              SizedBox(
                height: 50,
                child: FilledButton.icon(
                  onPressed: _isLoading ? null : _generateCards,
                  icon: _isLoading
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Colors.white,
                          ),
                        )
                      : const Icon(Icons.print),
                  label: Text(
                    _isLoading ? '生成中...' : '生成席卡',
                    style: const TextStyle(fontSize: 16),
                  ),
                ),
              ),

              const SizedBox(height: 16),

              // 示例按钮
              OutlinedButton.icon(
                onPressed: () {
                  _textController.text =
                      '张三，科技有限公司，总经理\n李四，数据集团，技术总监\n王五，创新科技，产品经理';
                  _eventNameController.text = '2026年度会议';
                },
                icon: const Icon(Icons.auto_awesome),
                label: const Text('填入示例数据'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
