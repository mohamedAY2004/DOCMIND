import 'dart:io';

import '../entities/document_file.dart';
import '../repositories/document_chat_repository.dart';

/// Adds a new file to an existing document conversation.
class AddConversationFileUseCase {
  const AddConversationFileUseCase(this._repository);

  final DocumentChatRepository _repository;

  Future<DocumentFile> call({
    required String conversationId,
    required File file,
    void Function(int sent, int total)? onProgress,
  }) {
    return _repository.addConversationFile(
      conversationId: conversationId,
      file: file,
      onProgress: onProgress,
    );
  }
}
