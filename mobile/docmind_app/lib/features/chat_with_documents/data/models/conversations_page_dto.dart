import 'document_conversation_dto.dart';

/// Paginated response DTO for listing document conversations.
class ConversationsPageDto {
  const ConversationsPageDto({
    required this.items,
    required this.page,
    required this.pageSize,
    required this.total,
    required this.totalPages,
  });

  final List<DocumentConversationDto> items;
  final int page;
  final int pageSize;
  final int total;
  final int totalPages;

  factory ConversationsPageDto.fromJson(Map<String, dynamic> json) {
    return ConversationsPageDto(
      items: (json['items'] as List<dynamic>?)
              ?.map((e) =>
                  DocumentConversationDto.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      page: json['page'] as int? ?? 1,
      pageSize: json['pageSize'] as int? ?? 20,
      total: json['total'] as int? ?? 0,
      totalPages: json['totalPages'] as int? ?? 1,
    );
  }
}
