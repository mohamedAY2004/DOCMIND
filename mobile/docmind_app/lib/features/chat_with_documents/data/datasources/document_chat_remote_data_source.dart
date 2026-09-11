import 'dart:io';
import 'package:dio/dio.dart';
import '../../../../core/network/api_constants.dart';
import '../models/conversations_page_dto.dart';
import '../models/create_conversation_response_dto.dart';
import '../models/document_file_dto.dart';

/// File and conversation management; message transport belongs to live_chat.
class DocumentChatRemoteDataSource {
  const DocumentChatRemoteDataSource(this._dio);
  final Dio _dio;

  Future<FormData> _fileBody(File file, String field) async =>
      FormData.fromMap({
        field: await MultipartFile.fromFile(
          file.path,
          filename: file.uri.pathSegments.last,
        ),
      });

  Future<CreateConversationResponseDto> createConversation(
    File file, {
    void Function(int, int)? onProgress,
  }) async {
    final response = await _dio.post(
      ApiConstants.docConversations,
      data: await _fileBody(file, 'files'),
      onSendProgress: onProgress,
      options: Options(sendTimeout: const Duration(minutes: 3)),
    );
    return CreateConversationResponseDto.fromJson(
      response.data as Map<String, dynamic>,
    );
  }

  Future<ConversationsPageDto> getConversations({
    int page = 1,
    int pageSize = 20,
  }) async {
    final response = await _dio.get(
      ApiConstants.docConversations,
      queryParameters: {'page': page, 'pageSize': pageSize},
    );
    return ConversationsPageDto.fromJson(response.data as Map<String, dynamic>);
  }

  Future<void> deleteConversation({required String conversationId}) async {
    await _dio.delete(ApiConstants.docConversation(conversationId));
  }

  Future<List<DocumentFileDto>> getConversationFiles({
    required String conversationId,
  }) async {
    final response = await _dio.get(ApiConstants.docFiles(conversationId));
    return (response.data as List)
        .map((item) => DocumentFileDto.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  Future<DocumentFileDto> addConversationFile({
    required String conversationId,
    required File file,
    void Function(int, int)? onProgress,
  }) async {
    final response = await _dio.post(
      ApiConstants.docFiles(conversationId),
      data: await _fileBody(file, 'file'),
      onSendProgress: onProgress,
      options: Options(sendTimeout: const Duration(minutes: 3)),
    );
    return DocumentFileDto.fromJson(response.data as Map<String, dynamic>);
  }

  Future<void> deleteConversationFile({
    required String conversationId,
    required String fileId,
  }) async {
    await _dio.delete(ApiConstants.docFile(conversationId, fileId));
  }
}
