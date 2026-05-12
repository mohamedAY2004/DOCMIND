/// Domain entity for a document conversation.
class DocumentConversation {
  const DocumentConversation({
    required this.id,
    required this.title,
    this.subjectId,
    required this.createdAt,
    required this.updatedAt,
    required this.messageCount,
  });

  final String id;
  final String title;
  final String? subjectId;
  final DateTime createdAt;
  final DateTime updatedAt;
  final int messageCount;

  /// Returns a human-readable relative time string based on last update.
  String get relativeTime {
    final now = DateTime.now();
    final diff = now.difference(updatedAt);

    if (diff.inDays > 365) {
      return '${(diff.inDays / 365).floor()}y ago';
    } else if (diff.inDays > 30) {
      return '${(diff.inDays / 30).floor()}mo ago';
    } else if (diff.inDays > 0) {
      return '${diff.inDays}d ago';
    } else if (diff.inHours > 0) {
      return '${diff.inHours}h ago';
    } else if (diff.inMinutes > 0) {
      return '${diff.inMinutes}m ago';
    } else {
      return 'Just now';
    }
  }
}
