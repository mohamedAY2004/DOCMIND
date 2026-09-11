import 'chat_message.dart';

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
