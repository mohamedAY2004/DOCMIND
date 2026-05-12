/// Describes the origin of the knowledge that the AI is reasoning over.
enum KnowledgeSourceType {
  document,
  subject,
}

/// An active chat session linked to a knowledge source.
///
/// Shared by Chat-With-Documents and AI Subject Tutors (future).
/// Pure Dart — no Flutter or framework dependencies.
class ChatSession {
  ChatSession({
    required this.sessionId,
    required this.knowledgeSourceId,
    required this.sourceType,
    this.displayName,
  });

  String sessionId;
  final String knowledgeSourceId;
  final KnowledgeSourceType sourceType;

  /// Human-readable label shown in the app bar (e.g. file name or subject name).
  final String? displayName;
}

