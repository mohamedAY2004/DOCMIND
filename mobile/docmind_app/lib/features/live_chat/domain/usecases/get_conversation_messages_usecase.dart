import '../entities/chat_message.dart';
import '../entities/chat_session.dart';
import '../repositories/live_chat_repository.dart';

class GetConversationMessagesUseCase {
  const GetConversationMessagesUseCase(this._repository);

  final LiveChatRepository _repository;

  Future<List<ChatMessage>> call({
    required String conversationId,
    required KnowledgeSourceType sourceType,
    int page = 1,
    int pageSize = 20,
  }) async {
    final result = await _repository.getConversationMessages(
      conversationId: conversationId,
      sourceType: sourceType,
      page: page,
      pageSize: pageSize,
    );
    return result.items;
  }
}
