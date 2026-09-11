import 'package:fpdart/fpdart.dart';
import '../../../../core/domain/failure.dart';
import '../entities/document_upload_result.dart';
import 'dart:io';

import '../entities/conversations_page.dart';
import '../entities/document_file.dart';

/// Repository interface for document chat operations.
abstract class DocumentChatRepository {
  /// Creates a new document conversation by uploading a file.
  Future<Either<Failure, DocumentChatCreateResult>> createConversation(
    File file, {
    void Function(int sent, int total)? onProgress,
  });

  /// Lists all document conversations.
  Future<Either<Failure, ConversationsPage>> getConversations({
    int page = 1,
    int pageSize = 20,
  });

  /// Deletes a conversation.
  Future<Either<Failure, void>> deleteConversation(String conversationId);

  /// Lists files for a conversation.
  Future<Either<Failure, List<DocumentFile>>> getConversationFiles({
    required String conversationId,
  });

  /// Adds a file to a conversation.
  Future<Either<Failure, DocumentFile>> addConversationFile({
    required String conversationId,
    required File file,
    void Function(int sent, int total)? onProgress,
  });

  /// Deletes a file from a conversation.
  Future<Either<Failure, void>> deleteConversationFile({
    required String conversationId,
    required String fileId,
  });
}
