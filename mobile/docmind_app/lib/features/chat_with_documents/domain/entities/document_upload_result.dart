import 'document_file.dart';

/// Result of creating a document conversation.
class DocumentChatCreateResult {
  const DocumentChatCreateResult({
    required this.conversationId,
    required this.title,
    required this.files,
  });

  final String conversationId;
  final String title;
  final List<DocumentFile> files;
  bool get isProcessing =>
      files.any((file) => file.status == DocumentFileStatus.processing);
  bool get isReady =>
      files.isNotEmpty &&
      files.every((file) => file.status == DocumentFileStatus.completed);
  bool get hasFailed =>
      files.any((file) => file.status == DocumentFileStatus.failed);
}
