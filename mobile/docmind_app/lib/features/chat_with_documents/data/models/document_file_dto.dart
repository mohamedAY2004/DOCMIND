/// Processing status for an uploaded document file.
enum FileProcessingStatus {
  processing,
  completed,
  failed,
}

/// Data Transfer Object for a document file from the API.
class DocumentFileDto {
  const DocumentFileDto({
    required this.id,
    required this.name,
    required this.status,
    this.sizeBytes,
    this.mime,
  });

  final String id;
  final String name;
  final FileProcessingStatus status;
  final int? sizeBytes;
  final String? mime;

  factory DocumentFileDto.fromJson(Map<String, dynamic> json) {
    final statusStr = json['status'] as String? ?? 'processing';
    final status = switch (statusStr.toLowerCase()) {
      'completed' => FileProcessingStatus.completed,
      'ready' => FileProcessingStatus.completed,
      'failed' => FileProcessingStatus.failed,
      _ => FileProcessingStatus.processing,
    };

    return DocumentFileDto(
      id: json['id'] as String? ?? '',
      name: json['name'] as String? ?? '',
      status: status,
      sizeBytes: json['sizeBytes'] as int?,
      mime: json['mime'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'status': status.name,
      'sizeBytes': sizeBytes,
      'mime': mime,
    };
  }
}
