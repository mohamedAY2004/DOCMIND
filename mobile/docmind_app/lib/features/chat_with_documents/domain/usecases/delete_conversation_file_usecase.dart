import '../repositories/document_chat_repository.dart';

/// Deletes a file from a document conversation.
class DeleteConversationFileUseCase {
  const DeleteConversationFileUseCase(this._repository);

  final DocumentChatRepository _repository;

  Future<void> call({
    required String conversationId,
    required String fileId,
  }) {
    return _repository.deleteConversationFile(
      conversationId: conversationId,
      fileId: fileId,
    );
  }
}
