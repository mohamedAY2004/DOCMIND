import 'package:flutter/material.dart';

import '../constants/app_colors.dart';

/// Centralized text styles for the app.
/// Splash uses dark-theme colors (light text on dark background).
abstract final class AppTextStyles {
  AppTextStyles._();

  static const TextStyle splashTitle = TextStyle(
    fontSize: 32,
    fontWeight: FontWeight.w700,
    color: AppColors.splashTitle,
    letterSpacing: -0.5,
  );

  static const TextStyle splashTagline = TextStyle(
    fontSize: 14,
    fontWeight: FontWeight.w400,
    color: AppColors.splashTagline,
  );

  static const TextStyle splashFeature = TextStyle(
    fontSize: 12,
    fontWeight: FontWeight.w500,
    color: AppColors.splashAccent,
  );

  static const TextStyle splashVersion = TextStyle(
    fontSize: 12,
    fontWeight: FontWeight.w400,
    color: AppColors.splashVersion,
  );
}
