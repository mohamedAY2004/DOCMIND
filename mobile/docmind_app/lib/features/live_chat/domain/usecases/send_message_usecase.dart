import 'package:dio/dio.dart';

import '../../../../core/network/dio_client.dart';
import '../../../auth/data/datasources/auth_local_data_source.dart';
import '../entities/chat_message.dart';
import '../entities/chat_session.dart';

/// Sends a user message to the conversation API and returns the AI reply.
/// Uses different endpoints based on sourceType:
/// - Document: POST /chat/doc/conversations/{conv_id}/messages
/// - Subject: POST /chat/tutor/conversations/{conv_id}/messages
class SendMessageUseCase {
  SendMessageUseCase({Dio? dio, AuthLocalDataSource? authLocal})
      : _dio = dio ?? DioClient.instance,
        _authLocal = authLocal ?? AuthLocalDataSource();

  final Dio _dio;
  final AuthLocalDataSource _authLocal;

  /// Posts the message to the appropriate endpoint based on sourceType
  /// and returns the AI reply as a [ChatMessage].
  Future<ChatMessage> call({
    required String sessionId,
    required String message,
    required KnowledgeSourceType sourceType,
  }) async {
    if (sessionId.isEmpty) {
      throw ArgumentError('sessionId must not be empty');
    }
    if (message.trim().isEmpty) {
      throw ArgumentError('message must not be blank');
    }

    final token = await _authLocal.getToken();
    if (token == null || token.isEmpty) {
      throw ArgumentError('User is not authenticated');
    }

    final endpoint = sourceType == KnowledgeSourceType.document
        ? '/chat/doc/conversations/$sessionId/messages'
        : '/chat/tutor/conversations/$sessionId/messages';

    try {
      final response = await _dio.post(
        endpoint,
        data: {'message': message},
        options: Options(headers: {'Authorization': 'Bearer $token'}),
      );

      if (response.data is Map<String, dynamic>) {
        final map = response.data as Map<String, dynamic>;
        final reply = map['reply'] as Map<String, dynamic>?;
        if (reply == null) {
          throw Exception('No reply from server');
        }

        final id = reply['id'] as String? ?? DateTime.now().toString();
        final text = reply['text'] as String? ?? '';
        final createdAt = reply['createdAt'] as String?;
        final timestamp = createdAt != null
            ? DateTime.tryParse(createdAt) ?? DateTime.now()
            : DateTime.now();

        return ChatMessage(
          id: id,
          content: text,
          sender: MessageSender.ai,
          timestamp: timestamp,
        );
      }

      throw Exception('Unexpected server response');
    } on DioException catch (e) {
      final status = e.response?.statusCode;
      if (status == 422) {
        // Let caller handle validation errors.
        rethrow;
      }
      rethrow;
    }
  }
}
