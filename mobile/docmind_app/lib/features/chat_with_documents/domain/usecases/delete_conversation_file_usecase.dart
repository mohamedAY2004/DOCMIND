import 'package:fpdart/fpdart.dart';
import '../../../../core/domain/failure.dart';
import '../repositories/document_chat_repository.dart';

/// Deletes a file from a document conversation.
class DeleteConversationFileUseCase {
  const DeleteConversationFileUseCase(this._repository);

  final DocumentChatRepository _repository;

  Future<Either<Failure, void>> call({
    required String conversationId,
    required String fileId,
  }) {
    return _repository.deleteConversationFile(
      conversationId: conversationId,
      fileId: fileId,
    );
  }
}
