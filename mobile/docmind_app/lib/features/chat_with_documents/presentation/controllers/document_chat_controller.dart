import 'dart:async';
import 'dart:io';

import 'package:file_picker/file_picker.dart';
import 'package:get/get.dart';

import '../../../../core/routes/app_routes.dart';
import '../../../live_chat/domain/entities/chat_message.dart';
import '../../../live_chat/domain/entities/chat_session.dart';
import '../../domain/entities/document_chat_session.dart';
import '../../domain/entities/document_conversation.dart';
import '../../domain/entities/document_file.dart';
import '../../domain/errors/document_chat_failure.dart';
import '../../domain/usecases/add_conversation_file_usecase.dart';
import '../../domain/usecases/create_document_conversation_usecase.dart';
import '../../domain/usecases/delete_document_conversation_usecase.dart';
import '../../domain/usecases/delete_conversation_file_usecase.dart';
import '../../domain/usecases/get_conversation_files_usecase.dart';
import '../../domain/usecases/get_conversations_usecase.dart';
import '../../domain/usecases/get_document_messages_usecase.dart';
import '../../domain/usecases/send_document_message_usecase.dart';
import '../../data/repositories/document_chat_repository_impl.dart';

/// Manages the Chat-with-Documents workflow lifecycle.
///
/// Holds session state, chat messages, and orchestrates navigation.
/// UI talks only to this controller; it delegates to use cases.
class DocumentChatController extends GetxController {
  // ── Dependencies ────────────────────────────────────────────────
  late final CreateDocumentConversationUseCase _createConversation;
  late final GetConversationsUseCase _getConversations;
  late final GetDocumentMessagesUseCase _getMessages;
  late final SendDocumentMessageUseCase _sendMessage;
  late final DeleteDocumentConversationUseCase _deleteConversation;
  late final GetConversationFilesUseCase _getConversationFiles;
  late final AddConversationFileUseCase _addConversationFile;
  late final DeleteConversationFileUseCase _deleteConversationFile;

  DocumentChatController() {
    final repo = DocumentChatRepositoryImpl();
    _createConversation = CreateDocumentConversationUseCase(repo);
    _getConversations = GetConversationsUseCase(repo);
    _getMessages = GetDocumentMessagesUseCase(repo);
    _sendMessage = SendDocumentMessageUseCase(repo);
    _deleteConversation = DeleteDocumentConversationUseCase(repo);
    _getConversationFiles = GetConversationFilesUseCase(repo);
    _addConversationFile = AddConversationFileUseCase(repo);
    _deleteConversationFile = DeleteConversationFileUseCase(repo);
  }

  // ── State ───────────────────────────────────────────────────────
  
  // Conversation list state
  final conversations = <DocumentConversation>[].obs;
  final isLoadingConversations = false.obs;
  final conversationsPage = 1.obs;
  final hasMoreConversations = true.obs;
  final conversationsError = RxnString();

  // Session state (for new conversation flow)
  final session = Rxn<DocumentChatSession>();
  final selectedFile = Rxn<File>();
  final uploadProgress = 0.0.obs;
  final messages = <ChatMessage>[].obs;
  final isLoading = false.obs;
  final errorMessage = RxnString();

  // Current conversation ID for messaging
  final currentConversationId = RxnString();

  // Conversation files state
  final conversationFiles = <DocumentFile>[].obs;
  final isLoadingFiles = false.obs;
  final filesError = RxnString();
  final isUploadingFile = false.obs;

  // Polling state
  Timer? _pollingTimer;
  final isPolling = false.obs;

  /// Reactive readiness flag — true when session training is completed.
  RxBool get isReadyForChat =>
      (session.value?.isReadyForChat ?? false).obs;

  // ── Lifecycle ────────────────────────────────────────────────────

  @override
  void onInit() {
    super.onInit();
    loadConversations();
  }

  @override
  void onClose() {
    _pollingTimer?.cancel();
    super.onClose();
  }

  // ── Navigation ──────────────────────────────────────────────────

  void navigateToFileSelection() {
    Get.toNamed(AppRoutes.documentFileSelection);
  }

  void navigateToTrainingProgress() {
    Get.toNamed(AppRoutes.documentTrainingProgress);
  }

