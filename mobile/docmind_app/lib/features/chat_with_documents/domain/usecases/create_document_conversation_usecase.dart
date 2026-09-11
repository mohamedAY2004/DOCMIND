import 'package:fpdart/fpdart.dart';
import '../../../../core/domain/failure.dart';
import 'dart:io';
import '../entities/document_upload_result.dart';
import '../repositories/document_chat_repository.dart';

class CreateDocumentConversationUseCase {
  const CreateDocumentConversationUseCase(this._repository);
  final DocumentChatRepository _repository;
  Future<Either<Failure, DocumentChatCreateResult>> call(
    File file, {
    void Function(int, int)? onProgress,
  }) => _repository.createConversation(file, onProgress: onProgress);
}
