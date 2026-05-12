/// Data Transfer Object for a document conversation from the API.
class DocumentConversationDto {
  const DocumentConversationDto({
    required this.id,
    required this.title,
    this.subjectId,
    required this.createdAt,
    required this.updatedAt,
    required this.messageCount,
  });

  final String id;
  final String title;
  final String? subjectId;
  final DateTime createdAt;
  final DateTime updatedAt;
  final int messageCount;

  factory DocumentConversationDto.fromJson(Map<String, dynamic> json) {
    return DocumentConversationDto(
      id: json['id'] as String? ?? '',
      title: json['title'] as String? ?? '',
      subjectId: json['subjectId'] as String?,
      createdAt: DateTime.tryParse(json['createdAt'] as String? ?? '') ??
          DateTime.now(),
      updatedAt: DateTime.tryParse(json['updatedAt'] as String? ?? '') ??
          DateTime.now(),
      messageCount: json['messageCount'] as int? ?? 0,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'title': title,
      'subjectId': subjectId,
      'createdAt': createdAt.toIso8601String(),
      'updatedAt': updatedAt.toIso8601String(),
      'messageCount': messageCount,
    };
  }
}
