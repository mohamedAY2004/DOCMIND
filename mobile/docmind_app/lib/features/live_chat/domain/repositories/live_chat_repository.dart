import 'package:fpdart/fpdart.dart';
import '../../../../core/domain/failure.dart';
import '../entities/chat_messages_page.dart';
import '../entities/chat_session.dart';
import '../entities/chat_turn.dart';

abstract class LiveChatRepository {
  Future<Either<Failure, ChatMessagesPage>> getConversationMessages({
    required String conversationId,
    required KnowledgeSourceType sourceType,
    int page = 1,
    int pageSize = 50,
  });
  Future<Either<Failure, ChatTurn>> sendMessage({
    required String conversationId,
    required String message,
    required KnowledgeSourceType sourceType,
  });
}
