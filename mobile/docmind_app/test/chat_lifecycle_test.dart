import 'dart:async';
import 'package:flutter_test/flutter_test.dart';
import 'package:fpdart/fpdart.dart';
import 'package:docmind_app/core/domain/failure.dart';
import 'package:docmind_app/features/live_chat/domain/entities/chat_message.dart';
import 'package:docmind_app/features/live_chat/domain/entities/chat_messages_page.dart';
import 'package:docmind_app/features/live_chat/domain/entities/chat_session.dart';
import 'package:docmind_app/features/live_chat/domain/entities/chat_turn.dart';
import 'package:docmind_app/features/live_chat/domain/repositories/live_chat_repository.dart';
import 'package:docmind_app/features/live_chat/domain/usecases/send_message_usecase.dart';
import 'package:docmind_app/features/live_chat/domain/usecases/get_conversation_messages_usecase.dart';
import 'package:docmind_app/features/live_chat/presentation/controllers/live_chat_controller.dart';
import 'package:docmind_app/features/subject_tutors/domain/repositories/subjects_repository.dart';
import 'package:docmind_app/features/subject_tutors/domain/usecases/create_tutor_conversation_usecase.dart';
import 'package:docmind_app/features/subject_tutors/domain/usecases/get_tutor_conversations_usecase.dart';
import 'package:docmind_app/features/subject_tutors/domain/entities/tutor_conversation.dart';

class FakeSubjects implements SubjectsRepository {
  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

class FakeChat implements LiveChatRepository {
  int sends = 0;
  Future<Either<Failure, ChatTurn>> Function()? sending;
  Future<Either<Failure, ChatMessagesPage>> Function(String, int)? history;
  @override
  Future<Either<Failure, ChatTurn>> sendMessage({
    required String conversationId,
    required String message,
    required KnowledgeSourceType sourceType,
  }) {
    sends++;
    return sending!();
  }

  @override
  Future<Either<Failure, ChatMessagesPage>> getConversationMessages({
    required String conversationId,
    required KnowledgeSourceType sourceType,
    int page = 1,
    int pageSize = 50,
  }) => history!(conversationId, page);
}

ChatMessage message(String id, {bool user = false}) => ChatMessage(
  id: id,
  content: id,
  sender: user ? MessageSender.user : MessageSender.ai,
  timestamp: DateTime(2026),
);
ChatMessagesPage page(String id) => ChatMessagesPage(
  items: [message(id)],
  page: 1,
  pageSize: 50,
  total: 1,
  totalPages: 1,
);
LiveChatController controller(FakeChat repository) => LiveChatController(
  session: ChatSession(
    sessionId: 'first',
    knowledgeSourceId: 'subject',
    sourceType: KnowledgeSourceType.subject,
  ),
  sendMessage: SendMessageUseCase(repository),
  getMessages: GetConversationMessagesUseCase(repository),
  createConversation: CreateTutorConversationUseCase(FakeSubjects()),
  getHistory: GetTutorConversationsUseCase(FakeSubjects()),
);

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  test(
    'failed delivery preserves draft and retry replaces pending message',
    () async {
      final repository = FakeChat()
        ..sending = () async => const Left(NetworkFailure('Offline'));
      final chat = controller(repository);
      chat.messageController.text = 'Question';
      await chat.sendMessage();
      expect(chat.messageController.text, 'Question');
      expect(chat.messages.single.deliveryStatus, DeliveryStatus.failed);
      expect(chat.sendError.value, 'Offline');
      repository.sending = () async => Right(
        ChatTurn(
          userMessage: message('server-user', user: true),
          reply: message('reply'),
        ),
      );
      await chat.retrySend();
      expect(repository.sends, 2);
      expect(chat.messages.map((m) => m.id), ['server-user', 'reply']);
      expect(chat.messageController.text, isEmpty);
      chat.onClose();
    },
  );
  test(
    'switching conversation rejects delayed history and send completion',
    () async {
      final oldHistory = Completer<Either<Failure, ChatMessagesPage>>();
      final oldSend = Completer<Either<Failure, ChatTurn>>();
      final repository = FakeChat()
        ..history = ((id, _) => id == 'first'
            ? oldHistory.future
            : Future.value(Right(page('new-history'))))
        ..sending = () => oldSend.future;
      final chat = controller(repository);
      chat.messageController.text = 'Question';
      final sending = chat.sendMessage();
      final loading = chat.loadMessages();
      await chat.selectConversation(
        TutorConversation(
          id: 'second',
          title: '',
          subjectId: 'subject',
          createdAt: DateTime(2026),
          updatedAt: DateTime(2026),
          messageCount: 1,
        ),
      );
      oldHistory.complete(Right(page('stale-history')));
      oldSend.complete(
        Right(
          ChatTurn(
            userMessage: message('stale-user'),
            reply: message('stale-reply'),
          ),
        ),
      );
      await Future.wait([sending, loading]);
      expect(chat.messages.map((m) => m.id), ['new-history']);
      chat.onClose();
    },
  );
  test(
    'history failure is distinct from empty history and disposal invalidates requests',
    () async {
      final repository = FakeChat()
        ..history = (_, __) async =>
            const Left(NetworkFailure('History unavailable'));
      final chat = controller(repository);
      await chat.loadMessages();
      expect(chat.messagesError.value, 'History unavailable');
      final pending = Completer<Either<Failure, ChatMessagesPage>>();
      repository.history = (_, __) => pending.future;
      final loading = chat.loadMessages();
      chat.onClose();
      pending.complete(Right(page('late')));
      await loading;
      expect(chat.messages, isEmpty);
    },
  );
  test('send validation has no transport dependency', () async {
    final repository = FakeChat();
    final result = await SendMessageUseCase(repository)(
      sessionId: 'id',
      message: ' ',
      sourceType: KnowledgeSourceType.document,
    );
    expect(
      result.fold((failure) => failure, (_) => null),
      isA<ValidationFailure>(),
    );
    expect(repository.sends, 0);
  });
}
