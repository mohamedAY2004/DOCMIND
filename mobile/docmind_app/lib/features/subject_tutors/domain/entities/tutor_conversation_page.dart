import 'tutor_conversation.dart';

/// Paged list of tutor conversations.
class TutorConversationPage {
  const TutorConversationPage({
    required this.items,
    required this.page,
    required this.pageSize,
    required this.total,
    required this.totalPages,
  });

  final List<TutorConversation> items;
  final int page;
  final int pageSize;
  final int total;
  final int totalPages;
}
