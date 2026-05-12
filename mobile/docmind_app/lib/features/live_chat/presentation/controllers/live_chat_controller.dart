import 'package:flutter/material.dart';
import 'package:get/get.dart';

import '../../domain/entities/chat_message.dart';
import '../../domain/entities/chat_session.dart';
import '../../domain/usecases/send_message_usecase.dart';
import '../../domain/usecases/get_conversation_messages_usecase.dart';
import '../../../subject_tutors/data/repositories/subjects_repository_impl.dart';
import '../../../subject_tutors/domain/entities/tutor_conversation.dart';
import '../../../subject_tutors/domain/errors/tutor_conversation_failure.dart';
import '../../../subject_tutors/domain/usecases/get_tutor_conversations_usecase.dart';
import '../../../subject_tutors/domain/usecases/create_tutor_conversation_usecase.dart';
import '../../data/repositories/live_chat_repository_impl.dart';

/// Controls the live chat session state and delegates to [SendMessageUseCase].
///
/// Receives a [ChatSession] via [Get.arguments]. Works for any source type
/// (document, subject tutor, etc.) because all chat logic lives here.
class LiveChatController extends GetxController {
  // ── Dependencies ────────────────────────────────────────────────
  final _sendMessageUseCase = SendMessageUseCase();
  late final GetConversationMessagesUseCase _getConversationMessages;
  final isLoadingMessages = true.obs;
  late final CreateTutorConversationUseCase _createConversation;

  // ── State ───────────────────────────────────────────────────────
  final messages = <ChatMessage>[].obs;
  final isSending = false.obs;
  final messageController = TextEditingController();
  final history = <TutorConversation>[].obs;
  final isHistoryLoading = false.obs;
  final historyError = RxnString();
  final historyPage = 1.obs;
  final historyPageSize = 20.obs;
  final historyHasMore = false.obs;

  late final ChatSession session;
  late final GetTutorConversationsUseCase _getHistory;

  // ── Lifecycle ───────────────────────────────────────────────────

  @override
  void onInit() {
    super.onInit();
    _initializeSession();
    _getHistory = GetTutorConversationsUseCase(SubjectsRepositoryImpl());
    _createConversation = CreateTutorConversationUseCase(SubjectsRepositoryImpl());
    _getConversationMessages = GetConversationMessagesUseCase(
      LiveChatRepositoryImpl(),
    );
    _loadConversationMessages();
  }

  @override
  void onClose() {
    messageController.dispose();
    super.onClose();
  }

  // ── Helpers ─────────────────────────────────────────────────────

  void _initializeSession() {
    final args = Get.arguments;

    if (args is ChatSession) {
      session = args;
      return;
    }

    // Fallback: accept legacy Map arguments for backward compatibility.
    final map = args as Map<String, dynamic>? ?? {};
    session = ChatSession(
      sessionId: map['sessionId'] as String? ?? 'default-session',
      knowledgeSourceId: map['knowledgeSourceId'] as String? ?? 'unknown',
      sourceType: KnowledgeSourceType.document,
      displayName: map['fileName'] as String?,
    );
  }

  Future<void> _loadConversationMessages() async {
    isLoadingMessages.value = true;

    // If there's no remote conversation id (new chat), skip loading.
    if (session.sessionId.trim().isEmpty) {
      isLoadingMessages.value = false;
      return;
    }
    try {
      final previousMessages = await _getConversationMessages(
        conversationId: session.sessionId,
        sourceType: session.sourceType,
        page: 1,
        pageSize: 100,
      );
      // Ensure messages are in chronological order (oldest first -> newest last).
      messages.addAll(previousMessages);
    } catch (_) {
      // Silently fail on load — user can still send messages.
    } finally {
      isLoadingMessages.value = false;
    }
  }

  // ── Actions ─────────────────────────────────────────────────────

