import 'dart:io';

import '../entities/document_file.dart';
import '../repositories/document_chat_repository.dart';

/// Use case for creating a new document conversation.
class CreateDocumentConversationUseCase {
  const CreateDocumentConversationUseCase(this._repository);

  final DocumentChatRepository _repository;

  Future<CreateConversationResult> call(
    File file, {
    void Function(int sent, int total)? onProgress,
  }) async {
    final result = await _repository.createConversation(
      file,
      onProgress: onProgress,
    );

    return CreateConversationResult(
      conversationId: result.conversationId,
      title: result.title,
      files: result.files,
    );
  }
}

/// Result of creating a document conversation.
class CreateConversationResult {
  const CreateConversationResult({
    required this.conversationId,
    required this.title,
    required this.files,
  });

  final String conversationId;
  final String title;
  final List<DocumentFile> files;

  bool get isProcessing =>
      files.any((f) => f.status == DocumentFileStatus.processing);
  bool get isReady =>
      files.isNotEmpty && files.every((f) => f.status == DocumentFileStatus.completed);
  bool get hasFailed =>
      files.any((f) => f.status == DocumentFileStatus.failed);
}
