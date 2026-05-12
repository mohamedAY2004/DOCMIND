/// Tutor conversation entity.
class TutorConversation {
  const TutorConversation({
    required this.id,
    required this.title,
    required this.subjectId,
    required this.createdAt,
    required this.updatedAt,
    required this.messageCount,
  });

  final String id;
  final String title;
  final String subjectId;
  final DateTime createdAt;
  final DateTime updatedAt;
  final int messageCount;
}
