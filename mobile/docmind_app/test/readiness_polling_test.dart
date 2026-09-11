import 'dart:async';
import 'package:flutter_test/flutter_test.dart';
import 'package:fpdart/fpdart.dart';
import 'package:docmind_app/core/domain/failure.dart';
import 'package:docmind_app/features/chat_with_documents/domain/entities/document_chat_session.dart';
import 'package:docmind_app/features/chat_with_documents/domain/entities/document_file.dart';
import 'package:docmind_app/features/chat_with_documents/domain/repositories/document_chat_repository.dart';
import 'package:docmind_app/features/chat_with_documents/domain/usecases/create_document_conversation_usecase.dart';
import 'package:docmind_app/features/chat_with_documents/domain/usecases/get_conversations_usecase.dart';
import 'package:docmind_app/features/chat_with_documents/domain/usecases/delete_document_conversation_usecase.dart';
import 'package:docmind_app/features/chat_with_documents/domain/usecases/get_conversation_files_usecase.dart';
import 'package:docmind_app/features/chat_with_documents/domain/usecases/add_conversation_file_usecase.dart';
import 'package:docmind_app/features/chat_with_documents/domain/usecases/delete_conversation_file_usecase.dart';
import 'package:docmind_app/features/chat_with_documents/presentation/controllers/document_chat_controller.dart';

class FakeDocuments implements DocumentChatRepository {
  final requests = <Completer<Either<Failure, List<DocumentFile>>>>[];
  @override
  Future<Either<Failure, List<DocumentFile>>> getConversationFiles({
    required String conversationId,
  }) {
    final request = Completer<Either<Failure, List<DocumentFile>>>();
    requests.add(request);
    return request.future;
  }

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

DocumentFile file(String id, DocumentFileStatus status) =>
    DocumentFile(id: id, name: '$id.pdf', status: status);
DocumentChatController controller(FakeDocuments repo) =>
    DocumentChatController(
        createConversation: CreateDocumentConversationUseCase(repo),
        getConversations: GetConversationsUseCase(repo),
        deleteConversation: DeleteDocumentConversationUseCase(repo),
        getFiles: GetConversationFilesUseCase(repo),
        addFile: AddConversationFileUseCase(repo),
        deleteFile: DeleteConversationFileUseCase(repo),
        pollInterval: const Duration(milliseconds: 10),
      )
      ..currentConversationId.value = 'chat'
      ..session.value = const DocumentChatSession(
        sessionId: 'chat',
        fileName: 'a.pdf',
        trainingStatus: TrainingStatus.processing,
      );

void main() {
  testWidgets(
    'readiness waits for every file and allows only one status request in flight',
    (tester) async {
      final repo = FakeDocuments();
      final chat = controller(repo)..startPolling('chat');
      await tester.pump(const Duration(seconds: 1));
      expect(repo.requests, hasLength(1));
      repo.requests[0].complete(
        Right([
          file('a', DocumentFileStatus.completed),
          file('b', DocumentFileStatus.processing),
        ]),
      );
      await tester.pump();
      expect(chat.isReadyForChat, isFalse);
      await tester.pump(const Duration(milliseconds: 10));
      expect(repo.requests, hasLength(2));
      repo.requests[1].complete(
        Right([
          file('a', DocumentFileStatus.completed),
          file('b', DocumentFileStatus.completed),
        ]),
      );
      await tester.pump();
      expect(chat.isReadyForChat, isTrue);
      expect(chat.isPolling.value, isFalse);
      await tester.pump(const Duration(seconds: 1));
      expect(repo.requests, hasLength(2));
      chat.onClose();
    },
  );
  testWidgets(
    'failure stops polling and navigation/disposal reject late readiness',
    (tester) async {
      final repo = FakeDocuments();
      final chat = controller(repo)..startPolling('chat');
      repo.requests[0].complete(Right([file('a', DocumentFileStatus.failed)]));
      await tester.pump();
      expect(chat.session.value!.trainingStatus, TrainingStatus.failed);
      expect(chat.isPolling.value, isFalse);
      chat.startPolling('chat');
      chat.stopPolling();
      repo.requests[1].complete(
        Right([file('a', DocumentFileStatus.completed)]),
      );
      await tester.pump();
      expect(chat.isReadyForChat, isFalse);
      chat.startPolling('chat');
      chat.onClose();
      repo.requests[2].complete(
        Right([file('a', DocumentFileStatus.completed)]),
      );
      await tester.pump(const Duration(seconds: 1));
      expect(chat.isReadyForChat, isFalse);
      expect(repo.requests, hasLength(3));
    },
  );
  testWidgets('temporary network failure retries without reporting readiness', (
    tester,
  ) async {
    final repo = FakeDocuments();
    final chat = controller(repo)..startPolling('chat');
    repo.requests[0].complete(const Left(NetworkFailure('Offline')));
    await tester.pump();
    expect(chat.errorMessage.value, 'Offline');
    expect(chat.isReadyForChat, isFalse);
    await tester.pump(const Duration(milliseconds: 10));
    expect(repo.requests, hasLength(2));
    chat.onClose();
    repo.requests[1].complete(const Left(NetworkFailure('Offline')));
    await tester.pump();
  });
}
