import 'package:fpdart/fpdart.dart';
import '../../../../core/domain/failure.dart';
import '../repositories/document_chat_repository.dart';

/// Use case for deleting a document conversation.
class DeleteDocumentConversationUseCase {
  const DeleteDocumentConversationUseCase(this._repository);

  final DocumentChatRepository _repository;

  Future<Either<Failure, void>> call(String conversationId) async {
    return _repository.deleteConversation(conversationId);
  }
}
