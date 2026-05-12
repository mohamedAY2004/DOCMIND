import 'document_conversation.dart';

/// Paginated result for document conversations.
class ConversationsPage {
  const ConversationsPage({
    required this.items,
    required this.page,
    required this.pageSize,
    required this.total,
    required this.totalPages,
  });

  final List<DocumentConversation> items;
  final int page;
  final int pageSize;
  final int total;
  final int totalPages;

  bool get hasNextPage => page < totalPages;
  bool get hasPreviousPage => page > 1;
  bool get isEmpty => items.isEmpty;
}
