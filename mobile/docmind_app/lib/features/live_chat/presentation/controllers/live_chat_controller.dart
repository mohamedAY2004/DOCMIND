import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../../domain/entities/chat_message.dart';
import '../../domain/entities/chat_session.dart';
import '../../domain/usecases/send_message_usecase.dart';
import '../../domain/usecases/get_conversation_messages_usecase.dart';
import '../../../subject_tutors/domain/entities/tutor_conversation.dart';
import '../../../subject_tutors/domain/usecases/get_tutor_conversations_usecase.dart';
import '../../../subject_tutors/domain/usecases/create_tutor_conversation_usecase.dart';

/// Owns one visible chat. Selection/disposal invalidate every pending continuation.
class LiveChatController extends GetxController {
  LiveChatController({
    required this.session,
    required SendMessageUseCase sendMessage,
    required GetConversationMessagesUseCase getMessages,
    required CreateTutorConversationUseCase createConversation,
    required GetTutorConversationsUseCase getHistory,
  }) : _sendMessage = sendMessage,
       _getMessages = getMessages,
       _createConversation = createConversation,
       _getHistory = getHistory;

  final ChatSession session;
  final SendMessageUseCase _sendMessage;
  final GetConversationMessagesUseCase _getMessages;
  final CreateTutorConversationUseCase _createConversation;
  final GetTutorConversationsUseCase _getHistory;
  final messages = <ChatMessage>[].obs;
  final isLoadingMessages = false.obs;
  final messagesError = RxnString();
  final hasOlderMessages = false.obs;
  int _messagesPage = 0;
  final isSending = false.obs;
  final sendError = RxnString();
  final lastFailedText = RxnString();
  final messageController = TextEditingController();
  final history = <TutorConversation>[].obs;
  final isHistoryLoading = false.obs;
  final historyError = RxnString();
  final historyPage = 1.obs;
  final historyPageSize = 20.obs;
  final historyHasMore = false.obs;
  int _selection = 0;
  bool _disposed = false;
  bool _owns(int selection) => !_disposed && selection == _selection;

  @override
  void onInit() {
    super.onInit();
    loadMessages();
  }

  @override
  void onClose() {
    _disposed = true;
    _selection++;
    messageController.dispose();
    super.onClose();
  }

  Future<void> loadMessages({bool older = false}) async {
    if (isLoadingMessages.value || (older && !hasOlderMessages.value)) return;
    if (session.sessionId.isEmpty) {
      messagesError.value = null;
      return;
    }
    final owner = _selection;
    isLoadingMessages.value = true;
    messagesError.value = null;
    final result = await _getMessages(
      conversationId: session.sessionId,
      sourceType: session.sourceType,
      page: older ? _messagesPage + 1 : 1,
      pageSize: 50,
    );
    if (!_owns(owner)) return;
    result.fold((failure) => messagesError.value = failure.message, (page) {
      if (older) {
        final ids = messages.map((message) => message.id).toSet();
        messages.insertAll(
          0,
          page.items.where((message) => !ids.contains(message.id)),
        );
      } else {
        messages.assignAll(page.items);
      }
      _messagesPage = page.page;
      hasOlderMessages.value = page.page < page.totalPages;
    });
    isLoadingMessages.value = false;
  }

  Future<void> sendMessage() async {
    final text = messageController.text.trim();
    if (text.isEmpty || isSending.value || isLoadingMessages.value) return;
    final owner = _selection;
    final localId = 'pending-${DateTime.now().microsecondsSinceEpoch}';
    final thinkingId = '$localId-reply';
    isSending.value = true;
    sendError.value = null;
    lastFailedText.value = null;
    messages.add(
      ChatMessage(
        id: localId,
        content: text,
        sender: MessageSender.user,
        timestamp: DateTime.now(),
        deliveryStatus: DeliveryStatus.sending,
      ),
    );
    messages.add(
      ChatMessage(
        id: thinkingId,
        content: '',
        sender: MessageSender.ai,
        timestamp: DateTime.now(),
        isThinking: true,
      ),
    );
    messageController.clear();

    void failed(String message) {
      messages.removeWhere((item) => item.id == thinkingId);
      final index = messages.indexWhere((item) => item.id == localId);
      if (index >= 0) {
        messages[index] = messages[index].withDelivery(DeliveryStatus.failed);
      }
      sendError.value = message;
      lastFailedText.value = text;
      // Preserve a draft, including when the server conversation could not be created.
      messageController.text = text;
      isSending.value = false;
    }

    if (session.sessionId.isEmpty &&
        session.sourceType == KnowledgeSourceType.subject) {
      final created = await _createConversation(
        subjectId: session.knowledgeSourceId,
      );
      if (!_owns(owner)) return;
      final ready = created.fold(
        (failure) {
          failed(failure.message);
          return false;
        },
        (conversation) {
          session.sessionId = conversation.id;
          return true;
        },
      );
      if (!ready) return;
    }
    final result = await _sendMessage(
      sessionId: session.sessionId,
      message: text,
      sourceType: session.sourceType,
    );
    if (!_owns(owner)) return;
    result.fold((failure) => failed(failure.message), (turn) {
      messages.removeWhere(
        (item) => item.id == localId || item.id == thinkingId,
      );
      messages.addAll([turn.userMessage, turn.reply]);
      if (turn.reply.interrupted) {
        sendError.value =
            'The response was interrupted. You can retry your question.';
        lastFailedText.value = text;
      }
    });
    isSending.value = false;
  }

  Future<void> retrySend() async {
    final text = lastFailedText.value;
    if (text == null || isSending.value) return;
    messages.removeWhere(
      (item) =>
          item.deliveryStatus == DeliveryStatus.failed && item.content == text,
    );
    messageController.text = text;
    await sendMessage();
  }

  Future<void> loadHistory({int page = 1, int pageSize = 20}) async {
    if (_disposed ||
        isHistoryLoading.value ||
        session.sourceType != KnowledgeSourceType.subject) {
      return;
    }
    isHistoryLoading.value = true;
    historyError.value = null;
    final result = await _getHistory(
      subjectId: session.knowledgeSourceId,
      page: page,
      pageSize: pageSize,
    );
    if (_disposed) return;
    result.fold((failure) => historyError.value = failure.message, (response) {
      if (page == 1) {
        history.assignAll(response.items);
      } else {
        final ids = history.map((item) => item.id).toSet();
        history.addAll(response.items.where((item) => !ids.contains(item.id)));
      }
      historyPage.value = response.page;
      historyPageSize.value = response.pageSize;
      historyHasMore.value = response.page < response.totalPages;
    });
    isHistoryLoading.value = false;
  }

  Future<void> loadMoreHistory() async {
    if (historyHasMore.value) {
      await loadHistory(
        page: historyPage.value + 1,
        pageSize: historyPageSize.value,
      );
    }
  }

  Future<void> refreshHistory() => loadHistory(pageSize: historyPageSize.value);

  Future<void> selectConversation(TutorConversation conversation) async {
    _selection++;
    session.sessionId = conversation.id;
    messages.clear();
    messageController.clear();
    _messagesPage = 0;
    hasOlderMessages.value = false;
    isLoadingMessages.value = false;
    isSending.value = false;
    sendError.value = null;
    lastFailedText.value = null;
    await loadMessages();
  }
}
