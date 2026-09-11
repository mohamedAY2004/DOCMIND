import 'dart:async';
import 'dart:io';
import 'package:file_picker/file_picker.dart';
import 'package:get/get.dart';
import '../../../../core/domain/failure.dart';
import '../../../../core/routes/app_routes.dart';
import '../../../live_chat/domain/entities/chat_session.dart';
import '../../domain/entities/document_chat_session.dart';
import '../../domain/entities/document_conversation.dart';
import '../../domain/entities/document_file.dart';
import '../../domain/usecases/add_conversation_file_usecase.dart';
import '../../domain/usecases/create_document_conversation_usecase.dart';
import '../../domain/usecases/delete_document_conversation_usecase.dart';
import '../../domain/usecases/delete_conversation_file_usecase.dart';
import '../../domain/usecases/get_conversation_files_usecase.dart';
import '../../domain/usecases/get_conversations_usecase.dart';

/// Owns uploads, attachments and readiness. LiveChatController owns messages.
class DocumentChatController extends GetxController {
  DocumentChatController({
    required CreateDocumentConversationUseCase createConversation,
    required GetConversationsUseCase getConversations,
    required DeleteDocumentConversationUseCase deleteConversation,
    required GetConversationFilesUseCase getFiles,
    required AddConversationFileUseCase addFile,
    required DeleteConversationFileUseCase deleteFile,
    this.pollInterval = const Duration(seconds: 3),
  }) : _createConversation = createConversation,
       _getConversations = getConversations,
       _deleteConversation = deleteConversation,
       _getFiles = getFiles,
       _addFile = addFile,
       _deleteFile = deleteFile;

  final CreateDocumentConversationUseCase _createConversation;
  final GetConversationsUseCase _getConversations;
  final DeleteDocumentConversationUseCase _deleteConversation;
  final GetConversationFilesUseCase _getFiles;
  final AddConversationFileUseCase _addFile;
  final DeleteConversationFileUseCase _deleteFile;
  final Duration pollInterval;
  final conversations = <DocumentConversation>[].obs;
  final isLoadingConversations = false.obs;
  final conversationsPage = 1.obs;
  final hasMoreConversations = true.obs;
  final conversationsError = RxnString();
  final session = Rxn<DocumentChatSession>();
  final selectedFile = Rxn<File>();
  final uploadProgress = 0.0.obs;
  final isLoading = false.obs;
  final errorMessage = RxnString();
  final currentConversationId = RxnString();
  final conversationFiles = <DocumentFile>[].obs;
  final isLoadingFiles = false.obs;
  final filesError = RxnString();
  final isUploadingFile = false.obs;
  final isPolling = false.obs;
  bool get isReadyForChat => session.value?.isReadyForChat ?? false;
  Timer? _pollingTimer;
  bool _statusRequestInFlight = false;
  bool _disposed = false;
  int _pollVersion = 0;
  int _sessionVersion = 0;
  int _filesRequest = 0;
  String? _filesConversationId;

  @override
  void onInit() {
    super.onInit();
    loadConversations();
  }

  @override
  void onClose() {
    _disposed = true;
    _sessionVersion++;
    stopPolling();
    super.onClose();
  }

  void navigateToFileSelection() {
    stopPolling();
    Get.toNamed(AppRoutes.documentFileSelection);
  }

  void navigateToTrainingProgress() {
    Get.toNamed(AppRoutes.documentTrainingProgress);
  }

  void navigateToLiveChat() {
    final id = currentConversationId.value;
    if (id == null || !isReadyForChat) return;
    stopPolling();
    Get.toNamed(
      AppRoutes.liveChat,
      arguments: ChatSession(
        sessionId: id,
        knowledgeSourceId: id,
        sourceType: KnowledgeSourceType.document,
        displayName: session.value?.fileName,
      ),
    );
  }

