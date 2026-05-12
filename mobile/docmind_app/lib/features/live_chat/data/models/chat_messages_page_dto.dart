import 'chat_message_dto.dart';

class ChatMessagesPageDto {
  const ChatMessagesPageDto({
    required this.items,
    required this.page,
    required this.pageSize,
    required this.total,
    required this.totalPages,
  });

  final List<ChatMessageDto> items;
  final int page;
  final int pageSize;
  final int total;
  final int totalPages;

  factory ChatMessagesPageDto.fromJson(Map<String, dynamic> json) {
    return ChatMessagesPageDto(
      items: (json['items'] as List<dynamic>?)
              ?.map((e) => ChatMessageDto.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      page: json['page'] as int? ?? 1,
      pageSize: json['pageSize'] as int? ?? 20,
      total: json['total'] as int? ?? 0,
      totalPages: json['totalPages'] as int? ?? 1,
    );
  }
}
