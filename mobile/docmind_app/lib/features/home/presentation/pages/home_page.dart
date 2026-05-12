import 'package:flutter/material.dart';
import 'package:get/get.dart';

import '../../../../core/theme/theme_service.dart';

import '../../../../core/constants/app_assets.dart';
import '../../../../core/constants/app_colors.dart';
import '../controllers/home_controller.dart';
import '../widgets/home_option_card.dart';

/// Layout constants matching Figma.
const double _screenPaddingH = 16.0;
const double _screenPaddingTop = 24.0;
const double _headerGap = 12.0;
const double _cardsGap = 12.0;
const double _logoBoxSize = 40.0;
const double _logoBoxRadius = 16.0;
const double _welcomeFontSize = 16.0;
const double _nameFontSize = 14.0;
const double _subtitleFontSize = 14.0;

/// Home screen — displays a welcome header and a dynamic list of
/// feature cards driven entirely by the [HomeController].
class HomePage extends StatelessWidget {
  const HomePage({super.key});

  @override
  Widget build(BuildContext context) {
    final themeService = Get.find<ThemeService>();

    return Obx(() {
      // read reactive value so Obx rebuilds when theme changes
      final _ = themeService.isDarkMode.value;
      return GetBuilder<HomeController>(
        init: HomeController(),
        builder: (controller) {
          return Scaffold(
            body: Container(
              width: double.infinity,
              height: double.infinity,
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  colors: [
                    AppColors.screenBackgroundGradientTop,
                    AppColors.screenBackgroundGradientCenter,
                    AppColors.screenBackgroundGradientBottom,
                  ],
                  stops: [0.0, 0.5, 1.0],
                ),
              ),
              child: Stack(
                children: [
                  // ── Decorative blurred circles ──
                  _buildGlowCircle(
                    left: -73,
                    top: 146,
                    size: 267,
                    opacity: 0.05,
                  ),
                  _buildGlowCircle(
                    left: 76,
                    top: 660,
                    size: 291,
                    opacity: 0.05,
                  ),

                  // ── Main content ──
                  SafeArea(
                    child: SingleChildScrollView(
                      child: Padding(
                        padding: const EdgeInsets.symmetric(
                          horizontal: _screenPaddingH,
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const SizedBox(height: _screenPaddingTop),
                            _buildHeader(controller),
                            const SizedBox(height: _headerGap),
                            _buildSubtitle(),
                            const SizedBox(height: 24),
                            _buildOptionsList(controller),
                          ],
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          );
        },
      );
    });
  }

  // ── Decorative glow circles ──────────────────────────────────────

  Widget _buildGlowCircle({
    required double left,
    required double top,
    required double size,
    required double opacity,
  }) {
    return Positioned(
      left: left,
      top: top,
      child: Container(
        width: size,
        height: size,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: AppColors.primary.withValues(alpha: opacity),
        ),
      ),
    );
  }

  // ── Header ───────────────────────────────────────────────────────

  Widget _buildHeader(HomeController controller) {
    return Row(
      children: [
        // Logo box
        Container(
          width: _logoBoxSize,
          height: _logoBoxSize,
          decoration: BoxDecoration(
            color: AppColors.primary,
            borderRadius: BorderRadius.circular(_logoBoxRadius),
            boxShadow: [
              BoxShadow(
                color: AppColors.primary.withValues(alpha: 0.3),
                blurRadius: 15,
                offset: const Offset(0, 10),
              ),
              BoxShadow(
                color: AppColors.primary.withValues(alpha: 0.3),
                blurRadius: 6,
                offset: const Offset(0, 4),
              ),
            ],
          ),
          child: Center(
            child: Image.asset(
              AppAssets.docmindLogo,
              width: 30,
              height: 28,
              fit: BoxFit.contain,
              errorBuilder: (_, __, ___) => const Icon(
                Icons.auto_stories,
                color: AppColors.white,
                size: 22,
              ),
            ),
          ),
        ),
        const SizedBox(width: _headerGap),
        // Welcome text
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Welcome back!',
                style: TextStyle(
                  color: AppColors.textOnSurface,
                  fontSize: _welcomeFontSize,
                  fontWeight: FontWeight.w400,
                ),
              ),
              Obx(
                () => Text(
                  controller.userName.value,
                  style: TextStyle(
                    color: AppColors.textSecondary,
                    fontSize: _nameFontSize,
                    fontWeight: FontWeight.w400,
                  ),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  // ── Subtitle ─────────────────────────────────────────────────────

  Widget _buildSubtitle() {
    return Text(
      'What would you like to learn today?',
      style: TextStyle(
        color: AppColors.textSecondary,
        fontSize: _subtitleFontSize,
        fontWeight: FontWeight.w400,
      ),
    );
  }

  // ── Options list ─────────────────────────────────────────────────

  Widget _buildOptionsList(HomeController controller) {
    return Obx(
      () => Column(
        children: controller.options
            .map(
              (option) => Padding(
                padding: const EdgeInsets.only(bottom: _cardsGap),
                child: HomeOptionCard(
                  option: option,
                  onTap: () => controller.onOptionTapped(option.type),
                ),
              ),
            )
            .toList(),
      ),
    );
  }
}
