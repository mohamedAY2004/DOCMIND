import '../entities/chat_message.dart';
import '../entities/chat_session.dart';

class ChatMessagesPage {
  const ChatMessagesPage({
    required this.items,
    required this.page,
    required this.pageSize,
    required this.total,
    required this.totalPages,
  });

  final List<ChatMessage> items;
  final int page;
  final int pageSize;
  final int total;
  final int totalPages;
}

abstract class LiveChatRepository {
  Future<ChatMessagesPage> getConversationMessages({
    required String conversationId,
    required KnowledgeSourceType sourceType,
    int page = 1,
    int pageSize = 20,
  });
}
