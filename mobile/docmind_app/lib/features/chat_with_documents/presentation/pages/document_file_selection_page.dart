import 'package:flutter/material.dart';
import 'package:get/get.dart';

import '../../../../core/constants/app_assets.dart';
import '../../../../core/constants/app_colors.dart';
import '../controllers/document_chat_controller.dart';

/// Layout constants matching Figma node 4:324.
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
const double _heroIconSize = 80.0;
const double _heroIconRadius = 24.0;
const double _heroInnerIconSize = 40.0;
const double _chooseButtonRadius = 10.0;
const double _badgeRadius = 42770700.0;

/// Document File Selection page — second screen of Chat With Documents.
///
/// Displays an upload card with a "Choose File" button. After a file
/// is selected the file name is shown and a "Start Upload" button appears.
/// All logic is delegated to [DocumentChatController].
class DocumentFileSelectionPage extends StatelessWidget {
  const DocumentFileSelectionPage({super.key});

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
                  children: [
                    _buildUploadCard(controller),
                    const SizedBox(height: 24),
                    _buildSelectedFileInfo(controller),
                    const SizedBox(height: 24),
                    _buildStartUploadButton(controller),
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

  // ── App Bar (Figma 4:329) ────────────────────────────────────────

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
            // Back button
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
            // Gradient icon box (Figma 4:336)
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
            // Title (Figma 4:344)
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

  // ── Upload Card (Figma 4:346) ────────────────────────────────────

  Widget _buildUploadCard(DocumentChatController controller) {
    return Container(
      width: double.infinity,
      decoration: BoxDecoration(
        color: AppColors.surfaceContainer,
        borderRadius: BorderRadius.circular(_cardRadius),
        border: Border.all(
          color: AppColors.primary.withValues(alpha: 0.2),
          width: 1.275,
        ),
      ),
      child: Stack(
        clipBehavior: Clip.none,
        children: [
          // Card content
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 32),
            child: Column(
              children: [
                // Hero icon (Figma 4:368)
                _buildHeroIcon(),
                const SizedBox(height: 24),
                // Title (Figma 4:350)
                Text(
                  'Upload Your Study Material',
                  style: TextStyle(
                    color: AppColors.textOnSurface,
                    fontSize: 16,
                    fontWeight: FontWeight.w400,
                    height: 1.5,
                  ),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 8),
                // Description (Figma 4:352)
                Text(
                  'Upload a PDF, DOCX, or TXT file and start\nan intelligent conversation',
                  style: TextStyle(
                    color: AppColors.textSecondary,
                    fontSize: 14,
                    fontWeight: FontWeight.w400,
                    height: 1.43,
                  ),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 20),
                // Choose File button (Figma 4:354)
                _buildChooseFileButton(controller),
                const SizedBox(height: 24),
                // Format badges (Figma 4:360)
                _buildFormatBadges(),
              ],
            ),
          ),
        ],
      ),
    );
  }

  // ── Hero Icon (Figma 4:368) ──────────────────────────────────────

  Widget _buildHeroIcon() {
    return SizedBox(
      width: _heroIconSize,
      height: _heroIconSize,
      child: Stack(
        clipBehavior: Clip.none,
        children: [
          // Main gradient box
          Container(
            width: _heroIconSize,
            height: _heroIconSize,
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(_heroIconRadius),
              gradient: const LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [Color(0xFF2B7FFF), Color(0xFF00B8DB)],
              ),
              boxShadow: [
                BoxShadow(
                  color: const Color(0xFF2B7FFF).withValues(alpha: 0.3),
                  blurRadius: 50,
                  offset: const Offset(0, 25),
                ),
              ],
            ),
            child: const Center(
              child: Icon(
                Icons.cloud_upload_outlined,
                color: AppColors.white,
                size: _heroInnerIconSize,
              ),
            ),
          ),
          // Small badge (Figma 4:373) — settings/gear icon
          Positioned(
            right: -8,
            top: -8,
            child: Center(
              child: Image.asset(
                AppAssets.docmindLogo,
                width: 28,
                height: 28,
              ),
            ),
          ),
        ],
      ),
    );
  }

  // ── Choose File Button (Figma 4:354) ─────────────────────────────

  Widget _buildChooseFileButton(DocumentChatController controller) {
    return GestureDetector(
      onTap: controller.pickFile,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(_chooseButtonRadius),
          gradient: const LinearGradient(
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
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: const [
            Icon(Icons.cloud_upload_outlined, color: AppColors.white, size: 16),
            SizedBox(width: 8),
            Text(
              'Choose File',
              style: TextStyle(
                color: AppColors.white,
                fontSize: 14,
                fontWeight: FontWeight.w400,
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ── Format Badges (Figma 4:360) ──────────────────────────────────

  Widget _buildFormatBadges() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: const [
        _FormatBadge(label: 'PDF'),
        SizedBox(width: 8),
        _FormatBadge(label: 'DOCX'),
        SizedBox(width: 8),
        _FormatBadge(label: 'TXT'),
      ],
    );
  }

  // ── Selected File Info ───────────────────────────────────────────

  Widget _buildSelectedFileInfo(DocumentChatController controller) {
    return Obx(() {
      final file = controller.selectedFile.value;
      if (file == null) return const SizedBox.shrink();

      final fileName = file.path.split(RegExp(r'[/\\]')).last;

      return Container(
        width: double.infinity,
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: AppColors.surfaceContainer,
          borderRadius: BorderRadius.circular(_cardRadius),
          border: Border.all(
            color: AppColors.primary.withValues(alpha: 0.2),
            width: 1.275,
          ),
        ),
        child: Row(
          children: [
            // File icon
            Container(
              width: 40,
              height: 40,
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(12),
                gradient: LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: [
                    const Color(0xFF2B7FFF).withValues(alpha: 0.2),
                    const Color(0xFF00B8DB).withValues(alpha: 0.2),
                  ],
                ),
              ),
              child: const Center(
                child: Icon(
                  Icons.insert_drive_file_outlined,
                  color: Color(0xFF00B8DB),
                  size: 20,
                ),
              ),
            ),
            const SizedBox(width: 12),
            // File name
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    fileName,
                    style: TextStyle(
                      color: AppColors.textOnSurface,
                      fontSize: 14,
                      fontWeight: FontWeight.w500,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 2),
                  Text(
                    _getFileExtension(fileName).toUpperCase(),
                    style: TextStyle(
                      color: AppColors.textSecondary.withValues(alpha: 0.7),
                      fontSize: 12,
                      fontWeight: FontWeight.w400,
                    ),
                  ),
                ],
              ),
            ),
            // Change file button
            GestureDetector(
              onTap: controller.pickFile,
              child: Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 12,
                  vertical: 6,
                ),
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(
                    color: AppColors.primary.withValues(alpha: 0.3),
                  ),
                ),
                child: const Text(
                  'Change',
                  style: TextStyle(
                    color: Color(0xFF00B8DB),
                    fontSize: 12,
                    fontWeight: FontWeight.w400,
                  ),
                ),
              ),
            ),
          ],
        ),
      );
    });
  }

  // ── Start Upload Button ──────────────────────────────────────────

  Widget _buildStartUploadButton(DocumentChatController controller) {
    return Obx(() {
      final hasFile = controller.selectedFile.value != null;
      final loading = controller.isLoading.value;
      final progress = controller.uploadProgress.value;

      return GestureDetector(
        onTap: hasFile && !loading ? controller.startSession : null,
        child: AnimatedOpacity(
          opacity: hasFile ? 1.0 : 0.4,
          duration: const Duration(milliseconds: 250),
          child: Container(
            width: double.infinity,
            height: 48,
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(_chooseButtonRadius),
              gradient: const LinearGradient(
                colors: [Color(0xFF2B7FFF), Color(0xFF00B8DB)],
              ),
              boxShadow: hasFile
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
            child: Center(
              child: loading
                  ? Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(
                            value: progress > 0 ? progress : null,
                            strokeWidth: 2,
                            valueColor: const AlwaysStoppedAnimation<Color>(
                              AppColors.white,
                            ),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Text(
                          progress > 0
                              ? 'Uploading... ${(progress * 100).toInt()}%'
                              : 'Starting...',
                          style: const TextStyle(
                            color: AppColors.white,
                            fontSize: 14,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ],
                    )
                  : Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: const [
                        Icon(
                          Icons.cloud_upload_outlined,
                          color: AppColors.white,
                          size: 18,
                        ),
                        SizedBox(width: 8),
                        Text(
                          'Start Upload',
                          style: TextStyle(
                            color: AppColors.white,
                            fontSize: 14,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ],
                    ),
            ),
          ),
        ),
      );
    });
  }

  // ── Helpers ──────────────────────────────────────────────────────

  static String _getFileExtension(String fileName) {
    final dotIndex = fileName.lastIndexOf('.');
    if (dotIndex == -1 || dotIndex == fileName.length - 1) return '';
    return fileName.substring(dotIndex + 1);
  }
}

/// Small rounded pill showing a supported format label.
class _FormatBadge extends StatelessWidget {
  const _FormatBadge({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
      decoration: BoxDecoration(
        color: AppColors.inputBackground,
        borderRadius: BorderRadius.circular(_badgeRadius),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: AppColors.textSecondary,
          fontSize: 12,
          fontWeight: FontWeight.w400,
          height: 1.33,
        ),
        textAlign: TextAlign.center,
      ),
    );
  }
}
