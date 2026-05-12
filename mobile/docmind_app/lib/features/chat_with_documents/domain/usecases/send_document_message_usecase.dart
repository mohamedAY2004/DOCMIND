import '../entities/send_message_result.dart';
import '../repositories/document_chat_repository.dart';

/// Sends a user message in a document conversation and returns both
/// the user message and AI reply.
class SendDocumentMessageUseCase {
  const SendDocumentMessageUseCase(this._repository);

  final DocumentChatRepository _repository;

  Future<SendMessageResult> call({
    required String conversationId,
    required String message,
  }) async {
    if (conversationId.isEmpty) {
      throw ArgumentError('conversationId must not be empty');
    }
    if (message.trim().isEmpty) {
      throw ArgumentError('message must not be blank');
    }

    return _repository.sendMessage(
      conversationId: conversationId,
      message: message.trim(),
    );
  }
}
