import 'package:get/get.dart';

import '../../../../core/routes/app_routes.dart';
import '../../../live_chat/domain/entities/chat_session.dart';
import '../../domain/entities/subject.dart';
// conversation creation is handled lazily by the chat controller now
import '../../domain/usecases/get_subjects_usecase.dart';

/// Manages the Subject Tutors screen state.
///
/// Loads subjects on init and navigates to [LiveChatPage] when a subject is tapped.
class SubjectTutorsController extends GetxController {
  // ── Dependencies ────────────────────────────────────────────────
  SubjectTutorsController(this._getSubjects);
  final GetSubjectsUseCase _getSubjects;

  // ── State ───────────────────────────────────────────────────────
  final subjects = <Subject>[].obs;
  final isLoading = true.obs;
  final isCreating = false.obs;
  final errorMessage = RxnString();

  // ── Lifecycle ───────────────────────────────────────────────────

  @override
  void onInit() {
    super.onInit();
    _loadSubjects();
  }

  // ── Actions ─────────────────────────────────────────────────────

  Future<void> _loadSubjects() async {
    isLoading.value = true;
    errorMessage.value = null;
    final result = await _getSubjects();
    if (isClosed) return;
    result.fold(
      (failure) => errorMessage.value = failure.message,
      subjects.assignAll,
    );
    isLoading.value = false;
  }

  Future<void> selectSubject(Subject subject) async {
    // Navigate to the live chat UI but do NOT create a server conversation yet.
    // The conversation will be created lazily when the user sends the first message.
    errorMessage.value = null;
    Get.toNamed(
      AppRoutes.liveChat,
      arguments: ChatSession(
        sessionId: '', // empty => no remote conversation yet
        knowledgeSourceId: subject.id,
        sourceType: KnowledgeSourceType.subject,
        displayName: subject.name,
      ),
    );
  }

  void onHistoryTapped() {
    Get.snackbar('Coming soon', 'Previous subject chats will appear here.');
  }
}
