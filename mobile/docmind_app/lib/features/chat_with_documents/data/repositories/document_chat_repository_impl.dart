import 'package:fpdart/fpdart.dart';
import '../../../../core/domain/failure.dart';
import '../../../../core/network/repository_call.dart';
import 'dart:io';

import '../../domain/entities/conversations_page.dart';
import '../../domain/entities/document_conversation.dart';
import '../../domain/entities/document_file.dart';
import '../../domain/repositories/document_chat_repository.dart';
import '../../domain/entities/document_upload_result.dart';
import '../datasources/document_chat_remote_data_source.dart';
import '../models/document_file_dto.dart';

/// Implementation of DocumentChatRepository.
class DocumentChatRepositoryImpl implements DocumentChatRepository {
  const DocumentChatRepositoryImpl(this._remote);

  final DocumentChatRemoteDataSource _remote;

  @override
  Future<Either<Failure, DocumentChatCreateResult>> createConversation(
    File file, {
    void Function(int sent, int total)? onProgress,
  }) => repositoryCall(() async {
    final response = await _remote.createConversation(
      file,
      onProgress: onProgress,
    );

    return DocumentChatCreateResult(
      conversationId: response.conversation.id,
      title: response.conversation.title,
      files: response.files.map(_mapFileDto).toList(),
    );
  });

  @override
  Future<Either<Failure, ConversationsPage>> getConversations({
    int page = 1,
    int pageSize = 20,
  }) => repositoryCall(() async {
    final response = await _remote.getConversations(
      page: page,
      pageSize: pageSize,
    );

    return ConversationsPage(
      items: response.items
          .map(
            (dto) => DocumentConversation(
              id: dto.id,
              title: dto.title,
              subjectId: dto.subjectId,
              createdAt: dto.createdAt,
              updatedAt: dto.updatedAt,
              messageCount: dto.messageCount,
            ),
          )
          .toList(),
      page: response.page,
      pageSize: response.pageSize,
      total: response.total,
      totalPages: response.totalPages,
    );
  });

  @override
  Future<Either<Failure, void>> deleteConversation(String conversationId) =>
      repositoryCall(() async {
        await _remote.deleteConversation(conversationId: conversationId);
      });

  @override
  Future<Either<Failure, List<DocumentFile>>> getConversationFiles({
    required String conversationId,
  }) => repositoryCall(() async {
    final response = await _remote.getConversationFiles(
      conversationId: conversationId,
    );

    return response.map(_mapFileDto).toList();
  });

  @override
  Future<Either<Failure, DocumentFile>> addConversationFile({
    required String conversationId,
    required File file,
    void Function(int sent, int total)? onProgress,
  }) => repositoryCall(() async {
    final response = await _remote.addConversationFile(
      conversationId: conversationId,
      file: file,
      onProgress: onProgress,
    );

    return _mapFileDto(response);
  });

  @override
  Future<Either<Failure, void>> deleteConversationFile({
    required String conversationId,
    required String fileId,
  }) => repositoryCall(() async {
    await _remote.deleteConversationFile(
      conversationId: conversationId,
      fileId: fileId,
    );
  });

  DocumentFile _mapFileDto(DocumentFileDto dto) {
    final status = switch (dto.status) {
      FileProcessingStatus.completed => DocumentFileStatus.completed,
      FileProcessingStatus.failed => DocumentFileStatus.failed,
      FileProcessingStatus.processing => DocumentFileStatus.processing,
    };

    return DocumentFile(
      id: dto.id,
      name: dto.name,
      status: status,
      sizeBytes: dto.sizeBytes,
      mime: dto.mime,
    );
  }
}
