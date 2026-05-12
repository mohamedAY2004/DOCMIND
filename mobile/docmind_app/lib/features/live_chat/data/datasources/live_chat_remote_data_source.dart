import 'package:dio/dio.dart';

import '../../../../core/network/dio_client.dart';
import '../../../auth/data/datasources/auth_local_data_source.dart';
import '../../domain/entities/chat_session.dart';
import '../models/chat_messages_page_dto.dart';

class LiveChatRemoteDataSource {
  LiveChatRemoteDataSource({
    Dio? dio,
    AuthLocalDataSource? authLocal,
  })  : _dio = dio ?? DioClient.instance,
        _authLocal = authLocal ?? AuthLocalDataSource();

  final Dio _dio;
  final AuthLocalDataSource _authLocal;

  /// Fetches previous messages for a conversation.
  /// Uses different endpoints based on sourceType:
  /// - Document: GET /chat/doc/conversations/{conv_id}/messages
  /// - Subject: GET /chat/tutor/conversations/{conv_id}/messages
  Future<ChatMessagesPageDto> getConversationMessages({
    required String conversationId,
    required KnowledgeSourceType sourceType,
    int page = 1,
    int pageSize = 20,
  }) async {
    final token = await _authLocal.getToken();
    if (token == null || token.isEmpty) {
      throw Exception('User is not authenticated');
    }

    final endpoint = sourceType == KnowledgeSourceType.document
        ? '/chat/doc/conversations/$conversationId/messages'
        : '/chat/tutor/conversations/$conversationId/messages';

    try {
      final response = await _dio.get(
        endpoint,
        queryParameters: {
          'page': page,
          'pageSize': pageSize,
        },
        options: Options(headers: {'Authorization': 'Bearer $token'}),
      );

      if (response.data is Map<String, dynamic>) {
        return ChatMessagesPageDto.fromJson(
          response.data as Map<String, dynamic>,
        );
      }

      throw Exception('Unexpected server response');
    } on DioException catch (e) {
      final status = e.response?.statusCode;
      if (status == 422) {
        throw Exception('Invalid request parameters');
      }
      throw Exception('Failed to load messages: ${e.message}');
    }
  }
}
