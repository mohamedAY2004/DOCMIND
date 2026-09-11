import 'package:get/get.dart';

import '../../../../core/routes/app_routes.dart';
import '../../../../core/theme/theme_service.dart';
import '../../../auth/domain/usecases/get_saved_session_usecase.dart';
import '../../../auth/domain/usecases/logout_usecase.dart';

/// Manages Profile & Settings screen state.
///
/// Holds reactive toggle states and user info.
class ProfileController extends GetxController {
  ProfileController(this._themeService, this._getSession, this._logout);
  final ThemeService _themeService;
  final GetSavedSessionUseCase _getSession;
  final LogoutUseCase _logout;

  // User info from the saved authenticated session.
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
    final result = await _getSession();
    if (isClosed) return;
    final session = result.fold((failure) {
      Get.snackbar('Profile', failure.message);
      return null;
    }, (session) => session);
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

  Future<void> signOut() async {
    final result = await _logout();
    if (isClosed) return;
    result.fold(
      (failure) => Get.snackbar('Sign out', failure.message),
      (_) => Get.offAllNamed(AppRoutes.signIn),
    );
  }
}
