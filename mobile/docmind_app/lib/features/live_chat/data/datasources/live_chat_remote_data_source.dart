import 'package:dio/dio.dart';
import '../../../../core/network/api_constants.dart';
import '../../domain/entities/chat_session.dart';
import '../models/chat_messages_page_dto.dart';
import '../models/send_message_response_dto.dart';

class LiveChatRemoteDataSource {
  const LiveChatRemoteDataSource(this._dio);
  final Dio _dio;

  Future<ChatMessagesPageDto> getConversationMessages({
    required String conversationId,
    required KnowledgeSourceType sourceType,
    int page = 1,
    int pageSize = 50,
  }) async {
    final response = await _dio.get(
      ApiConstants.messages(
        conversationId,
        document: sourceType == KnowledgeSourceType.document,
      ),
      queryParameters: {'page': page, 'pageSize': pageSize, 'order': 'desc'},
    );
    return ChatMessagesPageDto.fromJson(response.data as Map<String, dynamic>);
  }

  Future<SendMessageResponseDto> sendMessage({
    required String conversationId,
    required String message,
    required KnowledgeSourceType sourceType,
  }) async {
    final response = await _dio.post(
      ApiConstants.messages(
        conversationId,
        document: sourceType == KnowledgeSourceType.document,
      ),
      data: {'message': message},
    );
    return SendMessageResponseDto.fromJson(
      response.data as Map<String, dynamic>,
    );
  }
}
