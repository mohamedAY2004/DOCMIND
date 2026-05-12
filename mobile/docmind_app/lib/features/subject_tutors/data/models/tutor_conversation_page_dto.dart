import 'tutor_conversation_dto.dart';

class TutorConversationPageDto {
  const TutorConversationPageDto({
    required this.items,
    required this.page,
    required this.pageSize,
    required this.total,
    required this.totalPages,
  });

  final List<TutorConversationDto> items;
  final int page;
  final int pageSize;
  final int total;
  final int totalPages;

  factory TutorConversationPageDto.fromJson(Map<String, dynamic> json) {
    return TutorConversationPageDto(
      items: (json['items'] as List<dynamic>?)
              ?.map((e) => TutorConversationDto.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
      page: json['page'] as int? ?? 1,
      pageSize: json['pageSize'] as int? ?? 20,
      total: json['total'] as int? ?? 0,
      totalPages: json['totalPages'] as int? ?? 0,
    );
  }
}
