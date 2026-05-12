import '../repositories/document_chat_repository.dart';

/// Use case for deleting a document conversation.
class DeleteDocumentConversationUseCase {
  const DeleteDocumentConversationUseCase(this._repository);

  final DocumentChatRepository _repository;

  Future<void> call(String conversationId) async {
    await _repository.deleteConversation(conversationId);
  }
}
