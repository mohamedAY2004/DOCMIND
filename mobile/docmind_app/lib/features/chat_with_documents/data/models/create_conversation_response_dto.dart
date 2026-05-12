import 'document_conversation_dto.dart';
import 'document_file_dto.dart';

/// Response DTO for creating a new document conversation.
class CreateConversationResponseDto {
  const CreateConversationResponseDto({
    required this.conversation,
    required this.files,
  });

  final DocumentConversationDto conversation;
  final List<DocumentFileDto> files;

  factory CreateConversationResponseDto.fromJson(Map<String, dynamic> json) {
    return CreateConversationResponseDto(
      conversation: DocumentConversationDto.fromJson(
        json['conversation'] as Map<String, dynamic>? ?? {},
      ),
      files: (json['files'] as List<dynamic>?)
              ?.map((e) => DocumentFileDto.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
    );
  }
}
