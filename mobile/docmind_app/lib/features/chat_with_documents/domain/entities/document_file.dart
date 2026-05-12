/// Processing status for an uploaded document file.
enum DocumentFileStatus {
  processing,
  completed,
  failed,
}

/// Domain entity for a document file.
class DocumentFile {
  const DocumentFile({
    required this.id,
    required this.name,
    required this.status,
    this.sizeBytes,
    this.mime,
  });

  final String id;
  final String name;
  final DocumentFileStatus status;
  final int? sizeBytes;
  final String? mime;

  bool get isReady => status == DocumentFileStatus.completed;
  bool get isFailed => status == DocumentFileStatus.failed;
  bool get isProcessing => status == DocumentFileStatus.processing;
}
