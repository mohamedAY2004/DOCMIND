import 'package:flutter/material.dart';
import 'package:get/get.dart';

import '../theme/theme_service.dart';

/// Centralized app color constants for DocMind.
abstract final class AppColors {
  AppColors._();

    static bool get _isDark {
        if (Get.isRegistered<ThemeService>()) {
            return Get.find<ThemeService>().isDarkMode.value;
        }
        return Get.isDarkMode;
    }

  // ── Screen background gradient (theme-aware) ─────────────────────

  static Color get screenBackgroundGradientTop =>
      _isDark ? const Color(0xFF05161A) : const Color(0xFFF8FAFC);

  static Color get screenBackgroundGradientCenter =>
      _isDark ? const Color(0xFF05161A) : const Color(0xFFF8FAFC);

  static Color get screenBackgroundGradientBottom =>
      _isDark ? const Color(0xFF072E33) : const Color(0xFFE2E8F0);

  // ── Text colors (theme-aware) ────────────────────────────────────

  static Color get textOnSurface =>
      _isDark ? const Color(0xFFFFFFFF) : const Color(0xFF0F172A);

  static Color get textSecondary =>
      _isDark ? const Color(0xFFA0AEC0) : const Color(0xFF475569);

  // ── Surface colors (theme-aware) ─────────────────────────────────

  static Color get formCardBackground =>
      _isDark ? const Color(0xCC072E33) : const Color(0xFFFFFFFF);

  static Color get inputBackground =>
      _isDark ? const Color(0x80072E33) : const Color(0xFFF1F5F9);

  static Color get surfaceContainer =>
      _isDark ? const Color(0x80072E33) : const Color(0xFFF8FAFC);

  // ── Universal (static const) ─────────────────────────────────────

  // Primary & brand
  static const Color primary = Color(0xFF0F9197);
  static const Color primaryDark = Color(0xFF1D4ED8);
  static const Color primaryLight = Color(0xFF3B82F6);

  // Container
  static const Color containerBorder = Color(0xFF0F9197);

  // Splash (Figma: dark teal, glowing teal/cyan accent)
  static const Color splashBackgroundTop = Color(0xFF0A1619);
  static const Color splashBackgroundBottom = Color(0xFF0D2228);
  static const Color splashAccent = Color(0xFF00E5CC);
  static const Color splashAccentGlow = Color(0x4000E5CC);
  static const Color splashTitle = Color(0xFFFFFFFF);
  static const Color splashTagline = Color(0xFFFFFFFF);
  static const Color splashVersion = Color(0xFFB0BEC5);

  // Legacy backgrounds (for theme external use)
  static const Color scaffoldBackground = Color(0xFFFFFFFF);

  // Text (light theme screens)
  static const Color textPrimary = Color(0xFF0F172A);
  static const Color textTertiary = Color(0xFF94A3B8);

  // Form / Input (login screens)
  static const Color hintText = Color(0xFFA0AEC0);

  // Neutral
  static const Color white = Color(0xFFFFFFFF);
  static const Color black = Color(0xFF000000);
}
