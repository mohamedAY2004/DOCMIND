import 'package:fpdart/fpdart.dart';
import '../../../../core/domain/failure.dart';
import '../entities/chat_session.dart';
import '../entities/chat_turn.dart';
import '../repositories/live_chat_repository.dart';

class SendMessageUseCase {
  const SendMessageUseCase(this._repository);
  final LiveChatRepository _repository;

  Future<Either<Failure, ChatTurn>> call({
    required String sessionId,
    required String message,
    required KnowledgeSourceType sourceType,
  }) async {
    if (sessionId.isEmpty || message.trim().isEmpty || message.length > 4000) {
      return const Left(
        ValidationFailure(
          'A conversation and a message of 1–4000 characters are required.',
        ),
      );
    }
    return _repository.sendMessage(
      conversationId: sessionId,
      message: message.trim(),
      sourceType: sourceType,
    );
  }
}
