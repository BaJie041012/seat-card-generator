import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../models/card_models.dart';
import '../services/api_service.dart';

class ResultPage extends StatelessWidget {
  final GenerateCardsResponse response;
  final ApiService apiService;

  const ResultPage({
    super.key,
    required this.response,
    required this.apiService,
  });

  void _showDownloadDialog(BuildContext context, String url) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('下载文件'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('请在浏览器中打开以下链接下载文件：'),
            const SizedBox(height: 8),
            SelectableText(
              url,
              style: const TextStyle(fontSize: 12, color: Colors.blue),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () {
              Clipboard.setData(ClipboardData(text: url));
              Navigator.of(ctx).pop();
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('链接已复制到剪贴板')),
              );
            },
            child: const Text('复制链接'),
          ),
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: const Text('关闭'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return Scaffold(
      appBar: AppBar(
        title: const Text('生成结果'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 600),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // 成功摘要卡片
              Card(
                color: colorScheme.primaryContainer,
                child: Padding(
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    children: [
                      Icon(Icons.check_circle,
                          size: 48, color: colorScheme.primary),
                      const SizedBox(height: 8),
                      Text(
                        '成功生成 ${response.count} 张席卡',
                        style: Theme.of(context).textTheme.headlineSmall,
                      ),
                      if (response.outputDir != null) ...[
                        const SizedBox(height: 4),
                        Text(
                          response.outputDir!,
                          style: Theme.of(context).textTheme.bodySmall,
                          textAlign: TextAlign.center,
                        ),
                      ],
                    ],
                  ),
                ),
              ),

              const SizedBox(height: 16),

              // Word 文件列表
              if (response.wordFiles.isNotEmpty) ...[
                _buildSectionTitle(context, 'Word 文件',
                    Icons.description, response.wordFiles.length),
                const SizedBox(height: 8),
                ...response.wordFiles.map((f) => _buildFileTile(
                      context,
                      f.filename,
                      apiService.getDownloadUrl(f.fileId),
                      Icons.description,
                      colorScheme.tertiary,
                    )),
              ],

              const SizedBox(height: 16),

              // PDF 文件列表
              if (response.pdfFiles.isNotEmpty) ...[
                _buildSectionTitle(context, 'PDF 文件',
                    Icons.picture_as_pdf, response.pdfFiles.length),
                const SizedBox(height: 8),
                ...response.pdfFiles.map((f) => _buildFileTile(
                      context,
                      f.filename,
                      apiService.getDownloadUrl(f.fileId),
                      Icons.picture_as_pdf,
                      Colors.red,
                    )),
              ],

              const SizedBox(height: 16),

              // PDF 合集
              if (response.pdfCombinedId != null) ...[
                Card(
                  child: ListTile(
                    leading: Icon(Icons.library_books,
                        color: colorScheme.primary, size: 32),
                    title: const Text('PDF 合集'),
                    subtitle: const Text('所有席卡合并为一个 PDF'),
                    trailing: const Icon(Icons.download),
                    onTap: () => _showDownloadDialog(
                        context, apiService.getDownloadUrl(response.pdfCombinedId!)),
                  ),
                ),
                const SizedBox(height: 16),
              ],

              // 质量报告
              if (response.reportId != null) ...[
                Card(
                  child: ListTile(
                    leading: Icon(Icons.assessment,
                        color: colorScheme.primary, size: 32),
                    title: const Text('质量报告'),
                    subtitle: const Text('查看生成质量详情'),
                    trailing: const Icon(Icons.download),
                    onTap: () => _showDownloadDialog(
                        context, apiService.getDownloadUrl(response.reportId!)),
                  ),
                ),
                const SizedBox(height: 16),
              ],

              // 失败记录
              if (response.failed.isNotEmpty) ...[
                Card(
                  color: colorScheme.errorContainer,
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Icon(Icons.error_outline,
                                color: colorScheme.error),
                            const SizedBox(width: 8),
                            Text(
                              '失败记录 (${response.failed.length})',
                              style: TextStyle(
                                color: colorScheme.onErrorContainer,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        ...response.failed.map((name) => Padding(
                              padding:
                                  const EdgeInsets.symmetric(vertical: 2),
                              child: Text(
                                '  $name',
                                style: TextStyle(
                                    color: colorScheme.onErrorContainer),
                              ),
                            )),
                      ],
                    ),
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildSectionTitle(
      BuildContext context, String title, IconData icon, int count) {
    return Row(
      children: [
        Icon(icon, size: 20, color: Theme.of(context).colorScheme.primary),
        const SizedBox(width: 8),
        Text(
          '$title ($count)',
          style: Theme.of(context).textTheme.titleMedium,
        ),
      ],
    );
  }

  Widget _buildFileTile(BuildContext context, String filename, String url,
      IconData icon, Color iconColor) {
    return Card(
      child: ListTile(
        leading: Icon(icon, color: iconColor),
        title: Text(
          filename,
          style: const TextStyle(fontSize: 14),
          overflow: TextOverflow.ellipsis,
        ),
        trailing: const Icon(Icons.download, size: 20),
        onTap: () => _showDownloadDialog(context, url),
      ),
    );
  }
}
