import 'dart:io';

import 'package:dio/dio.dart';

import '../../../../core/network/dio_client.dart';
import '../../../auth/data/datasources/auth_local_data_source.dart';
import '../../domain/errors/document_chat_failure.dart';
import '../models/conversations_page_dto.dart';
import '../models/create_conversation_response_dto.dart';
import '../models/document_file_dto.dart';
import '../models/send_message_request.dart';
import '../models/send_message_response_dto.dart';
import '../../../live_chat/data/models/chat_messages_page_dto.dart';

/// Remote data source for document chat API calls.
class DocumentChatRemoteDataSource {
  DocumentChatRemoteDataSource({
    Dio? dio,
    AuthLocalDataSource? authLocal,
  })  : _dio = dio ?? DioClient.instance,
        _authLocal = authLocal ?? AuthLocalDataSource();

  final Dio _dio;
  final AuthLocalDataSource _authLocal;

  /// Creates a new document conversation by uploading a file.
  /// POST /chat/doc/conversations
  Future<CreateConversationResponseDto> createConversation(
    File file, {
    void Function(int sent, int total)? onProgress,
  }) async {
    final token = await _authLocal.getToken();
    if (token == null || token.isEmpty) {
      throw const AuthenticationFailure('User is not authenticated');
    }

    final fileName = file.path.split(RegExp(r'[/\\]')).last;

    try {
      final formData = FormData.fromMap({
        'files': await MultipartFile.fromFile(
          file.path,
          filename: fileName,
        ),
      });

      final response = await _dio.post(
        '/chat/doc/conversations',
        data: formData,
        options: Options(
          headers: {
            'Authorization': 'Bearer $token',
            'Content-Type': 'multipart/form-data',
          },
        ),
        onSendProgress: onProgress,
      );

      if (response.data is Map<String, dynamic>) {
        return CreateConversationResponseDto.fromJson(
          response.data as Map<String, dynamic>,
        );
      }

      throw const DocumentChatFailure('Unexpected server response');
    } on DioException catch (e) {
      throw _mapDioError(e);
    } catch (e) {
      throw DocumentChatFailure('Failed to upload file: $e');
    }
  }

  /// Lists all document conversations.
  /// GET /chat/doc/conversations
  Future<ConversationsPageDto> getConversations({
    int page = 1,
    int pageSize = 20,
  }) async {
    final token = await _authLocal.getToken();
    if (token == null || token.isEmpty) {
      throw const AuthenticationFailure('User is not authenticated');
    }

    try {
      final response = await _dio.get(
        '/chat/doc/conversations',
        queryParameters: {
          'page': page,
          'pageSize': pageSize,
        },
        options: Options(headers: {'Authorization': 'Bearer $token'}),
      );

      if (response.data is Map<String, dynamic>) {
        return ConversationsPageDto.fromJson(
          response.data as Map<String, dynamic>,
        );
      }

      throw const DocumentChatFailure('Unexpected server response');
    } on DioException catch (e) {
      throw _mapDioError(e);
    }
  }

  /// Gets messages for a specific conversation.
  /// GET /chat/doc/conversations/{conv_id}/messages
  Future<ChatMessagesPageDto> getMessages({
    required String conversationId,
    int page = 1,
    int pageSize = 20,
  }) async {
    final token = await _authLocal.getToken();
    if (token == null || token.isEmpty) {
      throw const AuthenticationFailure('User is not authenticated');
    }

    try {
      final response = await _dio.get(
        '/chat/doc/conversations/$conversationId/messages',
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

      throw const DocumentChatFailure('Unexpected server response');
    } on DioException catch (e) {
      throw _mapDioError(e);
    }
  }

  /// Sends a message in a document conversation.
  /// POST /chat/doc/conversations/{conv_id}/messages
  Future<SendMessageResponseDto> sendMessage({
    required String conversationId,
    required String message,
  }) async {
    final token = await _authLocal.getToken();
    if (token == null || token.isEmpty) {
      throw const AuthenticationFailure('User is not authenticated');
    }

    try {
      final response = await _dio.post(
        '/chat/doc/conversations/$conversationId/messages',
        data: SendMessageRequest(message: message).toJson(),
        options: Options(headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        }),
      );

      if (response.data is Map<String, dynamic>) {
        return SendMessageResponseDto.fromJson(
          response.data as Map<String, dynamic>,
        );
      }

      throw const DocumentChatFailure('Unexpected server response');
    } on DioException catch (e) {
      throw _mapDioError(e);
    }
  }

