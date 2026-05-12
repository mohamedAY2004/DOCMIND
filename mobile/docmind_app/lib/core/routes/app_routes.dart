import 'package:get/get.dart';

import '../../features/auth/presentation/pages/sign_in_page.dart';
import '../../features/chat_with_documents/presentation/pages/document_chat_entry_page.dart';
import '../../features/chat_with_documents/presentation/pages/document_file_selection_page.dart';
import '../../features/chat_with_documents/presentation/pages/document_training_progress_page.dart';
import '../../features/live_chat/presentation/pages/live_chat_page.dart';
import '../../features/subject_tutors/presentation/pages/subject_tutors_page.dart';
import '../../features/profile/presentation/pages/profile_page.dart';
import '../../features/home/presentation/pages/home_page.dart';

/// App route names.
abstract final class AppRoutes {
  AppRoutes._();

  // ── Auth ──
  static const String signIn = '/sign-in';

  // ── Home ──
  static const String home = '/home';

  // ── Chat with Documents ──
  static const String chatWithDocuments = '/chat-with-documents';
  static const String documentFileSelection = '/document-file-selection';
  static const String documentTrainingProgress = '/document-training-progress';
  static const String documentLiveChat = '/document-live-chat';

  // ── Live Chat (shared) ──
  static const String liveChat = '/live-chat';

  // ── Other features ──
  static const String subjectTutors = '/subject-tutors';
  static const String profile = '/profile';
}

/// App pages for GetX routing.
abstract final class AppPages {
  AppPages._();

  static final List<GetPage<dynamic>> pages = [
    // Auth
    GetPage(name: AppRoutes.signIn, page: () => const SignInPage()),

    // Home
    GetPage(name: AppRoutes.home, page: () => const HomePage()),

    // Chat with Documents
    GetPage(
      name: AppRoutes.chatWithDocuments,
      page: () => const DocumentChatEntryPage(),
    ),
    GetPage(
      name: AppRoutes.documentFileSelection,
      page: () => const DocumentFileSelectionPage(),
    ),
    GetPage(
      name: AppRoutes.documentTrainingProgress,
      page: () => const DocumentTrainingProgressPage(),
    ),
    GetPage(
      name: AppRoutes.documentLiveChat,
      page: () => const LiveChatPage(),
    ),
    GetPage(
      name: AppRoutes.liveChat,
      page: () => const LiveChatPage(),
    ),

    // Other features (placeholders)
    GetPage(
      name: AppRoutes.subjectTutors,
      page: () => const SubjectTutorsPage(),
    ),
    GetPage(
      name: AppRoutes.profile,
      page: () => const ProfilePage(),
    ),
  ];
}

