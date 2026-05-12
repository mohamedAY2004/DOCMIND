import 'package:flutter/material.dart';
import 'package:get/get.dart';

import '../../../../core/constants/app_colors.dart';
import '../../../chat_with_documents/presentation/controllers/document_chat_controller.dart';
import '../../../chat_with_documents/domain/entities/document_file.dart';
import '../../domain/entities/chat_session.dart';
import '../controllers/live_chat_controller.dart';
import '../widgets/chat_bubble.dart';

/// Layout constants matching Figma node 4:450.
const double _appBarHeight = 73.0;
const double _appBarPaddingH = 16.0;
const double _appBarPaddingTop = 16.0;
// icon constants removed (unused in this simplified app bar)
const double _backButtonSize = 36.0;
const double _inputFieldHeight = 48.0;
const double _inputFieldRadius = 16.0;
const double _sendButtonSize = 48.0;
const double _sendButtonRadius = 16.0;
const double _sendIconSize = 16.0;
const double _messagePaddingH = 16.0;

/// Live Chat Session page — reusable across features.
///
/// Receives a [ChatSession] object via [Get.arguments]. All state is driven
/// reactively by [LiveChatController].
class LiveChatPage extends StatelessWidget {
  const LiveChatPage({super.key});

  @override
  Widget build(BuildContext context) {
    return GetBuilder<LiveChatController>(
      init: LiveChatController(),
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
            child: Column(
              children: [
                _buildAppBar(context, controller),
                Expanded(
                  child: Container(
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        begin: Alignment.topCenter,
                        end: Alignment.bottomCenter,
                        colors: [
                          AppColors.surfaceContainer,
                          AppColors.screenBackgroundGradientBottom,
                        ],
                      ),
                    ),
                    child: _buildMessageList(controller),
                  ),
                ),
                _buildInputBar(controller),
              ],
            ),
          ),
        );
      },
    );
  }

  // ── App Bar (simple) ───────────────────────────────────────────

  Widget _buildAppBar(BuildContext context, LiveChatController controller) {
    final topPadding = MediaQuery.of(context).padding.top;
    final isDocumentChat = controller.session.sourceType == KnowledgeSourceType.document;
    final docController = isDocumentChat &&
        Get.isRegistered<DocumentChatController>()
      ? Get.find<DocumentChatController>()
      : null;
    final displayName = isDocumentChat
      ? (docController?.session.value?.fileName ??
        controller.session.displayName ??
        'Chat')
      : (controller.session.displayName ?? 'Chat');

    return Container(
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
          // Back button for document chats, History icon for tutor chats
          GestureDetector(
            onTap: () => isDocumentChat ? Get.back() : _showHistorySheet(context, controller),
            child: Container(
              width: _backButtonSize,
              height: _backButtonSize,
              decoration: BoxDecoration(
                color: AppColors.primary.withValues(alpha: 0.12),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: AppColors.primary.withValues(alpha: 0.3),
                  width: 1,
                ),
              ),
              child: Center(
                child: Icon(
                  isDocumentChat ? Icons.arrow_back : Icons.history,
                  color: AppColors.textOnSurface,
                  size: 18,
                ),
              ),
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  isDocumentChat ? 'Document Chat' : 'AI Tutor Chat',
                  style: TextStyle(
                    color: AppColors.textOnSurface,
                    fontSize: 14,
                    fontWeight: FontWeight.w400,
                    height: 1.43,
                  ),
                ),
                Text(
                  displayName,
                  style: TextStyle(
                    color: AppColors.textSecondary,
                    fontSize: 12,
                    fontWeight: FontWeight.w400,
                    height: 1.33,
                  ),
                ),
              ],
            ),
          ),
          if (isDocumentChat)
            GestureDetector(
              onTap: () => _showDocumentOptionsSheet(
                context,
                controller,
                docController,
              ),
              child: SizedBox(
                width: _backButtonSize,
                height: _backButtonSize,
                child: Center(
                  child: Icon(
                    Icons.more_vert,
                    color: AppColors.textSecondary,
                    size: 18,
                  ),
                ),
              ),
            ),
          if (!isDocumentChat)
            GestureDetector(
              onTap: () => Get.back(),
              child: SizedBox(
                width: _backButtonSize,
                height: _backButtonSize,
                child: Center(
                  child: Icon(
                    Icons.close,
                    color: AppColors.textSecondary,
                    size: 16,
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }

  Future<void> _showDocumentOptionsSheet(
    BuildContext context,
    LiveChatController controller,
    DocumentChatController? docController,
  ) async {
    if (docController == null) {
      Get.snackbar('Error', 'Document chat controller unavailable');
      return;
    }

    await showModalBottomSheet(
      context: context,
      backgroundColor: AppColors.formCardBackground,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (sheetContext) {
        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(
                  width: 40,
                  height: 4,
                  decoration: BoxDecoration(
                    color: AppColors.hintText.withValues(alpha: 0.4),
                    borderRadius: BorderRadius.circular(4),
                  ),
                ),
                const SizedBox(height: 16),
                _buildSheetAction(
                  icon: Icons.folder_open,
                  label: 'Manage files',
                  onTap: () {
                    Navigator.of(sheetContext).pop();
                    _showConversationFilesSheet(
                      context,
                      controller,
                      docController,
                    );
                  },
                ),
                const SizedBox(height: 8),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildSheetAction({
    required IconData icon,
    required String label,
    required VoidCallback onTap,
  }) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        decoration: BoxDecoration(
          color: AppColors.surfaceContainer,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: AppColors.primary.withValues(alpha: 0.2),
          ),
        ),
        child: Row(
          children: [
            Icon(icon, color: AppColors.textOnSurface, size: 18),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                label,
                style: TextStyle(
                  color: AppColors.textOnSurface,
                  fontSize: 14,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ),
            Icon(
              Icons.chevron_right,
              color: AppColors.hintText.withValues(alpha: 0.7),
              size: 18,
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _showConversationFilesSheet(
    BuildContext context,
    LiveChatController controller,
    DocumentChatController docController,
  ) async {
    final conversationId = controller.session.sessionId;
    if (conversationId.trim().isEmpty) return;

    docController.loadConversationFiles(conversationId);

    await showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppColors.formCardBackground,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (sheetContext) {
        return SafeArea(
          child: Padding(
            padding: EdgeInsets.only(
              left: 16,
              right: 16,
              top: 12,
              bottom: MediaQuery.of(sheetContext).viewInsets.bottom + 16,
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(
                  width: 40,
                  height: 4,
                  decoration: BoxDecoration(
                    color: AppColors.hintText.withValues(alpha: 0.4),
                    borderRadius: BorderRadius.circular(4),
                  ),
                ),
                const SizedBox(height: 16),
                Row(
                  children: [
                    Text(
                      'Chat files',
                      style: TextStyle(
                        color: AppColors.textOnSurface,
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const Spacer(),
                    TextButton.icon(
                      onPressed: () async {
                        await docController.pickFile();
                        await docController
                            .addSelectedFileToConversation(conversationId);
                      },
                      icon: Icon(Icons.add, color: AppColors.primary, size: 18),
                      label: Text(
                        'Add file',
                        style: TextStyle(color: AppColors.primary),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Obx(() {
                  if (docController.isLoadingFiles.value) {
                    return const Padding(
                      padding: EdgeInsets.symmetric(vertical: 24),
                      child: CircularProgressIndicator(
                        color: AppColors.primary,
                      ),
                    );
                  }

                  if (docController.filesError.value != null) {
                    return Padding(
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      child: Text(
                        docController.filesError.value ??
                            'Failed to load files',
                        style: TextStyle(color: AppColors.textSecondary),
                        textAlign: TextAlign.center,
                      ),
                    );
                  }

                  if (docController.conversationFiles.isEmpty) {
                    return Padding(
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      child: Text(
                        'No files linked to this chat yet.',
                        style: TextStyle(color: AppColors.textSecondary),
                      ),
                    );
                  }

                  return SizedBox(
                    height: 320,
                    child: ListView.separated(
                      itemCount: docController.conversationFiles.length,
                      separatorBuilder: (_, __) => const SizedBox(height: 8),
                      itemBuilder: (itemContext, index) {
                        final file = docController.conversationFiles[index];
                        return Container(
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: AppColors.surfaceContainer,
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(
                              color: AppColors.primary.withValues(alpha: 0.15),
                            ),
                          ),
                          child: Row(
                            children: [
                              Icon(
                                Icons.description_outlined,
                                color: AppColors.textOnSurface,
                                size: 20,
                              ),
                              const SizedBox(width: 12),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      file.name,
                                      style: TextStyle(
                                        color: AppColors.textOnSurface,
                                        fontSize: 13,
                                        fontWeight: FontWeight.w500,
                                      ),
                                      maxLines: 1,
                                      overflow: TextOverflow.ellipsis,
                                    ),
                                    const SizedBox(height: 4),
                                    Text(
                                      _formatFileMeta(file),
                                      style: TextStyle(
                                        color: AppColors.textSecondary,
                                        fontSize: 11,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                              const SizedBox(width: 8),
                              GestureDetector(
                                onTap: () => docController.deleteConversationFile(
                                  conversationId: conversationId,
                                  fileId: file.id,
                                ),
                                child: Icon(
                                  Icons.delete_outline,
                                  color: Colors.red.withValues(alpha: 0.8),
                                  size: 18,
                                ),
                              ),
                            ],
                          ),
                        );
                      },
                    ),
                  );
                }),
              ],
            ),
          ),
        );
      },
    );
  }

  String _formatFileMeta(DocumentFile file) {
    final size = file.sizeBytes == null
        ? ''
        : _formatBytes(file.sizeBytes!);
    final status = switch (file.status) {
      DocumentFileStatus.completed => 'Ready',
      DocumentFileStatus.processing => 'Processing',
      DocumentFileStatus.failed => 'Failed',
    };
    final parts = [status];
    if (size.isNotEmpty) parts.add(size);
    return parts.join(' • ');
  }

  String _formatBytes(int bytes) {
    const kb = 1024;
    const mb = 1024 * 1024;
    if (bytes >= mb) {
      return '${(bytes / mb).toStringAsFixed(1)} MB';
    }
    if (bytes >= kb) {
      return '${(bytes / kb).toStringAsFixed(1)} KB';
    }
    return '$bytes B';
  }

  Future<void> _showHistorySheet(
    BuildContext context,
    LiveChatController controller,
  ) async {
    // Prepare a single ScrollController and listener so the list isn't recreated
    // and the scroll position is preserved when new pages are appended.
    final scroll = ScrollController();
    scroll.addListener(() {
      if (scroll.position.pixels >= scroll.position.maxScrollExtent - 80) {
        controller.loadMoreHistory();
      }
    });

    // Only load initial history if nothing is cached yet for this session.
    if (controller.history.isEmpty) {
      // Kick off history loading but don't await to avoid using `context`
      // across an async gap (this method is a StatelessWidget helper).
      controller.loadHistory();
    }

    // Right-side sliding panel (chatgpt-like)
    await showGeneralDialog(
      context: context,
      barrierDismissible: true,
      barrierLabel: 'History',
      barrierColor: Colors.black54,
      transitionDuration: const Duration(milliseconds: 300),
      pageBuilder: (context, anim1, anim2) {
        final width = MediaQuery.of(context).size.width * 0.85;
        final panelWidth = width > 420 ? 420.0 : width;
        return Align(
          alignment: Alignment.centerRight,
          child: SafeArea(
            child: Material(
              color: Colors.transparent,
              child: Container(
                width: panelWidth,
                height: MediaQuery.of(context).size.height,
                decoration: BoxDecoration(
                  color: AppColors.formCardBackground,
                  borderRadius: const BorderRadius.horizontal(left: Radius.circular(20)),
                ),
                padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Previous Chats',
                      style: TextStyle(
                        color: AppColors.textOnSurface,
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const SizedBox(height: 12),
                    Expanded(
                      child: Obx(() {
                        if (controller.isHistoryLoading.value) {
                          return const Center(
                            child: Padding(
                              padding: EdgeInsets.all(24),
                              child: CircularProgressIndicator(
                                color: AppColors.primary,
                              ),
                            ),
                          );
                        }

                        final error = controller.historyError.value;
                        if (error != null) {
                          return Padding(
                            padding: const EdgeInsets.all(12),
                            child: Text(
                              error,
                              style: TextStyle(
                                color: AppColors.textSecondary,
                                fontSize: 14,
                              ),
                            ),
                          );
                        }

                        if (controller.history.isEmpty) {
                          return Padding(
                            padding: const EdgeInsets.all(12),
                            child: Text(
                              'No previous conversations yet.',
                              style: TextStyle(
                                color: AppColors.textSecondary,
                                fontSize: 14,
                              ),
                            ),
                          );
                        }

                        return ListView.separated(
                          controller: scroll,
                          itemCount: controller.history.length +
                              (controller.historyHasMore.value ? 1 : 0),
                          separatorBuilder: (_, __) => const Divider(
                            color: Color(0x1A0F9197),
                            height: 16,
                          ),
                          itemBuilder: (context, index) {
                            if (index < controller.history.length) {
                              final item = controller.history[index];
                              return ListTile(
                                contentPadding: EdgeInsets.zero,
                                title: Text(
                                  item.title.isNotEmpty
                                      ? item.title
                                      : 'Conversation ${index + 1}',
                                  style: TextStyle(
                                    color: AppColors.textOnSurface,
                                    fontSize: 14,
                                    fontWeight: FontWeight.w500,
                                  ),
                                ),
                                subtitle: Text(
                                  '${item.messageCount} messages',
                                  style: TextStyle(
                                    color: AppColors.textSecondary,
                                    fontSize: 12,
                                  ),
                                ),
                                trailing: Icon(
                                  Icons.chevron_right,
                                  color: AppColors.textSecondary,
                                ),
                                onTap: () {
                                  Navigator.of(context).pop();
                                  controller.selectConversation(item);
                                },
                              );
                            }

                            // Loading indicator for additional pages
                            if (controller.isHistoryLoading.value) {
                              return const Padding(
                                padding: EdgeInsets.all(12),
                                child: Center(
                                  child: CircularProgressIndicator(
                                    color: AppColors.primary,
                                  ),
                                ),
                              );
                            }

                            return const SizedBox.shrink();
                          },
                        );
                      }),
                    ),
                  ],
                ),
              ),
            ),
          ),
        );
      },
      transitionBuilder: (context, anim1, anim2, child) {
        return SlideTransition(
          position: Tween<Offset>(begin: const Offset(1, 0), end: Offset.zero)
              .animate(CurvedAnimation(parent: anim1, curve: Curves.easeOut)),
          child: child,
        );
      },
    );

    // Dispose the scroll controller after the dialog is dismissed.
    scroll.dispose();
  }

  // ── Message List ─────────────────────────────────────────────────

  Widget _buildMessageList(LiveChatController controller) {
    return Obx(() {
      final msgs = controller.messages;

      if (msgs.isEmpty) {
        return Center(
          child: Padding(
            padding: const EdgeInsets.all(32),
            child: Text(
              'Start a conversation by typing a message below.',
              style: TextStyle(
                color: AppColors.textSecondary,
                fontSize: 14,
                fontWeight: FontWeight.w400,
              ),
              textAlign: TextAlign.center,
            ),
          ),
        );
      }

      return ListView.builder(
        padding: const EdgeInsets.symmetric(
          horizontal: _messagePaddingH,
          vertical: 24,
        ),
        reverse: true,
        itemCount: msgs.length,
        itemBuilder: (context, index) {
          final msgIndex = msgs.length - 1 - index;

          if (msgIndex < 0 || msgIndex >= msgs.length) {
            return const SizedBox.shrink();
          }

          return ChatBubble(message: msgs[msgIndex]);
        },
      );
    });
  }

  // ── Input Bar (Figma 4:552) ──────────────────────────────────────

  Widget _buildInputBar(LiveChatController controller) {
    return Container(
      padding: const EdgeInsets.fromLTRB(12, 13, 12, 13),
      decoration: BoxDecoration(
        color: AppColors.surfaceContainer,
        border: Border(
          top: BorderSide(
            color: AppColors.primary.withValues(alpha: 0.2),
            width: 1.275,
          ),
        ),
      ),
      child: SafeArea(
        top: false,
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Expanded(
              child: Container(
                constraints: const BoxConstraints(
                  minHeight: _inputFieldHeight,
                  maxHeight: 120, // Max ~5 lines
                ),
                decoration: BoxDecoration(
                  color: AppColors.inputBackground,
                  borderRadius: BorderRadius.circular(_inputFieldRadius),
                  border: Border.all(
                    color: AppColors.primary.withValues(alpha: 0.3),
                    width: 1.275,
                  ),
                ),
                child: TextField(
                  controller: controller.messageController,
                  style: TextStyle(
                    color: AppColors.textOnSurface,
                    fontSize: 14,
                    fontWeight: FontWeight.w400,
                  ),
                  decoration: InputDecoration(
                    hintText: 'Type your message...',
                    hintStyle: TextStyle(
                      color: AppColors.textSecondary,
                      fontSize: 14,
                      fontWeight: FontWeight.w400,
                    ),
                    border: InputBorder.none,
                    contentPadding: const EdgeInsets.symmetric(
                      horizontal: 12,
                      vertical: 14,
                    ),
                  ),
                  maxLines: 5,
                  minLines: 1,
                  keyboardType: TextInputType.multiline,
                  textInputAction: TextInputAction.newline,
                  onSubmitted: (_) => controller.sendMessage(),
                ),
              ),
            ),
            const SizedBox(width: 8),
            Obx(() {
              final sending = controller.isSending.value;
              return GestureDetector(
                onTap: sending ? null : controller.sendMessage,
                child: AnimatedOpacity(
                  opacity: sending ? 0.5 : 1.0,
                  duration: const Duration(milliseconds: 200),
                  child: Container(
                    width: _sendButtonSize,
                    height: _sendButtonSize,
                    decoration: BoxDecoration(
                      color: AppColors.primary,
                      borderRadius: BorderRadius.circular(_sendButtonRadius),
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
                    child: const Center(
                      child: Icon(
                        Icons.send,
                        color: AppColors.white,
                        size: _sendIconSize,
                      ),
                    ),
                  ),
                ),
              );
            }),
          ],
        ),
      ),
    );
  }
}
