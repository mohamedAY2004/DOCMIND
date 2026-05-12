class TutorConversationDto {
  const TutorConversationDto({
    required this.id,
    required this.title,
    required this.subjectId,
    required this.createdAt,
    required this.updatedAt,
    required this.messageCount,
  });

  final String id;
  final String title;
  final String subjectId;
  final DateTime createdAt;
  final DateTime updatedAt;
  final int messageCount;

  factory TutorConversationDto.fromJson(Map<String, dynamic> json) {
    return TutorConversationDto(
      id: json['id'] as String? ?? '',
      title: json['title'] as String? ?? '',
      subjectId: json['subjectId'] as String? ?? '',
      createdAt: DateTime.tryParse(json['createdAt'] as String? ?? '') ??
          DateTime.now(),
      updatedAt: DateTime.tryParse(json['updatedAt'] as String? ?? '') ??
          DateTime.now(),
      messageCount: json['messageCount'] as int? ?? 0,
    );
  }
}
