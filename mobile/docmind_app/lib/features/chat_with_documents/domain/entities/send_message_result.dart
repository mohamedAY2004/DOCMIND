import '../../../live_chat/domain/entities/chat_message.dart';

/// Result of sending a message in a document conversation.
class SendMessageResult {
  const SendMessageResult({
    required this.userMessage,
    required this.aiReply,
  });

  final ChatMessage userMessage;
  final ChatMessage aiReply;
}
