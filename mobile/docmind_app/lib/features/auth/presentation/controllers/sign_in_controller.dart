import 'package:flutter/material.dart';
import 'package:get/get.dart';

import '../../../../core/routes/app_routes.dart';
import '../../domain/usecases/login_usecase.dart';

/// Controller for the Regular User Sign In screen.
///
/// Holds form state, validates inputs, and orchestrates navigation
/// after a successful authentication attempt.
class SignInController extends GetxController {
  SignInController(this._login);
  final LoginUseCase _login;
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

    final result = await _login(
      username: usernameController.text.trim(),
      password: passwordController.text,
    );
    if (isClosed) return;
    isLoading.value = false;
    result.fold((failure) => errorMessage.value = failure.message, (session) {
      if (session.welcomeMessage != null) {
        Get.snackbar('Welcome', session.welcomeMessage!);
      }
      Get.offAllNamed(AppRoutes.home);
    });
  }

  // ── Lifecycle ───────────────────────────────────────────────────

  @override
  void onClose() {
    usernameController.dispose();
    passwordController.dispose();
    super.onClose();
  }
}
