import 'package:get/get.dart';

import '../../../../core/routes/app_routes.dart';
import '../../../../core/theme/theme_service.dart';
import '../../../auth/data/repositories/auth_repository_impl.dart';
import '../../../auth/domain/usecases/get_saved_session_usecase.dart';
import '../../../auth/domain/usecases/logout_usecase.dart';

/// Manages Profile & Settings screen state.
///
/// Holds reactive toggle states and user info.
/// TODO(backend): Replace static user data with real auth user object.
class ProfileController extends GetxController {
  final ThemeService _themeService = Get.find();

  // ── User info (fake — replace with real auth user) ───────────────
  final userName = 'User'.obs;
  final userEmail = ''.obs;
  final userPlan = 'Student'.obs;
  final joinedDate = ''.obs;

  // ── Settings toggles ─────────────────────────────────────────────
  RxBool get isDarkMode => _themeService.isDarkMode;
  final isNotificationsEnabled = true.obs;

  @override
  void onInit() {
    super.onInit();
    _loadProfile();
  }

  Future<void> _loadProfile() async {
    final useCase = GetSavedSessionUseCase(AuthRepositoryImpl());
    final session = await useCase();
    if (session != null) {
      userName.value = session.user.name.isNotEmpty
          ? session.user.name
          : session.user.username;
      userEmail.value = session.user.username;
      userPlan.value = session.user.role.isNotEmpty
          ? session.user.role
          : 'Student';
    }
  }

  // ── Actions ──────────────────────────────────────────────────────

  void toggleDarkMode(bool value) => _themeService.setDarkMode(value);

  void toggleNotifications(bool value) => isNotificationsEnabled.value = value;

  void onPrivacyTapped() {
    // TODO(nav): Navigate to Privacy screen when implemented.
  }

  void onHelpTapped() {
    // TODO(nav): Navigate to Help & Support screen when implemented.
  }

  void signOut() {
    final useCase = LogoutUseCase(AuthRepositoryImpl());
    useCase().whenComplete(() => Get.offAllNamed(AppRoutes.signIn));
  }
}