  Future<void> sendMessage() async {
    final text = messageController.text.trim();
    if (text.isEmpty || isSending.value) return;

    // Optimistic UI: add user message immediately.
    final userMessageId = DateTime.now().millisecondsSinceEpoch.toString();
    messages.add(ChatMessage(
      id: userMessageId,
      content: text,
      sender: MessageSender.user,
      timestamp: DateTime.now(),
    ));
    messageController.clear();

    isSending.value = true;
    // Create a single thinking message with animated dots.
    final thinkingId = 'ai-thinking-${DateTime.now().millisecondsSinceEpoch}';
    messages.add(ChatMessage(
      id: thinkingId,
      content: '',
      sender: MessageSender.ai,
      timestamp: DateTime.now(),
      isThinking: true,
    ));

    try {
      // If this session hasn't been created on the server yet, create it now.
      if (session.sourceType == KnowledgeSourceType.subject &&
          session.sessionId.trim().isEmpty) {
        try {
          final conv = await _createConversation(
            subjectId: session.knowledgeSourceId,
          );
          session.sessionId = conv.id;
        } catch (e) {
          // Failed to create conversation: remove optimistic messages and abort.
          messages.removeWhere((m) => m.id == thinkingId);
          messages.removeWhere((m) => m.id == userMessageId);
          rethrow;
        }
      }
      final aiMessage = await _sendMessageUseCase(
        sessionId: session.sessionId,
        message: text,
        sourceType: session.sourceType,
      );

      // Find and replace the thinking message with the actual streamed response.
      final thinkingIndex = messages.indexWhere((m) => m.id == thinkingId);
      if (thinkingIndex != -1) {
        // Stream the response by progressively updating the thinking message.
        final fullText = aiMessage.content;
        const chunkSize = 3; // characters per update
        for (var i = 1; i <= fullText.length; i += chunkSize) {
          final end = (i + chunkSize - 1) < fullText.length
              ? i + chunkSize - 1
              : fullText.length;
          final partial = fullText.substring(0, end);
          messages[thinkingIndex] = ChatMessage(
            id: aiMessage.id,
            content: partial,
            sender: MessageSender.ai,
            timestamp: aiMessage.timestamp,
            isThinking: false,
          );
          await Future.delayed(const Duration(milliseconds: 25));
        }
        // Ensure final content exactly matches.
        messages[thinkingIndex] = ChatMessage(
          id: aiMessage.id,
          content: fullText,
          sender: MessageSender.ai,
          timestamp: aiMessage.timestamp,
          isThinking: false,
        );
      } else {
        // Fallback: just add the final message if thinking message was removed.
        messages.add(aiMessage);
      }
    } catch (_) {
      // On error, remove the thinking message and show nothing.
      messages.removeWhere((m) => m.id == thinkingId);
    } finally {
      isSending.value = false;
    }
  }

  Future<void> loadHistory({int page = 1, int pageSize = 20}) async {
    historyError.value = null;

    if (session.sourceType != KnowledgeSourceType.subject) {
      historyError.value = 'History is only available for tutor chats.';
      return;
    }

    // Do not clear existing history when requesting page 1 —
    // we prefer to merge/append so the UI doesn't refresh the whole list.

    isHistoryLoading.value = true;
    try {
      final pageResult = await _getHistory(
        subjectId: session.knowledgeSourceId,
        page: page,
        pageSize: pageSize,
      );

      // Merge incoming page items into the existing `history` list without
      // replacing the already-loaded pages. This prevents the UI from
      // refreshing the entire list and preserves scroll position.
      final incoming = pageResult.items;
      final existingIds = history.map((h) => h.id).toSet();

      if (page == 1) {
        if (history.isEmpty) {
          // First load for this session: populate the history.
          history.addAll(incoming);
        } else {
          // Avoid replacing already-loaded first page; only append new unique
          // items that don't exist yet.
          for (final it in incoming) {
            if (!existingIds.contains(it.id)) {
              history.add(it);
            }
          }
        }
      } else {
        // Subsequent pages: append only items not already present.
        for (final it in incoming) {
          if (!existingIds.contains(it.id)) {
            history.add(it);
          }
        }
      }

      historyPage.value = page;
      historyPageSize.value = pageSize;
      historyHasMore.value = page < pageResult.totalPages;
    } on TutorConversationFailure catch (e) {
      historyError.value = e.message;
    } catch (_) {
      historyError.value = 'Failed to load history.';
    } finally {
      isHistoryLoading.value = false;
    }
  }

  Future<void> loadMoreHistory() async {
    if (isHistoryLoading.value || !historyHasMore.value) return;
    final nextPage = historyPage.value + 1;
    await loadHistory(page: nextPage, pageSize: historyPageSize.value);
  }

  Future<void> refreshHistory() async {
    await loadHistory(page: 1, pageSize: historyPageSize.value);
  }

  /// Switch to a different conversation from the history.
  /// Updates the session ID, clears current messages, and loads the new conversation's messages.
  Future<void> selectConversation(TutorConversation conversation) async {
    // Update the session with the selected conversation ID
    session.sessionId = conversation.id;

    // Clear current messages
    messages.clear();

    // Load messages from the new conversation
    await _loadConversationMessages();
  }
}
