import 'dart:io';
import 'package:flutter/material.dart';
import 'package:share_plus/share_plus.dart';
import 'package:open_filex/open_filex.dart';
import '../models/card_models.dart';

class ResultPage extends StatelessWidget {
  final GenerateResult result;
  const ResultPage({super.key, required this.result});

  Future<void> _shareFile(BuildContext context, String filePath) async {
    final file = File(filePath);
    if (!await file.exists()) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('文件不存在')),
        );
      }
      return;
    }
    await Share.shareXFiles([XFile(filePath)]);
  }

  Future<void> _openFile(BuildContext context, String filePath) async {
    final result = await OpenFilex.open(filePath);
    if (result.type != ResultType.done && context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('打开失败: ${result.message}')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final successCards = result.cards.where((c) => c.success).toList();
    final failedCards = result.cards.where((c) => !c.success).toList();

    return Scaffold(
      appBar: AppBar(
        title: const Text('生成结果'),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // 汇总
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceAround,
                    children: [
                      _buildStat(context, '成功', result.successCount, Colors.green),
                      _buildStat(context, '失败', result.failCount, Colors.red),
                      _buildStat(context, '总计', result.cards.length, Colors.blue),
                    ],
                  ),
                  if (result.combinedPdfPath != null) ...[
                    const Divider(height: 24),
                    ListTile(
                      leading: const Icon(Icons.picture_as_pdf, color: Colors.red),
                      title: const Text('席卡合集 PDF'),
                      subtitle: const Text('包含所有席卡的合并文件'),
                      trailing: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          IconButton(
                            icon: const Icon(Icons.open_in_new),
                            onPressed: () => _openFile(context, result.combinedPdfPath!),
                          ),
                          IconButton(
                            icon: const Icon(Icons.share),
                            onPressed: () => _shareFile(context, result.combinedPdfPath!),
                          ),
                        ],
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ),

          const SizedBox(height: 16),

          // 单个席卡列表
          Text('单个席卡', style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 8),

          ...successCards.map((card) => Card(
                child: ListTile(
                  leading: const Icon(Icons.check_circle, color: Colors.green),
                  title: Text(card.displayName),
                  subtitle: Text(File(card.filePath).uri.pathSegments.last),
                  trailing: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      IconButton(
                        icon: const Icon(Icons.open_in_new, size: 20),
                        onPressed: () => _openFile(context, card.filePath),
                      ),
                      IconButton(
                        icon: const Icon(Icons.share, size: 20),
                        onPressed: () => _shareFile(context, card.filePath),
                      ),
                    ],
                  ),
                ),
              )),

          // 失败列表
          if (failedCards.isNotEmpty) ...[
            const SizedBox(height: 16),
            Text('生成失败', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            ...failedCards.map((card) => Card(
                  color: Theme.of(context).colorScheme.errorContainer,
                  child: ListTile(
                    leading: Icon(Icons.error,
                        color: Theme.of(context).colorScheme.error),
                    title: Text(card.displayName),
                    subtitle: Text(card.error ?? '未知错误'),
                  ),
                )),
          ],

          const SizedBox(height: 24),

          // 输出目录信息
          Card(
            color: Theme.of(context).colorScheme.surfaceContainerLow,
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Text(
                '文件保存在: ${result.outputDir}',
                style: const TextStyle(fontSize: 12),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStat(BuildContext context, String label, int count, Color color) {
    return Column(
      children: [
        Text('$count',
            style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold, color: color)),
        Text(label, style: Theme.of(context).textTheme.bodySmall),
      ],
    );
  }
}
