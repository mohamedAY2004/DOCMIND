import 'package:dio/dio.dart';
import 'package:get/get.dart';
import '../network/dio_client.dart';
import '../theme/theme_service.dart';
import '../../features/auth/domain/repositories/auth_repository.dart';
import '../../features/auth/data/repositories/auth_repository_impl.dart';
import '../../features/auth/data/datasources/auth_remote_data_source.dart';
import '../../features/subject_tutors/domain/repositories/subjects_repository.dart';
import '../../features/subject_tutors/data/repositories/subjects_repository_impl.dart';
import '../../features/subject_tutors/data/datasources/subjects_remote_data_source.dart';
import '../../features/chat_with_documents/domain/repositories/document_chat_repository.dart';
import '../../features/chat_with_documents/data/repositories/document_chat_repository_impl.dart';
import '../../features/chat_with_documents/data/datasources/document_chat_remote_data_source.dart';
import '../../features/live_chat/domain/repositories/live_chat_repository.dart';
import '../../features/live_chat/data/repositories/live_chat_repository_impl.dart';
import '../../features/live_chat/data/datasources/live_chat_remote_data_source.dart';
import '../../features/auth/data/datasources/auth_local_data_source.dart';
import '../../features/live_chat/domain/entities/chat_session.dart';
import '../../features/auth/presentation/controllers/sign_in_controller.dart';
import '../../features/home/presentation/controllers/home_controller.dart';
import '../../features/profile/presentation/controllers/profile_controller.dart';
import '../../features/subject_tutors/presentation/controllers/subject_tutors_controller.dart';
import '../../features/chat_with_documents/presentation/controllers/document_chat_controller.dart';
import '../../features/live_chat/presentation/controllers/live_chat_controller.dart';
import '../../features/auth/domain/usecases/login_usecase.dart';
import '../../features/auth/domain/usecases/logout_usecase.dart';
import '../../features/auth/domain/usecases/get_saved_session_usecase.dart';
import '../../features/subject_tutors/domain/usecases/get_subjects_usecase.dart';
import '../../features/subject_tutors/domain/usecases/get_tutor_conversations_usecase.dart';
import '../../features/subject_tutors/domain/usecases/create_tutor_conversation_usecase.dart';
import '../../features/chat_with_documents/domain/usecases/create_document_conversation_usecase.dart';
import '../../features/chat_with_documents/domain/usecases/get_conversations_usecase.dart';
import '../../features/chat_with_documents/domain/usecases/delete_document_conversation_usecase.dart';
import '../../features/chat_with_documents/domain/usecases/get_conversation_files_usecase.dart';
import '../../features/chat_with_documents/domain/usecases/add_conversation_file_usecase.dart';
import '../../features/chat_with_documents/domain/usecases/delete_conversation_file_usecase.dart';
import '../../features/live_chat/domain/usecases/send_message_usecase.dart';
import '../../features/live_chat/domain/usecases/get_conversation_messages_usecase.dart';
import '../../features/home/domain/usecases/get_home_options_usecase.dart';

/// The only place that constructs repositories, transports and controllers.
class AppBinding extends Bindings {
  @override
  void dependencies() {
    if (Get.isRegistered<Dio>()) return;
    final local = Get.put(AuthLocalDataSource(), permanent: true);
    final dio = Get.put(
      DioClient.create(tokenProvider: local.getToken),
      permanent: true,
    );
    Get.put<AuthRepository>(
      AuthRepositoryImpl(AuthRemoteDataSource(dio), local),
      permanent: true,
    );
    Get.put<SubjectsRepository>(
      SubjectsRepositoryImpl(SubjectsRemoteDataSource(dio)),
      permanent: true,
    );
    Get.put<DocumentChatRepository>(
      DocumentChatRepositoryImpl(DocumentChatRemoteDataSource(dio)),
      permanent: true,
    );
    Get.put<LiveChatRepository>(
      LiveChatRepositoryImpl(LiveChatRemoteDataSource(dio)),
      permanent: true,
    );
    Get.put(LoginUseCase(Get.find<AuthRepository>()), permanent: true);
    Get.put(LogoutUseCase(Get.find<AuthRepository>()), permanent: true);
    Get.put(
      GetSavedSessionUseCase(Get.find<AuthRepository>()),
      permanent: true,
    );
    Get.put(
      GetSubjectsUseCase(Get.find<SubjectsRepository>()),
      permanent: true,
    );
    Get.put(
      GetTutorConversationsUseCase(Get.find<SubjectsRepository>()),
      permanent: true,
    );
    Get.put(
      CreateTutorConversationUseCase(Get.find<SubjectsRepository>()),
      permanent: true,
    );
    Get.put(
      CreateDocumentConversationUseCase(Get.find<DocumentChatRepository>()),
      permanent: true,
    );
    Get.put(
      GetConversationsUseCase(Get.find<DocumentChatRepository>()),
      permanent: true,
    );
    Get.put(
      DeleteDocumentConversationUseCase(Get.find<DocumentChatRepository>()),
      permanent: true,
    );
    Get.put(
      GetConversationFilesUseCase(Get.find<DocumentChatRepository>()),
      permanent: true,
    );
    Get.put(
      AddConversationFileUseCase(Get.find<DocumentChatRepository>()),
      permanent: true,
    );
    Get.put(
      DeleteConversationFileUseCase(Get.find<DocumentChatRepository>()),
      permanent: true,
    );
    Get.put(
      SendMessageUseCase(Get.find<LiveChatRepository>()),
      permanent: true,
    );
    Get.put(
      GetConversationMessagesUseCase(Get.find<LiveChatRepository>()),
      permanent: true,
    );
    Get.put(GetHomeOptionsUseCase(), permanent: true);
  }
}

class SignInBinding extends Bindings {
  @override
  void dependencies() => Get.lazyPut(() => SignInController(Get.find()));
}

class HomeBinding extends Bindings {
  @override
  void dependencies() =>
      Get.lazyPut(() => HomeController(Get.find(), Get.find()));
}

class ProfileBinding extends Bindings {
  @override
  void dependencies() => Get.lazyPut(
    () => ProfileController(Get.find<ThemeService>(), Get.find(), Get.find()),
  );
}

class SubjectTutorsBinding extends Bindings {
  @override
  void dependencies() => Get.lazyPut(() => SubjectTutorsController(Get.find()));
}

class DocumentBinding extends Bindings {
  @override
  void dependencies() {
    if (Get.isRegistered<DocumentChatController>()) return;
    Get.lazyPut(
      () => DocumentChatController(
        createConversation: Get.find(),
        getConversations: Get.find(),
        deleteConversation: Get.find(),
        getFiles: Get.find(),
        addFile: Get.find(),
        deleteFile: Get.find(),
      ),
    );
  }
}

class LiveChatBinding extends Bindings {
  @override
  void dependencies() {
    DocumentBinding().dependencies();
    Get.lazyPut(
      () => LiveChatController(
        session: sessionFromArguments(Get.arguments),
        sendMessage: Get.find(),
        getMessages: Get.find(),
        createConversation: Get.find(),
        getHistory: Get.find(),
      ),
    );
  }
}

ChatSession sessionFromArguments(dynamic args) {
  if (args is ChatSession) return args;
  final map = args is Map ? args : const {};
  return ChatSession(
    sessionId: map['sessionId'] as String? ?? '',
    knowledgeSourceId: map['knowledgeSourceId'] as String? ?? '',
    sourceType: map['sourceType'] == 'subject'
        ? KnowledgeSourceType.subject
        : KnowledgeSourceType.document,
    displayName: map['fileName'] as String?,
  );
}