  void navigateToLiveChat() {
    final convId = currentConversationId.value ?? session.value?.sessionId;
    if (convId == null) return;

    Get.toNamed(
      AppRoutes.liveChat,
      arguments: ChatSession(
        sessionId: convId,
        knowledgeSourceId: convId,
        sourceType: KnowledgeSourceType.document,
        displayName: session.value?.fileName,
      ),
    );
  }

  void navigateToLiveChatForConversation(DocumentConversation conversation) {
    currentConversationId.value = conversation.id;
    session.value = DocumentChatSession(
      sessionId: conversation.id,
      fileName: conversation.title,
      trainingStatus: TrainingStatus.completed,
    );
    Get.toNamed(
      AppRoutes.liveChat,
      arguments: ChatSession(
        sessionId: conversation.id,
        knowledgeSourceId: conversation.id,
        sourceType: KnowledgeSourceType.document,
        displayName: conversation.title,
      ),
    );
  }

  // ── Conversation List Actions ───────────────────────────────────

  /// Loads the list of conversations.
  Future<void> loadConversations({bool refresh = false}) async {
    if (isLoadingConversations.value) return;

    if (refresh) {
      conversationsPage.value = 1;
      hasMoreConversations.value = true;
      conversations.clear();
    }

    if (!hasMoreConversations.value) return;

    isLoadingConversations.value = true;
    conversationsError.value = null;

    try {
      final page = await _getConversations(
        page: conversationsPage.value,
        pageSize: 20,
      );

      conversations.addAll(page.items);
      hasMoreConversations.value = page.hasNextPage;
      conversationsPage.value++;
    } on DocumentChatFailure catch (e) {
      conversationsError.value = e.message;
    } catch (e) {
      conversationsError.value = 'Failed to load conversations';
    } finally {
      isLoadingConversations.value = false;
    }
  }

  /// Deletes a conversation.
  Future<void> deleteConversation(String conversationId) async {
    try {
      await _deleteConversation(conversationId);
      conversations.removeWhere((c) => c.id == conversationId);
      Get.snackbar('Success', 'Conversation deleted');
    } on DocumentChatFailure catch (e) {
      Get.snackbar('Error', e.message);
    } catch (e) {
      Get.snackbar('Error', 'Failed to delete conversation');
    }
  }


  // ── Conversation Files Actions ─────────────────────────────────

  Future<void> loadConversationFiles(String conversationId) async {
    if (isLoadingFiles.value) return;

    isLoadingFiles.value = true;
    filesError.value = null;

    try {
      final files = await _getConversationFiles(
        conversationId: conversationId,
      );
      conversationFiles.value = files;
    } on DocumentChatFailure catch (e) {
      filesError.value = e.message;
    } catch (e) {
      filesError.value = 'Failed to load files';
    } finally {
      isLoadingFiles.value = false;
    }
  }

  Future<void> addSelectedFileToConversation(String conversationId) async {
    final file = selectedFile.value;
    if (file == null || isUploadingFile.value) return;

    isUploadingFile.value = true;
    filesError.value = null;

    try {
      final uploaded = await _addConversationFile(
        conversationId: conversationId,
        file: file,
      );
      conversationFiles.add(uploaded);
      selectedFile.value = null;
      Get.snackbar('Success', 'File added');
    } on DocumentChatFailure catch (e) {
      filesError.value = e.message;
      Get.snackbar('Error', e.message);
    } catch (e) {
      filesError.value = 'Failed to add file';
      Get.snackbar('Error', 'Failed to add file');
    } finally {
      isUploadingFile.value = false;
    }
  }

  Future<void> deleteConversationFile({
    required String conversationId,
    required String fileId,
  }) async {
    try {
      await _deleteConversationFile(
        conversationId: conversationId,
        fileId: fileId,
      );
      conversationFiles.removeWhere((f) => f.id == fileId);
      Get.snackbar('Success', 'File removed');
    } on DocumentChatFailure catch (e) {
      Get.snackbar('Error', e.message);
    } catch (e) {
      Get.snackbar('Error', 'Failed to delete file');
    }
  }

  // ── File Upload Actions ──────────────────────────────────────────

