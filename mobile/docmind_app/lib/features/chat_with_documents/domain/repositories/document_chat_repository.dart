import 'dart:io';

import '../entities/conversations_page.dart';
import '../entities/document_file.dart';
import '../entities/send_message_result.dart';
import '../../../live_chat/domain/repositories/live_chat_repository.dart';

/// Repository interface for document chat operations.
abstract class DocumentChatRepository {
  /// Creates a new document conversation by uploading a file.
  Future<DocumentChatCreateResult> createConversation(
    File file, {
    void Function(int sent, int total)? onProgress,
  });

  /// Lists all document conversations.
  Future<ConversationsPage> getConversations({
    int page = 1,
    int pageSize = 20,
  });

  /// Gets messages for a specific conversation.
  Future<ChatMessagesPage> getMessages(
    String conversationId, {
    int page = 1,
    int pageSize = 20,
  });

  /// Sends a message and returns the user message + AI reply.
  Future<SendMessageResult> sendMessage({
    required String conversationId,
    required String message,
  });

  /// Deletes a conversation.
  Future<void> deleteConversation(String conversationId);


  /// Lists files for a conversation.
  Future<List<DocumentFile>> getConversationFiles({
    required String conversationId,
  });

  /// Adds a file to a conversation.
  Future<DocumentFile> addConversationFile({
    required String conversationId,
    required File file,
    void Function(int sent, int total)? onProgress,
  });

  /// Deletes a file from a conversation.
  Future<void> deleteConversationFile({
    required String conversationId,
    required String fileId,
  });

  /// Gets the file status for a conversation (for polling).
  Future<DocumentFile> getFileStatus(String conversationId);
}

/// Result of creating a document conversation.
class DocumentChatCreateResult {
  const DocumentChatCreateResult({
    required this.conversationId,
    required this.title,
    required this.files,
  });

  final String conversationId;
  final String title;
  final List<DocumentFile> files;
}
