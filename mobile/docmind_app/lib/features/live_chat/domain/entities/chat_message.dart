/// Identifies the origin of a chat message.
enum MessageSender { user, ai }

/// A single message in a live chat session.
///
/// Pure Dart — no Flutter or framework dependencies.
class ChatMessage {
  const ChatMessage({
    required this.id,
    required this.content,
    required this.sender,
    required this.timestamp,
    this.isThinking = false,
  });

  final String id;
  final String content;
  final MessageSender sender;
  final DateTime timestamp;
  final bool isThinking;

  bool get isUser => sender == MessageSender.user;
}
