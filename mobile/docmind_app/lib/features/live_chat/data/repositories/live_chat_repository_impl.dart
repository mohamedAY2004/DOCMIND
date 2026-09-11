import 'package:fpdart/fpdart.dart';
import '../../../../core/domain/failure.dart';
import '../../../../core/network/repository_call.dart';
import '../../domain/entities/chat_messages_page.dart';
import '../../domain/entities/chat_session.dart';
import '../../domain/entities/chat_turn.dart';
import '../../domain/repositories/live_chat_repository.dart';
import '../datasources/live_chat_remote_data_source.dart';

class LiveChatRepositoryImpl implements LiveChatRepository {
  const LiveChatRepositoryImpl(this._remote);
  final LiveChatRemoteDataSource _remote;

  @override
  Future<Either<Failure, ChatMessagesPage>> getConversationMessages({
    required String conversationId,
    required KnowledgeSourceType sourceType,
    int page = 1,
    int pageSize = 50,
  }) => repositoryCall(() async {
    final dto = await _remote.getConversationMessages(
      conversationId: conversationId,
      sourceType: sourceType,
      page: page,
      pageSize: pageSize,
    );
    return ChatMessagesPage(
      items: dto.items.reversed.map((message) => message.toDomain()).toList(),
      page: dto.page,
      pageSize: dto.pageSize,
      total: dto.total,
      totalPages: dto.totalPages,
    );
  });

  @override
  Future<Either<Failure, ChatTurn>> sendMessage({
    required String conversationId,
    required String message,
    required KnowledgeSourceType sourceType,
  }) => repositoryCall(() async {
    final dto = await _remote.sendMessage(
      conversationId: conversationId,
      message: message,
      sourceType: sourceType,
    );
    return ChatTurn(
      userMessage: dto.userMessage.toDomain(),
      reply: dto.reply.toDomain(),
    );
  });
}