  /// Deletes a document conversation.
  /// DELETE /chat/doc/conversations/{conv_id}
  Future<void> deleteConversation({required String conversationId}) async {
    final token = await _authLocal.getToken();
    if (token == null || token.isEmpty) {
      throw const AuthenticationFailure('User is not authenticated');
    }

    try {
      await _dio.delete(
        '/chat/doc/conversations/$conversationId',
        options: Options(headers: {'Authorization': 'Bearer $token'}),
      );
    } on DioException catch (e) {
      throw _mapDioError(e);
    }
  }

  /// Lists files associated with a document conversation.
  /// GET /chat/doc/conversations/{conv_id}/files
  Future<List<DocumentFileDto>> getConversationFiles({
    required String conversationId,
  }) async {
    final token = await _authLocal.getToken();
    if (token == null || token.isEmpty) {
      throw const AuthenticationFailure('User is not authenticated');
    }

    try {
      final response = await _dio.get(
        '/chat/doc/conversations/$conversationId/files',
        options: Options(headers: {'Authorization': 'Bearer $token'}),
      );

      if (response.data is List) {
        return (response.data as List)
            .whereType<Map<String, dynamic>>()
            .map(DocumentFileDto.fromJson)
            .toList();
      }

      throw const DocumentChatFailure('Unexpected server response');
    } on DioException catch (e) {
      throw _mapDioError(e);
    }
  }

  /// Adds a file to an existing document conversation.
  /// POST /chat/doc/conversations/{conv_id}/files
  Future<DocumentFileDto> addConversationFile({
    required String conversationId,
    required File file,
    void Function(int sent, int total)? onProgress,
  }) async {
    final token = await _authLocal.getToken();
    if (token == null || token.isEmpty) {
      throw const AuthenticationFailure('User is not authenticated');
    }

    final fileName = file.path.split(RegExp(r'[/\\]')).last;

    try {
      final formData = FormData.fromMap({
        'file': await MultipartFile.fromFile(
          file.path,
          filename: fileName,
        ),
      });

      final response = await _dio.post(
        '/chat/doc/conversations/$conversationId/files',
        data: formData,
        options: Options(
          headers: {
            'Authorization': 'Bearer $token',
            'Content-Type': 'multipart/form-data',
          },
        ),
        onSendProgress: onProgress,
      );

      if (response.data is Map<String, dynamic>) {
        return DocumentFileDto.fromJson(
          response.data as Map<String, dynamic>,
        );
      }

      throw const DocumentChatFailure('Unexpected server response');
    } on DioException catch (e) {
      throw _mapDioError(e);
    } catch (e) {
      throw DocumentChatFailure('Failed to upload file: $e');
    }
  }

  /// Deletes a file from a document conversation.
  /// DELETE /chat/doc/conversations/{conv_id}/files/{file_id}
  Future<void> deleteConversationFile({
    required String conversationId,
    required String fileId,
  }) async {
    final token = await _authLocal.getToken();
    if (token == null || token.isEmpty) {
      throw const AuthenticationFailure('User is not authenticated');
    }

    try {
      await _dio.delete(
        '/chat/doc/conversations/$conversationId/files/$fileId',
        options: Options(headers: {'Authorization': 'Bearer $token'}),
      );
    } on DioException catch (e) {
      throw _mapDioError(e);
    }
  }

  /// Maps Dio errors to domain failures.
  DocumentChatFailure _mapDioError(DioException e) {
    final status = e.response?.statusCode;
    final data = e.response?.data;

    // Authentication error
    if (status == 401) {
      return const AuthenticationFailure('Session expired. Please login again.');
    }

    // Validation error (422)
    if (status == 422 && data is Map<String, dynamic>) {
      final detail = data['detail'];
      if (detail is List && detail.isNotEmpty) {
        final first = detail.first;
        if (first is Map<String, dynamic>) {
          return ValidationFailure(first['msg'] as String? ?? 'Invalid input');
        }
      }
      return const ValidationFailure('Invalid request parameters');
    }

    // Not found
    if (status == 404) {
      return const ConversationNotFoundFailure('Conversation not found');
    }

    // Network error
    if (e.type == DioExceptionType.connectionTimeout ||
        e.type == DioExceptionType.receiveTimeout ||
        e.type == DioExceptionType.connectionError) {
      return const NetworkFailure('Network error. Please check your connection.');
    }

    // Generic error
    return DocumentChatFailure(
      data is Map<String, dynamic>
          ? (data['message'] as String? ?? 'Something went wrong')
          : 'Something went wrong. Please try again.',
    );
  }
}
