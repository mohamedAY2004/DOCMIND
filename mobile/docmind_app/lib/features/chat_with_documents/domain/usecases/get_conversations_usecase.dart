import '../entities/conversations_page.dart';
import '../repositories/document_chat_repository.dart';

/// Use case for fetching the list of document conversations.
class GetConversationsUseCase {
  const GetConversationsUseCase(this._repository);

  final DocumentChatRepository _repository;

  Future<ConversationsPage> call({
    int page = 1,
    int pageSize = 20,
  }) async {
    return _repository.getConversations(
      page: page,
      pageSize: pageSize,
    );
  }
}
