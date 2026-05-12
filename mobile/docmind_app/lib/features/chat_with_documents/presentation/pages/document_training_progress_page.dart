import 'package:flutter/material.dart';
import 'package:get/get.dart';

import '../../../../core/constants/app_assets.dart';
import '../../../../core/constants/app_colors.dart';
import '../../domain/entities/document_chat_session.dart';
import '../controllers/document_chat_controller.dart';

/// Layout constants matching.
const double _appBarHeight = 65.0;
const double _appBarPaddingH = 12.0;
const double _appBarPaddingTop = 12.0;
const double _iconBoxSize = 40.0;
const double _iconBoxRadius = 16.0;
const double _iconSize = 20.0;
const double _backButtonSize = 36.0;
const double _titleFontSize = 16.0;
const double _contentPaddingH = 16.0;
const double _contentPaddingTop = 16.0;
const double _cardRadius = 16.0;
const double _fileIconBoxSize = 56.0;
const double _fileIconBoxRadius = 16.0;
const double _fileIconSize = 28.0;
const double _progressBarHeight = 6.0;
const double _startButtonHeight = 48.0;
const double _startButtonRadius = 10.0;
const double _dotSize = 4.0;

/// Document Training Progress page — third screen of Chat With Documents.
///
/// Displays the session file, upload/training progress bar and status text,
/// a "Start AI Chat" button (enabled only when [DocumentChatController.isReadyForChat]
/// emits true), and an AI-Powered Learning info card.
/// All state is bound reactively to [DocumentChatController]; no logic lives here.
class DocumentTrainingProgressPage extends StatelessWidget {
  const DocumentTrainingProgressPage({super.key});

  @override
  Widget build(BuildContext context) {
    final controller = Get.find<DocumentChatController>();

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
            // Decorative glow
            Positioned(
              left: 40,
              top: 78,
              child: Container(
                width: 259,
                height: 259,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: const Color(0xFF2B7FFF).withValues(alpha: 0.05),
                ),
              ),
            ),

