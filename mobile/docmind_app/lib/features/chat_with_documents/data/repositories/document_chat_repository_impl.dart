import 'dart:io';

import '../../domain/entities/conversations_page.dart';
import '../../domain/entities/document_conversation.dart';
import '../../domain/entities/document_file.dart';
import '../../domain/entities/send_message_result.dart';
import '../../domain/errors/document_chat_failure.dart';
import '../../domain/repositories/document_chat_repository.dart';
import '../../../live_chat/domain/entities/chat_message.dart';
import '../../../live_chat/domain/repositories/live_chat_repository.dart';
import '../datasources/document_chat_remote_data_source.dart';
import '../models/document_file_dto.dart';

/// Implementation of DocumentChatRepository.
class DocumentChatRepositoryImpl implements DocumentChatRepository {
  DocumentChatRepositoryImpl({
    DocumentChatRemoteDataSource? remoteDataSource,
  }) : _remote = remoteDataSource ?? DocumentChatRemoteDataSource();

  final DocumentChatRemoteDataSource _remote;

  @override
  Future<DocumentChatCreateResult> createConversation(
    File file, {
    void Function(int sent, int total)? onProgress,
  }) async {
    final response = await _remote.createConversation(
      file,
      onProgress: onProgress,
    );

    return DocumentChatCreateResult(
      conversationId: response.conversation.id,
      title: response.conversation.title,
      files: response.files.map(_mapFileDto).toList(),
    );
  }

  @override
  Future<ConversationsPage> getConversations({
    int page = 1,
    int pageSize = 20,
  }) async {
    final response = await _remote.getConversations(
      page: page,
      pageSize: pageSize,
    );

    return ConversationsPage(
      items: response.items
          .map((dto) => DocumentConversation(
                id: dto.id,
                title: dto.title,
                subjectId: dto.subjectId,
                createdAt: dto.createdAt,
                updatedAt: dto.updatedAt,
                messageCount: dto.messageCount,
              ))
          .toList(),
      page: response.page,
      pageSize: response.pageSize,
      total: response.total,
      totalPages: response.totalPages,
    );
  }

  @override
  Future<ChatMessagesPage> getMessages(
    String conversationId, {
    int page = 1,
    int pageSize = 20,
  }) async {
    final response = await _remote.getMessages(
      conversationId: conversationId,
      page: page,
      pageSize: pageSize,
    );

    return ChatMessagesPage(
      items: response.items
          .map((dto) => ChatMessage(
                id: dto.id,
                content: dto.text,
                sender: dto.role == 'user'
                    ? MessageSender.user
                    : MessageSender.ai,
                timestamp: dto.createdAt,
              ))
          .toList(),
      page: response.page,
      pageSize: response.pageSize,
      total: response.total,
      totalPages: response.totalPages,
    );
  }

  @override
  Future<SendMessageResult> sendMessage({
    required String conversationId,
    required String message,
  }) async {
    final response = await _remote.sendMessage(
      conversationId: conversationId,
      message: message,
    );

    return SendMessageResult(
      userMessage: ChatMessage(
        id: response.userMessage.id,
        content: response.userMessage.text,
        sender: MessageSender.user,
        timestamp: response.userMessage.createdAt,
      ),
      aiReply: ChatMessage(
        id: response.reply.id,
        content: response.reply.text,
        sender: MessageSender.ai,
        timestamp: response.reply.createdAt,
      ),
    );
  }

  @override
  Future<void> deleteConversation(String conversationId) async {
    await _remote.deleteConversation(conversationId: conversationId);
  }


  @override
  Future<List<DocumentFile>> getConversationFiles({
    required String conversationId,
  }) async {
    final response = await _remote.getConversationFiles(
      conversationId: conversationId,
    );

    return response.map(_mapFileDto).toList();
  }

  @override
  Future<DocumentFile> addConversationFile({
    required String conversationId,
    required File file,
    void Function(int sent, int total)? onProgress,
  }) async {
    final response = await _remote.addConversationFile(
      conversationId: conversationId,
      file: file,
      onProgress: onProgress,
    );

    return _mapFileDto(response);
  }

  @override
  Future<void> deleteConversationFile({
    required String conversationId,
    required String fileId,
  }) async {
    await _remote.deleteConversationFile(
      conversationId: conversationId,
      fileId: fileId,
    );
  }

  @override
  Future<DocumentFile> getFileStatus(String conversationId) async {
    final files = await getConversationFiles(
      conversationId: conversationId,
    );
    if (files.isEmpty) {
      throw const DocumentChatFailure('No files found for this conversation.');
    }
    return files.first;
  }

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
