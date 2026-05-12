/// Failure types for document chat operations.
class DocumentChatFailure implements Exception {
  const DocumentChatFailure(this.message);

  final String message;

  @override
  String toString() => message;
}

/// Network-related failures.
class NetworkFailure extends DocumentChatFailure {
  const NetworkFailure(super.message);
}

/// Validation failures (422 errors).
class ValidationFailure extends DocumentChatFailure {
  const ValidationFailure(super.message);
}

/// Authentication failures (401 errors).
class AuthenticationFailure extends DocumentChatFailure {
  const AuthenticationFailure(super.message);
}

/// File-related failures.
class FileUploadFailure extends DocumentChatFailure {
  const FileUploadFailure(super.message);
}

/// Conversation not found.
class ConversationNotFoundFailure extends DocumentChatFailure {
  const ConversationNotFoundFailure(super.message);
}