            // Main content below app bar
            Positioned(
              top: _appBarHeight + MediaQuery.of(context).padding.top,
              left: 0,
              right: 0,
              bottom: 0,
              child: SingleChildScrollView(
                padding: const EdgeInsets.symmetric(
                  horizontal: _contentPaddingH,
                  vertical: _contentPaddingTop,
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    // File + progress card
                    _buildFileCard(controller),
                    const SizedBox(height: 16),
                    // Start AI Chat button
                    _buildStartChatButton(controller),
                    const SizedBox(height: 16),
                    // AI-Powered Learning info card
                    const _AiInfoCard(),
                  ],
                ),
              ),
            ),

            // App bar overlay
            _buildAppBar(context),
          ],
        ),
      ),
    );
  }

  // ── App Bar ────────────────────────────────────────

  Widget _buildAppBar(BuildContext context) {
    final topPadding = MediaQuery.of(context).padding.top;
    final onSurfaceColor = Theme.of(context).colorScheme.onSurface;

    return Positioned(
      top: 0,
      left: 0,
      right: 0,
      child: Container(
        height: _appBarHeight + topPadding,
        padding: EdgeInsets.only(
          top: topPadding + _appBarPaddingTop,
          left: _appBarPaddingH,
          right: _appBarPaddingH,
        ),
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: [
              AppColors.formCardBackground,
              AppColors.formCardBackground.withValues(alpha: 0.5),
            ],
          ),
          border: Border(
            bottom: BorderSide(
              color: AppColors.primary.withValues(alpha: 0.2),
              width: 1.275,
            ),
          ),
        ),
        child: Row(
          children: [
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
            // Gradient icon box
            Container(
              width: _iconBoxSize,
              height: _iconBoxSize,
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(_iconBoxRadius),
                gradient: const LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: [Color(0xFF2B7FFF), Color(0xFF00B8DB)],
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
                child: Image.asset(
                  AppAssets.documentIcon,
                  width: _iconSize,
                  height: _iconSize,
                  color: AppColors.white,
                  errorBuilder: (_, __, ___) => const Icon(
                    Icons.description,
                    color: AppColors.white,
                    size: _iconSize,
                  ),
                ),
              ),
            ),
            const SizedBox(width: 8),
            Text(
              'Upload Document',
              style: TextStyle(
                color: AppColors.textOnSurface,
                fontSize: _titleFontSize,
                fontWeight: FontWeight.w400,
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ── File + Progress Card ───────────────────────────

  Widget _buildFileCard(DocumentChatController controller) {
    return Container(
      decoration: BoxDecoration(
        color: AppColors.formCardBackground,
        borderRadius: BorderRadius.circular(_cardRadius),
        border: Border.all(
          color: AppColors.primary.withValues(alpha: 0.2),
          width: 1.275,
        ),
      ),
      padding: const EdgeInsets.all(16),
      child: Obx(() {
        final s = controller.session.value;
        final fileName = s?.fileName ?? '—';
        final progress = s?.uploadProgress ?? 0.0;
        final status = s?.trainingStatus ?? TrainingStatus.initial;

        return Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // File icon box
            Container(
              width: _fileIconBoxSize,
              height: _fileIconBoxSize,
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(_fileIconBoxRadius),
                gradient: const LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: [Color(0xFF2B7FFF), Color(0xFF00B8DB)],
                ),
                boxShadow: [
                  BoxShadow(
                    color: const Color(0xFF2B7FFF).withValues(alpha: 0.3),
                    blurRadius: 15,
                    offset: const Offset(0, 10),
                  ),
                  BoxShadow(
                    color: const Color(0xFF2B7FFF).withValues(alpha: 0.3),
                    blurRadius: 6,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: Center(
                child: Image.asset(
                  AppAssets.documentIcon,
                  width: _fileIconSize,
                  height: _fileIconSize,
                  color: AppColors.white,
                  errorBuilder: (_, __, ___) => const Icon(
                    Icons.insert_drive_file_outlined,
                    color: AppColors.white,
                    size: _fileIconSize,
                  ),
                ),
              ),
            ),
            const SizedBox(width: 16),
            // File info column
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // File name
                  Text(
                    fileName,
                    style: TextStyle(
                      color: AppColors.textOnSurface,
                      fontSize: 16,
                      fontWeight: FontWeight.w400,
                      height: 1.5,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 4),
                  // Status subtitle
                  Text(
                    _statusLabel(status),
                    style: TextStyle(
                      color: AppColors.textSecondary,
                      fontSize: 14,
                      fontWeight: FontWeight.w400,
                      height: 1.43,
                    ),
                  ),
                 // const SizedBox(height: 8),
                  // Progress bar + percentage
                  /*Row(
                    children: [
                      Expanded(
                        child: ClipRRect(
                          borderRadius: BorderRadius.circular(
                            _progressBarHeight,
                          ),
                          child: Stack(
                            children: [
                              // Track
                              Container(
                                height: _progressBarHeight,
                                decoration: BoxDecoration(
                                  color: AppColors.surfaceContainer,
                                  borderRadius: BorderRadius.circular(
                                    _progressBarHeight,
                                  ),
                                ),
                              ),
                              // Fill
                              FractionallySizedBox(
                                widthFactor: progress.clamp(0.0, 1.0),
                                child: Container(
                                  height: _progressBarHeight,
                                  decoration: BoxDecoration(
                                    borderRadius: BorderRadius.circular(
                                      _progressBarHeight,
                                    ),
                                    gradient: const LinearGradient(
                                      colors: [
                                        Color(0xFF2B7FFF),
                                        Color(0xFF00B8DB),
                                      ],
                                    ),
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(width: 8),
                      // Percentage label
                      Text(
                        '${(progress * 100).toInt()}%',
                        style: const TextStyle(
                          color: AppColors.primary,
                          fontSize: 12,
                          fontWeight: FontWeight.w400,
                          height: 1.33,
                        ),
                      ),
                    ],
                  ),*/
                ],
              ),
            ),
            const SizedBox(width: 8),
            // Dismiss / close button
            GestureDetector(
              onTap: () => Get.back(),
              child: const SizedBox(
                width: 36,
                height: 36,
                child: Center(
                  child: Icon(Icons.close, color: AppColors.hintText, size: 16),
                ),
              ),
            ),
          ],
        );
      }),
    );
  }

  // ── Start AI Chat Button ──────────────────────────

  Widget _buildStartChatButton(DocumentChatController controller) {
    return Obx(() {
      final ready = controller.isReadyForChat.value;
      final status = controller.session.value?.trainingStatus ?? TrainingStatus.initial;
      final isPolling = controller.isPolling.value;
      final hasFailed = status == TrainingStatus.failed;

      return ElevatedButton(
        onPressed: ready ? controller.navigateToLiveChat : null,
        style: ElevatedButton.styleFrom(
          padding: EdgeInsets.zero,
          minimumSize: const Size(double.infinity, _startButtonHeight),
          fixedSize: const Size(double.infinity, _startButtonHeight),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(_startButtonRadius),
          ),
          elevation: 0,
          backgroundColor: Colors.transparent,
          disabledBackgroundColor: Colors.transparent,
          shadowColor: Colors.transparent,
        ),
        child: AnimatedOpacity(
          opacity: ready || isPolling ? 1.0 : 0.4,
          duration: const Duration(milliseconds: 250),
          child: Container(
            height: _startButtonHeight,
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(_startButtonRadius),
              gradient: hasFailed
                  ? const LinearGradient(
                      colors: [Colors.red, Colors.redAccent],
                    )
                  : const LinearGradient(
                      colors: [Color(0xFF2B7FFF), Color(0xFF00B8DB)],
                    ),
              boxShadow: ready
                  ? [
                      BoxShadow(
                        color: const Color(0xFF2B7FFF).withValues(alpha: 0.3),
                        blurRadius: 15,
                        offset: const Offset(0, 10),
                      ),
                      BoxShadow(
                        color: const Color(0xFF2B7FFF).withValues(alpha: 0.3),
                        blurRadius: 6,
                        offset: const Offset(0, 4),
                      ),
                    ]
                  : [],
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                if (isPolling) ...[
                  const SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      valueColor: AlwaysStoppedAnimation<Color>(AppColors.white),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Text(
                    'Processing document…',
                    style: TextStyle(
                      color: AppColors.textOnSurface,
                      fontSize: 14,
                      fontWeight: FontWeight.w400,
                    ),
                  ),
                ] else if (hasFailed) ...[
                  const Icon(
                    Icons.refresh,
                    color: AppColors.white,
                    size: 16,
                  ),
                  const SizedBox(width: 8),
                  Text(
                    'Upload Failed — Tap to Retry',
                    style: TextStyle(
                      color: AppColors.textOnSurface,
                      fontSize: 14,
                      fontWeight: FontWeight.w400,
                    ),
                  ),
                ] else ...[
                  Image.asset(
                    AppAssets.starIcon,
                    width: 16,
                    height: 16,
                    color: AppColors.white,
                  ),
                  const SizedBox(width: 8),
                  Text(
                    'Start AI Chat',
                    style: TextStyle(
                      color: AppColors.textOnSurface,
                      fontSize: 14,
                      fontWeight: FontWeight.w400,
                    ),
                  ),
                ],
              ],
            ),
          ),
        ),
      );
    });
  }

  // ── Helpers ──────────────────────────────────────────────────────

  static String _statusLabel(TrainingStatus status) {
    return switch (status) {
      TrainingStatus.initial => 'Preparing…',
      TrainingStatus.uploading => 'Uploading…',
      TrainingStatus.processing => 'Processing document…',
      TrainingStatus.completed => 'Ready to chat',
      TrainingStatus.failed => 'Failed — please retry',
    };
  }
}

