import '../entities/document_file.dart';
import '../repositories/document_chat_repository.dart';

/// Loads files attached to a document conversation.
class GetConversationFilesUseCase {
  const GetConversationFilesUseCase(this._repository);

  final DocumentChatRepository _repository;

  Future<List<DocumentFile>> call({required String conversationId}) {
    return _repository.getConversationFiles(conversationId: conversationId);
  }
}
