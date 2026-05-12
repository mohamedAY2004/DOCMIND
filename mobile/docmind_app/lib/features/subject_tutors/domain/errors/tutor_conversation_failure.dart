/// Domain-level failure for tutor conversations.
class TutorConversationFailure implements Exception {
  const TutorConversationFailure(this.message);

  final String message;

  @override
  String toString() => message;
}
