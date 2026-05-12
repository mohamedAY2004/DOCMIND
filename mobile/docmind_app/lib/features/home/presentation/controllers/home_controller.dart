import 'package:get/get.dart';

import '../../../../core/routes/app_routes.dart';
import '../../../auth/data/repositories/auth_repository_impl.dart';
import '../../../auth/domain/usecases/get_saved_session_usecase.dart';
import '../../domain/entities/home_option.dart';
import '../../domain/usecases/get_home_options_usecase.dart';

/// Controller for the Home screen.
///
/// Loads the home options and exposes them to the UI.
/// and exposes the resulting option list for the UI.
class HomeController extends GetxController {
  // ── Dependencies ────────────────────────────────────────────────
  final GetHomeOptionsUseCase _getHomeOptions = GetHomeOptionsUseCase();

  // ── State ───────────────────────────────────────────────────────
  final options = <HomeOption>[].obs;
  final userName = 'User'.obs;

  // ── Lifecycle ───────────────────────────────────────────────────

  @override
  void onInit() {
    super.onInit();
    _loadOptions();
    _loadUser();
  }

  void _loadOptions() {
    options.value = _getHomeOptions();
  }

  Future<void> _loadUser() async {
    final useCase = GetSavedSessionUseCase(AuthRepositoryImpl());
    final session = await useCase();
    if (session != null) {
      userName.value = session.user.name.isNotEmpty
          ? session.user.name
          : session.user.username;
    }
  }

  // ── Navigation ──────────────────────────────────────────────────

  /// Maps each [HomeOptionType] to a named route.
  ///
  /// Navigation logic lives here so the UI remains type-agnostic.
  void onOptionTapped(HomeOptionType type) {
    switch (type) {
      case HomeOptionType.chatWithDocuments:
        Get.toNamed(AppRoutes.chatWithDocuments);
      case HomeOptionType.subjectTutors:
        Get.toNamed(AppRoutes.subjectTutors);
      case HomeOptionType.profile:
        Get.toNamed(AppRoutes.profile);
    }
  }
}