  void navigateToLiveChatForConversation(DocumentConversation conversation) {
    resetSession();
    currentConversationId.value = conversation.id;
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

  Future<void> loadConversations({bool refresh = false}) async {
    if (_disposed ||
        isLoadingConversations.value ||
        (!refresh && !hasMoreConversations.value)) {
      return;
    }
    isLoadingConversations.value = true;
    conversationsError.value = null;
    final result = await _getConversations(
      page: refresh ? 1 : conversationsPage.value,
      pageSize: 20,
    );
    if (_disposed) return;
    result.fold((failure) => conversationsError.value = failure.message, (
      page,
    ) {
      if (refresh) {
        conversations.assignAll(page.items);
      } else {
        final ids = conversations.map((item) => item.id).toSet();
        conversations.addAll(
          page.items.where((item) => !ids.contains(item.id)),
        );
      }
      hasMoreConversations.value = page.hasNextPage;
      conversationsPage.value = page.page + 1;
    });
    isLoadingConversations.value = false;
  }

  Future<void> deleteConversation(String id) async {
    final result = await _deleteConversation(id);
    if (_disposed) return;
    result.fold((failure) => Get.snackbar('Error', failure.message), (_) {
      conversations.removeWhere((item) => item.id == id);
      if (currentConversationId.value == id) resetSession();
    });
  }

  Future<void> loadConversationFiles(String id) async {
    _filesConversationId = id;
    final request = ++_filesRequest;
    isLoadingFiles.value = true;
    filesError.value = null;
    final result = await _getFiles(conversationId: id);
    if (_disposed || request != _filesRequest) return;
    result.fold(
      (failure) => filesError.value = failure.message,
      conversationFiles.assignAll,
    );
    isLoadingFiles.value = false;
  }

  Future<void> addSelectedFileToConversation(String id) async {
    final file = selectedFile.value;
    if (file == null || isUploadingFile.value) return;
    isUploadingFile.value = true;
    filesError.value = null;
    final result = await _addFile(conversationId: id, file: file);
    if (_disposed) return;
    if (_filesConversationId == id) {
      result.fold((failure) => filesError.value = failure.message, (uploaded) {
        _filesRequest++;
        conversationFiles.removeWhere((item) => item.id == uploaded.id);
        conversationFiles.add(uploaded);
        selectedFile.value = null;
      });
    }
    isUploadingFile.value = false;
  }

  Future<void> deleteConversationFile({
    required String conversationId,
    required String fileId,
  }) async {
    final result = await _deleteFile(
      conversationId: conversationId,
      fileId: fileId,
    );
    if (_disposed || _filesConversationId != conversationId) return;
    result.fold((failure) => filesError.value = failure.message, (_) {
      _filesRequest++;
      conversationFiles.removeWhere((item) => item.id == fileId);
    });
  }

  Future<void> pickFile() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['pdf'],
    );
    if (!_disposed && result?.files.single.path != null) {
      selectedFile.value = File(result!.files.single.path!);
    }
  }

  Future<void> startSession() async {
    final file = selectedFile.value;
    if (file == null || isLoading.value) return;
    final owner = ++_sessionVersion;
    stopPolling();
    isLoading.value = true;
    uploadProgress.value = 0;
    errorMessage.value = null;
    final result = await _createConversation(
      file,
      onProgress: (sent, total) {
        if (!_disposed && owner == _sessionVersion && total > 0) {
          uploadProgress.value = (sent / total).clamp(0.0, 1.0);
        }
      },
    );
    if (_disposed || owner != _sessionVersion) return;
    result.fold((failure) => errorMessage.value = failure.message, (created) {
      currentConversationId.value = created.conversationId;
      session.value = DocumentChatSession(
        sessionId: created.conversationId,
        fileName: created.title,
        uploadProgress: 1,
        trainingStatus: created.hasFailed
            ? TrainingStatus.failed
            : created.isReady
            ? TrainingStatus.completed
            : TrainingStatus.processing,
      );
      conversationFiles.assignAll(created.files);
      loadConversations(refresh: true);
      navigateToTrainingProgress();
      if (!created.isReady && !created.hasFailed) {
        startPolling(created.conversationId);
      }
    });
    isLoading.value = false;
  }

  void stopPolling() {
    _pollVersion++;
    _pollingTimer?.cancel();
    _pollingTimer = null;
    isPolling.value = false;
  }

  void startPolling(String conversationId) {
    stopPolling();
    if (_disposed) return;
    isPolling.value = true;
    _pollOnce(conversationId, _pollVersion);
  }

  bool _ownsPoll(int version) =>
      !_disposed && version == _pollVersion && isPolling.value;
  void _schedulePoll(String id, int version) {
    if (_ownsPoll(version)) {
      _pollingTimer = Timer(pollInterval, () => _pollOnce(id, version));
    }
  }

  Future<void> _pollOnce(String id, int version) async {
    if (!_ownsPoll(version)) return;
    if (_statusRequestInFlight) {
      _schedulePoll(id, version);
      return;
    }
    _statusRequestInFlight = true;
    final result = await _getFiles(conversationId: id);
    _statusRequestInFlight = false;
    if (!_ownsPoll(version)) return;
    result.fold(
      (failure) {
        errorMessage.value = failure.message;
        if (failure is! NetworkFailure) stopPolling();
      },
      (files) {
        conversationFiles.assignAll(files);
        errorMessage.value = null;
        final failed =
            files.isEmpty ||
            files.any((file) => file.status == DocumentFileStatus.failed);
        final ready =
            files.isNotEmpty &&
            files.every((file) => file.status == DocumentFileStatus.completed);
        session.value = session.value?.copyWith(
          trainingStatus: failed
              ? TrainingStatus.failed
              : ready
              ? TrainingStatus.completed
              : TrainingStatus.processing,
        );
        if (failed || ready) stopPolling();
      },
    );
    _schedulePoll(id, version);
  }

  Future<void> checkTraining() async {
    final id = currentConversationId.value;
    if (id != null && !isPolling.value) startPolling(id);
  }

  void resetSession() {
    _sessionVersion++;
    _filesRequest++;
    stopPolling();
    session.value = null;
    currentConversationId.value = null;
    _filesConversationId = null;
    selectedFile.value = null;
    conversationFiles.clear();
    uploadProgress.value = 0;
    isLoading.value = false;
    errorMessage.value = null;
  }
}
