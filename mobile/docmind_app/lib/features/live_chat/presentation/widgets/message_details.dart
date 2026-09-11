import 'package:flutter/material.dart';
import '../../domain/entities/chat_message.dart';

/// Renders persisted metadata identically for a new reply and loaded history.
class MessageDetails extends StatelessWidget {
  const MessageDetails({super.key, required this.message});
  final ChatMessage message;

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (message.deliveryStatus == DeliveryStatus.failed)
          const Text(
            'Not delivered — retry below',
            style: TextStyle(color: Colors.white),
          ),
        if (message.deliveryStatus == DeliveryStatus.sending)
          const Text('Sending…', style: TextStyle(color: Colors.white)),
        if (!message.isUser && message.interrupted)
          Text(
            message.generationStatus == 'failed'
                ? 'Response failed'
                : 'Response interrupted',
            style: TextStyle(color: colors.error),
          ),
        if (!message.isUser && message.groundingStatus != null)
          Text(switch (message.groundingStatus) {
            'grounded' => 'Based on your sources',
            'insufficient_evidence' => 'Not enough evidence in your sources',
            'ungrounded' => 'General response',
            _ => 'Source grounding unavailable',
          }, style: Theme.of(context).textTheme.labelSmall),
        if (message.citations.isNotEmpty)
          Wrap(
            spacing: 6,
            children: message.citations
                .map(
                  (source) => ActionChip(
                    label: Text(
                      '[${source.marker}] ${source.sourceName}',
                      overflow: TextOverflow.ellipsis,
                    ),
                    onPressed: () => showDialog<void>(
                      context: context,
                      builder: (context) => AlertDialog(
                        title: Text(source.sourceName),
                        content: SingleChildScrollView(
                          child: Column(
                            mainAxisSize: MainAxisSize.min,
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                '${source.locationType} ${source.locationNumber}',
                              ),
                              if (source.section?.isNotEmpty ?? false)
                                Text(source.section!),
                              const SizedBox(height: 12),
                              SelectableText(source.excerpt),
                            ],
                          ),
                        ),
                        actions: [
                          TextButton(
                            onPressed: () => Navigator.pop(context),
                            child: const Text('Close'),
                          ),
                        ],
                      ),
                    ),
                  ),
                )
                .toList(),
          ),
      ],
    );
  }
}
