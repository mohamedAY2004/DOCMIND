import 'package:flutter/material.dart';
import 'package:get/get.dart';

import '../../../../core/routes/app_routes.dart';
import '../../data/repositories/auth_repository_impl.dart';
import '../../domain/errors/auth_failure.dart';
import '../../domain/usecases/login_usecase.dart';

/// Controller for the Regular User Sign In screen.
///
/// Holds form state, validates inputs, and orchestrates navigation
/// after a successful authentication attempt.
class SignInController extends GetxController {
  // ── Form controllers ────────────────────────────────────────────
  final usernameController = TextEditingController();
  final passwordController = TextEditingController();
  final formKey = GlobalKey<FormState>();

  // ── Observable state ────────────────────────────────────────────
  final isLoading = false.obs;
  final errorMessage = RxnString();
  final obscurePassword = true.obs;

  // ── Actions ─────────────────────────────────────────────────────

  /// Toggles password visibility.
  void togglePasswordVisibility() {
    obscurePassword.value = !obscurePassword.value;
  }

  /// Validates inputs and performs the login flow.
  ///
  /// On success, navigates to the home screen.
  Future<void> login() async {
    errorMessage.value = null;

    // Validate form fields
    if (!(formKey.currentState?.validate() ?? false)) {
      return;
    }

    isLoading.value = true;

    try {
      final useCase = LoginUseCase(AuthRepositoryImpl());
      final session = await useCase(
        username: usernameController.text.trim(),
        password: passwordController.text,
      );

      if (session.welcomeMessage != null) {
        Get.snackbar('Welcome', session.welcomeMessage!);
      }

      Get.offAllNamed(AppRoutes.home);
    } on AuthFailure catch (e) {
      errorMessage.value = e.message;
    } catch (_) {
      errorMessage.value = 'An unexpected error occurred';
    } finally {
      isLoading.value = false;
    }
  }

  // ── Lifecycle ───────────────────────────────────────────────────

  @override
  void onClose() {
    usernameController.dispose();
    passwordController.dispose();
    super.onClose();
  }
}
