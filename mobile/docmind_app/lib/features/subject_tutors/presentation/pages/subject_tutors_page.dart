import 'package:flutter/material.dart';
import 'package:get/get.dart';

import '../../../../core/constants/app_colors.dart';
import '../../domain/entities/subject.dart';
import '../controllers/subject_tutors_controller.dart';

/// Layout constants matching Figma node 22:922.
const double _appBarHeight = 65.0;
const double _appBarPaddingH = 12.0;
const double _appBarPaddingTop = 12.0;
const double _backButtonSize = 36.0;
const double _appBarIconBoxSize = 40.0;
const double _appBarIconBoxRadius = 16.0;
const double _appBarIconSize = 20.0;
const double _contentPaddingH = 16.0;
const double _contentPaddingTop = 16.0;
const double _cardHeight = 74.0;
const double _cardRadius = 16.0;
const double _cardSpacing = 8.0;
const double _subjectIconSize = 52.0;
const double _subjectIconRadius = 16.0;
const double _subjectIconInnerSize = 26.0;
const double _infoBannerRadius = 16.0;
const double _infoBannerIconBoxSize = 32.0;
const double _infoBannerIconBoxRadius = 16.0;
const double _infoBannerIconSize = 16.0;

/// AI Subject Tutors page.
///
/// Lists the student's subjects for the semester. Tapping a subject
/// navigates to the shared [LiveChatPage] with [KnowledgeSourceType.subject].
class SubjectTutorsPage extends StatelessWidget {
  const SubjectTutorsPage({super.key});

  @override
  Widget build(BuildContext context) {
    return GetBuilder<SubjectTutorsController>(
      init: SubjectTutorsController(),
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
                // Decorative purple glow blob (Figma 22:926)
                Positioned(
                  top: 120,
                  left: 40,
                  right: 20,
                  child: Container(
                    height: 280,
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(9999),
                      color: const Color(0xFFAD46FF).withValues(alpha: 0.05),
                    ),
                  ),
                ),
                Column(
                  children: [
                    _buildAppBar(context, controller),
                    Expanded(
                      child: _buildBody(controller),
                    ),
                  ],
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  // ── App Bar (Figma 22:927) ───────────────────────────────────────

  Widget _buildAppBar(
    BuildContext context,
    SubjectTutorsController controller,
  ) {
    final topPadding = MediaQuery.of(context).padding.top;
    final onSurfaceColor = Theme.of(context).colorScheme.onSurface;

    return Container(
      height: _appBarHeight + topPadding,
      padding: EdgeInsets.only(
        top: topPadding + _appBarPaddingTop,
        left: _appBarPaddingH,
        right: _appBarPaddingH,
      ),
      decoration: BoxDecoration(
        color: AppColors.surfaceContainer,
        border: Border(
          bottom: BorderSide(
            color: AppColors.primary.withValues(alpha: 0.3),
            width: 1.275,
          ),
        ),
      ),
      child: Row(
        children: [
          // Back button (Figma 22:929)
          GestureDetector(
            onTap: () => Get.back(),
            child: SizedBox(
              width: _backButtonSize,
              height: _backButtonSize,
              child: Center(
                child: Icon(
                  Icons.arrow_back,
                  color: onSurfaceColor,
                  size: 16,
                ),
              ),
            ),
          ),
          const SizedBox(width: 12),
          // Purple-pink gradient icon box (Figma 22:934)
          Container(
            width: _appBarIconBoxSize,
            height: _appBarIconBoxSize,
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(_appBarIconBoxRadius),
              gradient: const LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [Color(0xFFAD46FF), Color(0xFFF6339A)],
              ),
              boxShadow: [
                BoxShadow(
                  color: AppColors.black.withValues(alpha: 0.1),
                  blurRadius: 15,
                  offset: const Offset(0, 10),
                ),
                BoxShadow(
                  color: AppColors.black.withValues(alpha: 0.1),
                  blurRadius: 6,
                  offset: const Offset(0, 4),
                ),
              ],
            ),
            child: const Center(
              child: Icon(
                Icons.school_outlined,
                color: AppColors.white,
                size: _appBarIconSize,
              ),
            ),
          ),
          const SizedBox(width: 8),
          // Title (Figma 22:937)
          Text(
            'Choose Subject',
            style: TextStyle(
              color: AppColors.textOnSurface,
              fontSize: 16,
              fontWeight: FontWeight.w400,
              height: 1.5,
            ),
          ),
        ],
      ),
    );
  }

  // ── Body ─────────────────────────────────────────────────────────

  Widget _buildBody(SubjectTutorsController controller) {
    return Obx(() {
      if (controller.isLoading.value) {
        return const Center(
          child: CircularProgressIndicator(color: AppColors.primary),
        );
      }

      if (controller.errorMessage.value != null) {
        return Center(
          child: Padding(
            padding: const EdgeInsets.all(32),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  controller.errorMessage.value!,
                  style: TextStyle(
                    color: AppColors.textSecondary,
                    fontSize: 14,
                  ),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 16),
                GestureDetector(
                  onTap: () => controller.onInit(),
                  child: const Text(
                    'Retry',
                    style: TextStyle(color: AppColors.primary, fontSize: 14),
                  ),
                ),
              ],
            ),
          ),
        );
      }

