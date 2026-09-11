import 'package:fpdart/fpdart.dart';
import '../../../../core/domain/failure.dart';
import '../entities/chat_messages_page.dart';
import '../entities/chat_session.dart';
import '../repositories/live_chat_repository.dart';

class GetConversationMessagesUseCase {
  const GetConversationMessagesUseCase(this._repository);
  final LiveChatRepository _repository;
  Future<Either<Failure, ChatMessagesPage>> call({
    required String conversationId,
    required KnowledgeSourceType sourceType,
    int page = 1,
    int pageSize = 50,
  }) => _repository.getConversationMessages(
    conversationId: conversationId,
    sourceType: sourceType,
    page: page,
    pageSize: pageSize,
  );
}
