import 'package:flutter/material.dart';
import '../models/card_models.dart';
import '../services/minimax_service.dart';
import '../services/card_generator.dart';
import '../services/settings_service.dart';
import 'settings_page.dart';
import 'result_page.dart';

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  final _inputController = TextEditingController();
  final _eventController = TextEditingController();
  final _settingsService = SettingsService();

  DisplayType _displayType = DisplayType.name;
  bool _isGenerating = false;
  bool _hasApiKey = false;

  @override
  void initState() {
    super.initState();
    _checkApiKey();
  }

  Future<void> _checkApiKey() async {
    final key = await _settingsService.getApiKey();
    if (mounted) setState(() => _hasApiKey = key.isNotEmpty);
  }

  @override
  void dispose() {
    _inputController.dispose();
    _eventController.dispose();
    super.dispose();
  }

  Future<void> _generate() async {
    final text = _inputController.text.trim();
    if (text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('请输入人员信息')),
      );
      return;
    }

    final apiKey = await _settingsService.getApiKey();
    if (apiKey.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('请先配置 API Key')),
      );
      Navigator.push(context, MaterialPageRoute(builder: (_) => const SettingsPage()));
      return;
    }

    setState(() => _isGenerating = true);

    try {
      final apiUrl = await _settingsService.getApiUrl();
      final model = await _settingsService.getModel();

      final miniMax = MiniMaxService(
        apiKey: apiKey,
        apiBaseUrl: apiUrl,
        model: model,
      );

      // Step 1: AI 提取人员信息
      final infos = await miniMax.extractFromText(text);
      if (infos.isEmpty) {
        if (!mounted) return;
        setState(() => _isGenerating = false);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('未提取到人员信息，请检查输入内容')),
        );
        return;
      }

      // Step 2: 本地生成 PDF 席卡
      final generator = CardGeneratorService();
      final result = await generator.generateCards(
        infos: infos,
        eventName: _eventController.text.trim(),
        displayType: _displayType,
      );

      if (!mounted) return;
      setState(() => _isGenerating = false);

      // Step 3: 跳转结果页
      Navigator.push(context, MaterialPageRoute(
        builder: (_) => ResultPage(result: result),
      ));
    } catch (e) {
      if (!mounted) return;
      setState(() => _isGenerating = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('生成失败: $e')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('席卡生成系统'),
        actions: [
          IconButton(
            icon: const Icon(Icons.settings),
            onPressed: () async {
              await Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const SettingsPage()),
              );
              _checkApiKey();
            },
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // API Key 提示
            if (!_hasApiKey)
              Card(
                color: Theme.of(context).colorScheme.errorContainer,
                child: Padding(
                  padding: const EdgeInsets.all(12),
                  child: Row(
                    children: [
                      Icon(Icons.warning_amber,
                          color: Theme.of(context).colorScheme.error),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          '未配置 API Key，点击右侧设置按钮配置',
                          style: TextStyle(
                              color: Theme.of(context).colorScheme.onErrorContainer),
                        ),
                      ),
                      TextButton(
                        onPressed: () async {
                          await Navigator.push(
                            context,
                            MaterialPageRoute(builder: (_) => const SettingsPage()),
                          );
                          _checkApiKey();
                        },
                        child: const Text('去设置'),
                      ),
                    ],
                  ),
                ),
              ),

            const SizedBox(height: 16),

            // 输入区域
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('人员信息',
                        style: Theme.of(context).textTheme.titleMedium),
                    const SizedBox(height: 8),
                    TextField(
                      controller: _inputController,
                      maxLines: 8,
                      minLines: 5,
                      decoration: const InputDecoration(
                        hintText: '输入人员信息，支持多种格式：\n'
                            '张三 北京科技有限公司 高级工程师\n'
                            '李四，上海数据集团，产品经理\n'
                            '王五 - 深圳创新科技 - 技术总监',
                        border: OutlineInputBorder(),
                      ),
                    ),
                    const SizedBox(height: 16),

                    // 活动名称
                    TextField(
                      controller: _eventController,
                      decoration: const InputDecoration(
                        labelText: '活动名称（可选）',
                        hintText: '如：2026年度工作会议',
                        border: OutlineInputBorder(),
                      ),
                    ),
                    const SizedBox(height: 16),

                    // 显示类型
                    Text('显示内容',
                        style: Theme.of(context).textTheme.titleSmall),
                    const SizedBox(height: 8),
                    SegmentedButton<DisplayType>(
                      segments: const [
                        ButtonSegment(
                          value: DisplayType.name,
                          label: Text('姓名'),
                          icon: Icon(Icons.person),
                        ),
                        ButtonSegment(
                          value: DisplayType.company,
                          label: Text('公司名'),
                          icon: Icon(Icons.business),
                        ),
                      ],
                      selected: {_displayType},
                      onSelectionChanged: (v) =>
                          setState(() => _displayType = v.first),
                    ),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 16),

            // 生成按钮
            FilledButton.icon(
              onPressed: _isGenerating ? null : _generate,
              icon: _isGenerating
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.print),
              label: Text(_isGenerating ? '生成中...' : '生成席卡'),
              style: FilledButton.styleFrom(
                minimumSize: const Size(double.infinity, 52),
                textStyle: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