// ── AI-Powered Learning Card ────────────────────────

class _AiInfoCard extends StatelessWidget {
  const _AiInfoCard();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 16),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(_cardRadius),
        border: Border.all(
          color: AppColors.primary.withValues(alpha: 0.1),
          width: 1.275,
        ),
        gradient: LinearGradient(
          begin: Alignment(0, -0.8),
          end: Alignment(0, 1),
          colors: [
            AppColors.surfaceContainer,
            AppColors.surfaceContainer.withValues(alpha: 0.5),
          ],
        ),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Brain / AI icon
          const Padding(
            padding: EdgeInsets.only(top: 2),
            child: Icon(
              Icons.psychology_outlined,
              color: AppColors.primary,
              size: 22,
            ),
          ),
          const SizedBox(width: 12),
          // Text block
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Heading
                Text(
                  'AI-Powered Learning',
                  style: TextStyle(
                    color: AppColors.textOnSurface,
                    fontSize: 14,
                    fontWeight: FontWeight.w400,
                    height: 1.43,
                  ),
                ),
                const SizedBox(height: 8),
                // Bullet list
                const _BulletItem(text: 'Ask questions about specific topics'),
                SizedBox(height: 6),
                const _BulletItem(text: 'Get instant summaries and explanations'),
                SizedBox(height: 6),
                const _BulletItem(text: 'Understand complex concepts easily'),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _BulletItem extends StatelessWidget {
  const _BulletItem({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        Container(
          width: _dotSize,
          height: _dotSize,
          decoration: const BoxDecoration(
            shape: BoxShape.circle,
            color: AppColors.primary,
          ),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: Text(
            text,
            style: TextStyle(
              color: AppColors.textSecondary,
              fontSize: 12,
              fontWeight: FontWeight.w400,
              height: 1.33,
            ),
          ),
        ),
      ],
    );
  }
}
