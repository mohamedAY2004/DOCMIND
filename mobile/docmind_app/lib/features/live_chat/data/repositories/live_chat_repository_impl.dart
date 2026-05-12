import '../datasources/live_chat_remote_data_source.dart';
import '../../domain/entities/chat_message.dart';
import '../../domain/entities/chat_session.dart';
import '../../domain/repositories/live_chat_repository.dart';

class LiveChatRepositoryImpl implements LiveChatRepository {
  LiveChatRepositoryImpl({LiveChatRemoteDataSource? remote})
      : _remote = remote ?? LiveChatRemoteDataSource();

  final LiveChatRemoteDataSource _remote;

  @override
  Future<ChatMessagesPage> getConversationMessages({
    required String conversationId,
    required KnowledgeSourceType sourceType,
    int page = 1,
    int pageSize = 20,
  }) async {
    final pageDto = await _remote.getConversationMessages(
      conversationId: conversationId,
      sourceType: sourceType,
      page: page,
      pageSize: pageSize,
    );

    final items = pageDto.items
        .map(
          (dto) => ChatMessage(
            id: dto.id,
            content: dto.text,
            sender: dto.role == 'user' ? MessageSender.user : MessageSender.ai,
            timestamp: dto.createdAt,
            isThinking: false,
          ),
        )
        .toList();

    return ChatMessagesPage(
      items: items,
      page: pageDto.page,
      pageSize: pageDto.pageSize,
      total: pageDto.total,
      totalPages: pageDto.totalPages,
    );
  }
}

