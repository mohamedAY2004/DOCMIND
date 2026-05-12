import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:get/get.dart';

import '../../../../core/constants/app_assets.dart';
import '../../../../core/constants/app_colors.dart';
import '../controllers/sign_in_controller.dart';
import '../widgets/auth_button.dart';
import '../widgets/auth_text_field.dart';

/// Layout constants matching Figma.
const double _horizontalPadding = 24.0;
const double _logoTopPadding = 60.0;
const double _logoToHeadingGap = 12.0;
const double _headingToCardGap = 20.0;
const double _cardBorderRadius = 24.0;
const double _cardBorderWidth = 1.275;
const double _cardPaddingH = 33.0;
const double _cardPaddingTop = 33.0;
const double _fieldSpacing = 16.0;
const double _logoBoxSize = 80.0;
const double _logoIconContainerRadius = 24.0;
const double _logoBubbleSize = 24.0;
const double _footerFontSize = 14.0;
const double _headingFontSize = 16.0;
const double _labelIconSize = 16.0;

/// Regular User Sign In page.
///
/// Matches the Figma design.
class SignInPage extends StatelessWidget {
  const SignInPage({super.key});

  @override
  Widget build(BuildContext context) {
    return GetBuilder<SignInController>(
      init: SignInController(),
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
                _buildGlowCircle(left: 27, top: 67, size: 154, opacity: 0.15),
                _buildGlowCircle(left: 177, top: 596, size: 192, opacity: 0.10),

                // ── Main content ──
                SafeArea(
                  child: SingleChildScrollView(
                    padding: const EdgeInsets.symmetric(
                      horizontal: _horizontalPadding,
                    ),
                    child: Column(
                      children: [
                        const SizedBox(height: _logoTopPadding),
                        _buildLogoSection(),
                        const SizedBox(height: _headingToCardGap),
                        _buildFormCard(controller, context),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
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

  // ── Logo + heading section ───────────────────────────────────────

  Widget _buildLogoSection() {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        // Logo icon container
        SizedBox(
          width: _logoBoxSize,
          height: _logoBoxSize,
          child: Stack(
            clipBehavior: Clip.none,
            children: [
              Container(
                width: _logoBoxSize,
                height: _logoBoxSize,
                decoration: BoxDecoration(
                  color: AppColors.primary,
                  borderRadius: BorderRadius.circular(_logoIconContainerRadius),
                  boxShadow: [
                    BoxShadow(
                      color: AppColors.primary.withValues(alpha: 0.5),
                      blurRadius: 50,
                      spreadRadius: 0,
                      offset: const Offset(0, 25),
                    ),
                  ],
                ),
                child: Center(
                  child: Image.asset(
                    AppAssets.docmindLogo,
                    width: 60,
                    height: 54,
                    fit: BoxFit.contain,
                    errorBuilder: (_, __, ___) => const Icon(
                      Icons.auto_stories,
                      color: AppColors.white,
                      size: 40,
                    ),
                  ),
                ),
              ),
              // Small decorative circle
              Positioned(
                right: -4,
                top: -4,
                child: Container(
                  width: _logoBubbleSize,
                  height: _logoBubbleSize,
                  decoration: const BoxDecoration(
                    color: AppColors.primary,
                    shape: BoxShape.circle,
                  ),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: _logoToHeadingGap),
        // "DocMind" text
        const Text(
          'DocMind',
          style: TextStyle(
            color: AppColors.primary,
            fontSize: _headingFontSize,
            fontWeight: FontWeight.w400,
          ),
        ),
        const SizedBox(height: 24),
        // Tagline
        Text(
          'Three clicks away from knowledge!',
          style: TextStyle(
            color: AppColors.textOnSurface,
            fontSize: _headingFontSize,
            fontWeight: FontWeight.w700,
          ),
          textAlign: TextAlign.center,
        ),
      ],
    );
  }

  // ── Form Card ────────────────────────────────────────────────────

  Widget _buildFormCard(SignInController controller, BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.only(
        left: _cardPaddingH,
        right: _cardPaddingH,
        top: _cardPaddingTop,
        bottom: 1.275,
      ),
      decoration: BoxDecoration(
        color: AppColors.formCardBackground,
        borderRadius: BorderRadius.circular(_cardBorderRadius),
        border: Border.all(
          color: AppColors.primary.withValues(alpha: 0.2),
          width: _cardBorderWidth,
        ),
        boxShadow: [
          BoxShadow(
            color: AppColors.black.withValues(alpha: 0.25),
            blurRadius: 50,
            offset: const Offset(0, 25),
          ),
        ],
      ),
      child: Form(
        key: controller.formKey,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // ── Username field ──
            AuthTextField(
              controller: controller.usernameController,
              hintText: 'Enter your username',
              labelText: 'Username',
              labelIcon: SvgPicture.asset(
                AppAssets.userIdIcon,
                width: _labelIconSize,
                height: _labelIconSize,
                colorFilter: ColorFilter.mode(
                  Theme.of(context).colorScheme.onSurface,
                  BlendMode.srcIn,
                ),
              ),
              suffixIcon: SvgPicture.asset(
                AppAssets.userIdIcon,
                colorFilter: ColorFilter.mode(
                  AppColors.white.withValues(alpha: 0.6),
                  BlendMode.srcIn,
                ),
              ),
              keyboardType: TextInputType.text,
              validator: (value) {
                if (value == null || value.trim().isEmpty) {
                  return 'Username is required';
                }
                return null;
              },
            ),
            const SizedBox(height: _fieldSpacing),

            // ── Password field ──
            Obx(
              () => AuthTextField(
                controller: controller.passwordController,
                hintText: 'Enter your password',
                labelText: 'Password',
                obscureText: controller.obscurePassword.value,
                labelIcon: SvgPicture.asset(
                  AppAssets.lockIcon,
                  width: _labelIconSize,
                  height: _labelIconSize,
                  colorFilter: ColorFilter.mode(
                    Theme.of(context).colorScheme.onSurface,
                    BlendMode.srcIn,
                  ),
                ),
                suffixIcon: GestureDetector(
                  onTap: controller.togglePasswordVisibility,
                  child: SvgPicture.asset(
                    AppAssets.lockIcon,
                    colorFilter: ColorFilter.mode(
                      Theme.of(
                        context,
                      ).colorScheme.onSurface.withValues(alpha: 0.6),
                      BlendMode.srcIn,
                    ),
                  ),
                ),
                validator: (value) {
                  if (value == null || value.isEmpty) {
                    return 'Password is required';
                  }
                  return null;
                },
              ),
            ),
            const SizedBox(height: _fieldSpacing),

            // ── Error message ──
            Obx(() {
              final error = controller.errorMessage.value;
              if (error == null) return const SizedBox.shrink();
              return Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: Text(
                  error,
                  style: const TextStyle(color: Colors.redAccent, fontSize: 13),
                ),
              );
            }),

            // ── Sign In button ──
            Obx(
              () => AuthButton(
                label: 'Sign In',
                icon: AppAssets.starIcon,
                isLoading: controller.isLoading.value,
                onPressed: controller.login,
              ),
            ),
            // ── Footer ──
            const SizedBox(height: 24),
            Text(
              'Powered by Advanced DocMind',
              style: TextStyle(
                color: AppColors.textSecondary,
                fontSize: _footerFontSize,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }
}
