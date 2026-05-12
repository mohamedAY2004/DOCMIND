import '../../../live_chat/domain/repositories/live_chat_repository.dart';
import '../repositories/document_chat_repository.dart';

/// Use case for fetching messages from a document conversation.
class GetDocumentMessagesUseCase {
  const GetDocumentMessagesUseCase(this._repository);

  final DocumentChatRepository _repository;

  Future<ChatMessagesPage> call(
    String conversationId, {
    int page = 1,
    int pageSize = 20,
  }) async {
    return _repository.getMessages(
      conversationId,
      page: page,
      pageSize: pageSize,
    );
  }
}
