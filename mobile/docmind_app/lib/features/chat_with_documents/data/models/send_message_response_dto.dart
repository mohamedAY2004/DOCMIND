import '../../../live_chat/data/models/chat_message_dto.dart';

/// Response DTO for sending a message in a document conversation.
class SendMessageResponseDto {
  const SendMessageResponseDto({
    required this.userMessage,
    required this.reply,
  });

  final ChatMessageDto userMessage;
  final ChatMessageDto reply;

  factory SendMessageResponseDto.fromJson(Map<String, dynamic> json) {
    return SendMessageResponseDto(
      userMessage: ChatMessageDto.fromJson(
        json['userMessage'] as Map<String, dynamic>? ?? {},
      ),
      reply: ChatMessageDto.fromJson(
        json['reply'] as Map<String, dynamic>? ?? {},
      ),
    );
  }
}