  Future<void> pickFile() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['pdf', 'docx', 'txt', 'pptx', 'ppt'],
    );
    if (result != null && result.files.single.path != null) {
      selectedFile.value = File(result.files.single.path!);
    }
  }

  Future<void> startSession() async {
    final file = selectedFile.value;
    if (file == null) return;

    isLoading.value = true;
    uploadProgress.value = 0.0;
    errorMessage.value = null;

    try {
      final result = await _createConversation(
        file,
        onProgress: (sent, total) {
          uploadProgress.value = sent / total;
        },
      );

      currentConversationId.value = result.conversationId;

      session.value = DocumentChatSession(
        sessionId: result.conversationId,
        fileName: result.title,
        uploadProgress: 1.0,
        trainingStatus: result.isReady
            ? TrainingStatus.completed
            : result.hasFailed
                ? TrainingStatus.failed
                : TrainingStatus.processing,
      );

      conversationFiles.value = result.files;

      // Refresh conversation list
      loadConversations(refresh: true);

      navigateToTrainingProgress();

      // If still processing, start polling
      if (result.isProcessing) {
        _startPolling(result.conversationId);
      }
    } on DocumentChatFailure catch (e) {
      errorMessage.value = e.message;
    } catch (e) {
      errorMessage.value = 'Failed to upload document';
    } finally {
      isLoading.value = false;
    }
  }

  // ── Polling Actions ──────────────────────────────────────────────

  void _startPolling(String conversationId) {
    _pollingTimer?.cancel();
    isPolling.value = true;

    _pollingTimer = Timer.periodic(
      const Duration(seconds: 3),
      (timer) async {
        await _checkFileStatus(conversationId);
      },
    );
  }

  Future<void> _checkFileStatus(String conversationId) async {
    try {
      // Since we don't have a dedicated file status endpoint,
      // we'll check by trying to fetch messages
      // If it succeeds, the file is processed
      await _getMessages(conversationId, pageSize: 1);
      
      // If we can fetch messages, processing is complete
      _pollingTimer?.cancel();
      isPolling.value = false;
      
      session.value = session.value?.copyWith(
        trainingStatus: TrainingStatus.completed,
      );
    } on DocumentChatFailure catch (e) {
      // If we get a specific error about processing, continue polling
      if (e.message.contains('processing') || e.message.contains('not ready')) {
        return;
      }
      
      // For other errors, stop polling and mark as failed
      _pollingTimer?.cancel();
      isPolling.value = false;
      session.value = session.value?.copyWith(
        trainingStatus: TrainingStatus.failed,
      );
    }
  }

  Future<void> checkTraining() async {
    final convId = currentConversationId.value ?? session.value?.sessionId;
    if (convId == null) return;

    await _checkFileStatus(convId);
  }

  // ── Messaging Actions ─────────────────────────────────────────────

  Future<void> sendMessage(String text) async {
    final convId = currentConversationId.value ?? session.value?.sessionId;
    if (convId == null) return;

    final currentSession = session.value;
    if (currentSession == null || !currentSession.isReadyForChat) return;

    final userMsg = ChatMessage(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      content: text,
      sender: MessageSender.user,
      timestamp: DateTime.now(),
    );
    messages.add(userMsg);

    isLoading.value = true;
    try {
      final result = await _sendMessage(
        conversationId: convId,
        message: text,
      );
      messages.add(result.aiReply);
    } on DocumentChatFailure catch (e) {
      errorMessage.value = e.message;
      // Remove the user message if sending failed
      messages.remove(userMsg);
    } catch (e) {
      errorMessage.value = 'Failed to send message';
      messages.remove(userMsg);
    } finally {
      isLoading.value = false;
    }
  }

  /// Loads messages for a specific conversation.
  Future<void> loadMessagesForConversation(String conversationId) async {
    isLoading.value = true;
    errorMessage.value = null;

    try {
      final page = await _getMessages(conversationId);
      messages.value = page.items;
      currentConversationId.value = conversationId;
    } on DocumentChatFailure catch (e) {
      errorMessage.value = e.message;
    } catch (e) {
      errorMessage.value = 'Failed to load messages';
    } finally {
      isLoading.value = false;
    }
  }

  // ── Session Management ───────────────────────────────────────────

  void resetSession() {
    _pollingTimer?.cancel();
    isPolling.value = false;
    session.value = null;
    currentConversationId.value = null;
    selectedFile.value = null;
    uploadProgress.value = 0.0;
    messages.clear();
    errorMessage.value = null;
  }
}
