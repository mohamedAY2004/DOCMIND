import 'package:flutter/material.dart';
import 'package:get/get.dart';

import '../../../../core/constants/app_assets.dart';
import '../../../../core/constants/app_colors.dart';
import '../../domain/entities/document_conversation.dart';
import '../controllers/document_chat_controller.dart';

/// Layout constants matching Figma node 4:282.
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
const double _buttonHeight = 48.0;
const double _buttonRadius = 10.0;
const double _emptyIconBoxSize = 64.0;
const double _emptyIconBoxRadius = 24.0;
const double _emptyIconSize = 24.0;
const double _emptyTitleFontSize = 14.0;
const double _emptySubtitleFontSize = 12.0;
const double _conversationItemRadius = 12.0;

/// Chat With Documents entry page.
///
/// Shows a top bar, a "Start New Chat" button, and a list of
/// existing conversations or an empty state when none exist.
class DocumentChatEntryPage extends StatelessWidget {
  const DocumentChatEntryPage({super.key});

  @override
  Widget build(BuildContext context) {
    return GetBuilder<DocumentChatController>(
      init: DocumentChatController(),
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
                // Decorative glow
                Positioned(
                  left: -73,
                  top: 146,
                  child: Container(
                    width: 267,
                    height: 263,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: const Color(0xFF2B7FFF).withValues(alpha: 0.05),
                    ),
                  ),
                ),

                // Content below app bar
                Positioned(
                  top: _appBarHeight,
                  left: 0,
                  right: 0,
                  bottom: 0,
                  child: Padding(
                    padding: const EdgeInsets.symmetric(
                      horizontal: _contentPaddingH,
                    ),
                    child: Column(
                      children: [
                        const SizedBox(
                          height: _contentPaddingTop + _appBarHeight,
                        ),
                        _buildStartButton(controller),
                        const SizedBox(height: 12),
                        Expanded(
                          child: Obx(() => _buildContent(controller)),
                        ),
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
      },
    );
  }

  // ── App Bar ──────────────────────────────────────────────────────
  Widget _buildAppBar(BuildContext context) {
    final onSurfaceColor = Theme.of(context).colorScheme.onSurface;

    return Positioned(
      top: 0,
      left: 0,
      right: 0,
      child: Container(
        height: _appBarHeight + MediaQuery.of(context).padding.top,
        padding: EdgeInsets.only(
          top: MediaQuery.of(context).padding.top + _appBarPaddingTop,
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
          border: const Border(
            bottom: BorderSide(color: Color(0x330F9197), width: 1.275),
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
            // Gradient icon
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
            // Title
            Text(
              'Document Chats',
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

  // ── Start New Chat button ────────────────────────────────────────

  Widget _buildStartButton(DocumentChatController controller) {
    return GestureDetector(
      onTap: controller.navigateToFileSelection,
      child: Container(
        width: double.infinity,
        height: _buttonHeight,
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(_buttonRadius),
          gradient: const LinearGradient(
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
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: const [
            Icon(Icons.add, color: AppColors.white, size: 16),
            SizedBox(width: 8),
            Text(
              'Start New Chat',
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

  // ── Content (list or empty state) ───────────────────────────────

  Widget _buildContent(DocumentChatController controller) {
    if (controller.isLoadingConversations.value &&
        controller.conversations.isEmpty) {
      return const Center(
        child: CircularProgressIndicator(
          color: AppColors.primary,
        ),
      );
    }

    if (controller.conversationsError.value != null &&
        controller.conversations.isEmpty) {
      return _buildErrorState(controller);
    }

    if (controller.conversations.isEmpty) {
      return _buildEmptyState();
    }

    return _buildConversationList(controller);
  }

  // ── Conversation List ────────────────────────────────────────────

  Widget _buildConversationList(DocumentChatController controller) {
    return RefreshIndicator(
      color: AppColors.primary,
      backgroundColor: AppColors.formCardBackground,
      onRefresh: () => controller.loadConversations(refresh: true),
      child: ListView.builder(
        padding: const EdgeInsets.only(bottom: 16),
        itemCount: controller.conversations.length + 
            (controller.hasMoreConversations.value ? 1 : 0),
        itemBuilder: (context, index) {
          if (index == controller.conversations.length) {
            // Load more indicator
            if (!controller.isLoadingConversations.value) {
              controller.loadConversations();
            }
            return const Padding(
              padding: EdgeInsets.all(16),
              child: Center(
                child: SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    color: AppColors.primary,
                  ),
                ),
              ),
            );
          }

          final conversation = controller.conversations[index];
          return _ConversationListItem(
            conversation: conversation,
            onTap: () => controller.navigateToLiveChatForConversation(conversation),
            onDelete: () => _confirmDelete(controller, conversation),
          );
        },
      ),
    );
  }

  void _confirmDelete(
    DocumentChatController controller,
    DocumentConversation conversation,
  ) {
    Get.dialog(
      AlertDialog(
        backgroundColor: AppColors.formCardBackground,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
        ),
        title: Text(
          'Delete Conversation',
          style: TextStyle(color: AppColors.textOnSurface),
        ),
        content: Text(
          'Are you sure you want to delete "${conversation.title}"?',
          style: TextStyle(color: AppColors.textSecondary),
        ),
        actions: [
          TextButton(
            onPressed: () => Get.back(),
            child: Text(
              'Cancel',
              style: TextStyle(color: AppColors.textSecondary),
            ),
          ),
          TextButton(
            onPressed: () {
              Get.back();
              controller.deleteConversation(conversation.id);
            },
            child: const Text(
              'Delete',
              style: TextStyle(
                color: Color(0xFFEF4444),
                fontSize: 14,
                fontWeight: FontWeight.w400,
              ),
            ),
          ),
        ],
      ),
    );
  }


  // ── Error State ──────────────────────────────────────────────────

  Widget _buildErrorState(DocumentChatController controller) {
    return Column(
      mainAxisAlignment: MainAxisAlignment.start,
      children: [
        const SizedBox(height: 32),
        const Icon(
          Icons.error_outline,
          color: AppColors.hintText,
          size: 48,
        ),
        const SizedBox(height: 12),
        Text(
          controller.conversationsError.value ?? 'Failed to load conversations',
          style: TextStyle(
            color: AppColors.textSecondary,
            fontSize: 14,
          ),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 16),
        GestureDetector(
          onTap: () => controller.loadConversations(refresh: true),
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(10),
              gradient: const LinearGradient(
                colors: [Color(0xFF2B7FFF), Color(0xFF00B8DB)],
              ),
            ),
            child: const Text(
              'Retry',
              style: TextStyle(color: AppColors.white, fontSize: 14),
            ),
          ),
        ),
      ],
    );
  }

  // ── Empty state ──────────────────────────────────────────────────

  Widget _buildEmptyState() {
    return Column(
      mainAxisAlignment: MainAxisAlignment.start,
      children: [
        const SizedBox(height: 32),
        // Faded gradient icon
        Opacity(
          opacity: 0.2,
          child: Container(
            width: _emptyIconBoxSize,
            height: _emptyIconBoxSize,
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(_emptyIconBoxRadius),
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
                width: _emptyIconSize,
                height: _emptyIconSize,
                color: AppColors.white,
                errorBuilder: (_, __, ___) => const Icon(
                  Icons.description,
                  color: AppColors.white,
                  size: _emptyIconSize,
                ),
              ),
            ),
          ),
        ),
        const SizedBox(height: 12),
        // "No chats yet" text
        Text(
          'No chats yet',
          style: TextStyle(
            color: AppColors.textOnSurface,
            fontSize: _emptyTitleFontSize,
            fontWeight: FontWeight.w400,
          ),
        ),
        const SizedBox(height: 4),
        // Subtitle
        Text(
          'Start your first conversation by clicking the button above',
          style: TextStyle(
            color: AppColors.textSecondary,
            fontSize: _emptySubtitleFontSize,
            fontWeight: FontWeight.w400,
          ),
          textAlign: TextAlign.center,
        ),
      ],
    );
  }
}

/// Conversation list item widget.
class _ConversationListItem extends StatelessWidget {
  const _ConversationListItem({
    required this.conversation,
    required this.onTap,
    required this.onDelete,
  });

  final DocumentConversation conversation;
  final VoidCallback onTap;
  final VoidCallback onDelete;

  @override
  Widget build(BuildContext context) {
    return Dismissible(
      key: Key(conversation.id),
      direction: DismissDirection.endToStart,
      background: Container(
        alignment: Alignment.centerRight,
        padding: const EdgeInsets.only(right: 20),
        margin: const EdgeInsets.only(bottom: 8),
        decoration: BoxDecoration(
          color: Colors.red.withValues(alpha: 0.2),
          borderRadius: BorderRadius.circular(_conversationItemRadius),
        ),
        child: const Icon(
          Icons.delete_outline,
          color: Colors.red,
          size: 24,
        ),
      ),
      confirmDismiss: (direction) async {
        onDelete();
        return false; // We handle delete in the callback
      },
      child: GestureDetector(
        onTap: onTap,
        child: Container(
          margin: const EdgeInsets.only(bottom: 8),
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: AppColors.surfaceContainer,
            borderRadius: BorderRadius.circular(_conversationItemRadius),
            border: Border.all(
              color: AppColors.primary.withValues(alpha: 0.2),
              width: 1,
            ),
          ),
          child: Row(
            children: [
              // Document icon
              Container(
                width: 44,
                height: 44,
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(12),
                  gradient: const LinearGradient(
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                    colors: [Color(0xFF2B7FFF), Color(0xFF00B8DB)],
                  ),
                ),
                child: const Center(
                  child: Icon(
                    Icons.description_outlined,
                    color: AppColors.white,
                    size: 22,
                  ),
                ),
              ),
              const SizedBox(width: 12),
              // Title and info
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      conversation.title,
                      style: TextStyle(
                        color: AppColors.textOnSurface,
                        fontSize: 14,
                        fontWeight: FontWeight.w500,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 4),
                    Row(
                      children: [
                        Icon(
                          Icons.chat_bubble_outline,
                          color: AppColors.hintText.withValues(alpha: 0.7),
                          size: 12,
                        ),
                        const SizedBox(width: 4),
                        Text(
                          '${conversation.messageCount} messages',
                          style: TextStyle(
                            color: AppColors.hintText.withValues(alpha: 0.7),
                            fontSize: 12,
                          ),
                        ),
                        const SizedBox(width: 12),
                        Icon(
                          Icons.access_time,
                          color: AppColors.hintText.withValues(alpha: 0.7),
                          size: 12,
                        ),
                        const SizedBox(width: 4),
                        Text(
                          conversation.relativeTime,
                          style: TextStyle(
                            color: AppColors.hintText.withValues(alpha: 0.7),
                            fontSize: 12,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              // Arrow
              Icon(
                Icons.chevron_right,
                color: AppColors.hintText.withValues(alpha: 0.5),
                size: 20,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