      return SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(
          _contentPaddingH,
          _contentPaddingTop,
          _contentPaddingH,
          24,
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Subtitle row (Figma 22:940)
            _buildSubtitleRow(),
            const SizedBox(height: 16),
            // Subject cards
            ...controller.subjects.map(
              (subject) => Padding(
                padding: const EdgeInsets.only(bottom: _cardSpacing),
                child: _SubjectCard(
                  subject: subject,
                  onTap: () {
                    if (controller.isCreating.value) return;
                    controller.selectSubject(subject);
                  },
                ),
              ),
            ),
            const SizedBox(height: 8),
            // Info banner (Figma 22:1075)
            _buildInfoBanner(),
          ],
        ),
      );
    });
  }

  // ── Subtitle row (Figma 22:940) ──────────────────────────────────

  Widget _buildSubtitleRow() {
    return Row(
      children: [
        Icon(
          Icons.auto_awesome,
          size: 16,
          color: AppColors.primary.withValues(alpha: 0.8),
        ),
        const SizedBox(width: 8),
        Text(
          'Select a subject to start chatting',
          style: TextStyle(
            color: AppColors.textSecondary,
            fontSize: 14,
            fontWeight: FontWeight.w400,
            height: 1.43,
          ),
        ),
      ],
    );
  }

  // ── Info Banner (Figma 22:1075) ──────────────────────────────────

  Widget _buildInfoBanner() {
    return Container(
      padding: const EdgeInsets.fromLTRB(13, 13, 13, 13),
      decoration: BoxDecoration(
        color: AppColors.primary.withValues(alpha: 0.05),
        borderRadius: BorderRadius.circular(_infoBannerRadius),
        border: Border.all(
          color: AppColors.primary.withValues(alpha: 0.2),
          width: 1.275,
        ),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Icon box (Figma 22:1077)
          Container(
            width: _infoBannerIconBoxSize,
            height: _infoBannerIconBoxSize,
            decoration: BoxDecoration(
              color: AppColors.primary.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(_infoBannerIconBoxRadius),
            ),
            child: Center(
              child: Icon(
                Icons.auto_awesome,
                size: _infoBannerIconSize,
                color: AppColors.primary,
              ),
            ),
          ),
          const SizedBox(width: 8),
          // Text column (Figma 22:1083)
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Personalized AI Learning',
                  style: TextStyle(
                    color: AppColors.textOnSurface,
                    fontSize: 12,
                    fontWeight: FontWeight.w400,
                    height: 1.33,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  'Each tutor provides accurate, detailed explanations.',
                  style: TextStyle(
                    color: AppColors.textSecondary,
                    fontSize: 12,
                    fontWeight: FontWeight.w400,
                    height: 1.625,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ── Subject Card (Figma 22:948) ──────────────────────────────────────

class _SubjectCard extends StatelessWidget {
  const _SubjectCard({required this.subject, required this.onTap});

  final Subject subject;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        height: _cardHeight,
        decoration: BoxDecoration(
          color: AppColors.surfaceContainer,
          borderRadius: BorderRadius.circular(_cardRadius),
          border: Border.all(
            color: AppColors.primary.withValues(alpha: 0.3),
            width: 1.275,
          ),
        ),
        child: ClipRRect(
          borderRadius: BorderRadius.circular(_cardRadius - 1),
          child: Row(
            children: [
              const SizedBox(width: 10),
              // Subject gradient icon box
              Container(
                width: _subjectIconSize,
                height: _subjectIconSize,
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(_subjectIconRadius),
                  gradient: LinearGradient(
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                    colors: subject.gradientColors,
                  ),
                  boxShadow: [
                    BoxShadow(
                      color: AppColors.black.withValues(alpha: 0.1),
                      blurRadius: 15,
                      offset: const Offset(0, 10),
                    ),
                    BoxShadow(
                      color: AppColors.black.withValues(alpha: 0.1),
                      blurRadius: 6,
                      offset: const Offset(0, 4),
                    ),
                  ],
                ),
                child: Center(
                  child: Icon(
                    subject.icon,
                    color: AppColors.white,
                    size: _subjectIconInnerSize,
                  ),
                ),
              ),
              const SizedBox(width: 12),
              // Name + description
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(
                      subject.name,
                      style: TextStyle(
                        color: AppColors.textOnSurface,
                        fontSize: 14,
                        fontWeight: FontWeight.w400,
                        height: 1.43,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      subject.description,
                      style: TextStyle(
                        color: AppColors.textSecondary,
                        fontSize: 12,
                        fontWeight: FontWeight.w400,
                        height: 1.33,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 22),
            ],
          ),
        ),
      ),
    );
  }
}
