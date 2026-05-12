import 'package:flutter/material.dart';

import '../../../../core/constants/app_assets.dart';
import '../../../../core/constants/app_colors.dart';
import '../../domain/entities/chat_message.dart';

/// Layout constants for chat bubbles matching Figma node 4:450.
const double _bubbleRadius = 16.0;
const double _avatarSize = 40.0;
const double _avatarRadius = 16.0;
const double _avatarIconSize = 20.0;
const double _messageFontSize = 14.0;
const double _timeFontSize = 12.0;
const double _bubblePaddingH = 16.0;
const double _bubblePaddingV = 16.0;
const double _avatarGap = 12.0;
const double _maxBubbleWidthFraction = 0.7;

/// A single chat message bubble.
///
/// User messages are teal, right-aligned with a person avatar.
/// AI messages have a dark bordered card, left-aligned with a brain avatar.
class ChatBubble extends StatefulWidget {
  const ChatBubble({super.key, required this.message});

  final ChatMessage message;

  @override
  State<ChatBubble> createState() => _ChatBubbleState();
}

class _ChatBubbleState extends State<ChatBubble>
    with SingleTickerProviderStateMixin {
  late AnimationController _dotsController;

  @override
  void initState() {
    super.initState();
    _dotsController = AnimationController(
      duration: const Duration(milliseconds: 1200),
      vsync: this,
    );
    if (widget.message.isThinking) {
      _dotsController.repeat();
    }
  }

  @override
  void didUpdateWidget(ChatBubble oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.message.isThinking && !_dotsController.isAnimating) {
      _dotsController.repeat();
    } else if (!widget.message.isThinking && _dotsController.isAnimating) {
      _dotsController.stop();
    }
  }

  @override
  void dispose() {
    _dotsController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final screenWidth = MediaQuery.of(context).size.width;
    final maxBubbleWidth = screenWidth * _maxBubbleWidthFraction;

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: widget.message.isUser
          ? _buildUserBubble(maxBubbleWidth)
          : _buildAiBubble(maxBubbleWidth),
    );
  }

  // ── User Bubble (Figma 4:480) ────────────────────────────────────

  Widget _buildUserBubble(double maxWidth) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.end,
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Spacer(),
        Container(
          constraints: BoxConstraints(maxWidth: maxWidth),
          padding: const EdgeInsets.fromLTRB(
            _bubblePaddingH,
            _bubblePaddingV,
            _bubblePaddingH,
            12,
          ),
          decoration: BoxDecoration(
            color: AppColors.primary,
            borderRadius: BorderRadius.circular(_bubbleRadius),
            boxShadow: [
              BoxShadow(
                color: AppColors.primary.withValues(alpha: 0.2),
                blurRadius: 15,
                offset: const Offset(0, 10),
              ),
              BoxShadow(
                color: AppColors.primary.withValues(alpha: 0.2),
                blurRadius: 6,
                offset: const Offset(0, 4),
              ),
            ],
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                widget.message.content,
                style: TextStyle(
                  color: AppColors.textOnSurface,
                  fontSize: _messageFontSize,
                  fontWeight: FontWeight.w400,
                  height: 1.625,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                _formatTime(widget.message.timestamp),
                style: TextStyle(
                  color: AppColors.textOnSurface.withValues(alpha: 0.7),
                  fontSize: _timeFontSize,
                  fontWeight: FontWeight.w400,
                  height: 1.33,
                ),
              ),
            ],
          ),
        ),
        const SizedBox(width: _avatarGap),
        _buildAvatar(
          background: AppColors.surfaceContainer,
          icon: Icons.person_outline,
          shadow: AppColors.black.withValues(alpha: 0.1),
        ),
      ],
    );
  }

  // ── AI Bubble (Figma 4:490) ──────────────────────────────────────

  Widget _buildAiBubble(double maxWidth) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.start,
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(
          width: _avatarSize,
          height: _avatarSize,
          child: Image.asset(
            AppAssets.docmindLogo,
            width: _avatarSize,
            height: _avatarSize,
            errorBuilder: (_, __, ___) => _buildAvatar(
              background: AppColors.surfaceContainer,
              icon: Icons.psychology_outlined,
              shadow: AppColors.black.withValues(alpha: 0.1),
            ),
          ),
        ),
        const SizedBox(width: _avatarGap),
        Container(
          constraints: BoxConstraints(maxWidth: maxWidth),
          padding: const EdgeInsets.fromLTRB(
            _bubblePaddingH + 1,
            _bubblePaddingV + 1,
            _bubblePaddingH + 1,
            12,
          ),
          decoration: BoxDecoration(
            color: AppColors.formCardBackground,
            borderRadius: BorderRadius.circular(_bubbleRadius),
            border: Border.all(
              color: AppColors.primary.withValues(alpha: 0.2),
              width: 1.275,
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
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (widget.message.isThinking)
                _buildThinkingIndicator()
              else
                Text(
                  widget.message.content,
                  style: TextStyle(
                    color: AppColors.textOnSurface,
                    fontSize: _messageFontSize,
                    fontWeight: FontWeight.w400,
                    height: 1.625,
                  ),
                ),
              const SizedBox(height: 8),
              Text(
                _formatTime(widget.message.timestamp),
                style: TextStyle(
                  color: AppColors.textSecondary,
                  fontSize: _timeFontSize,
                  fontWeight: FontWeight.w400,
                  height: 1.33,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  // ── Thinking Indicator ───────────────────────────────────────────

  Widget _buildThinkingIndicator() {
    return AnimatedBuilder(
      animation: _dotsController,
      builder: (context, child) {
        // Show 1, 2, or 3 dots based on animation progress
        final progress = _dotsController.value;
        final dotsCount = (progress * 3).toInt() + 1;
        final dots = List.filled(dotsCount, '.').join();
        final spaces = List.filled(3 - dotsCount, ' ').join();

        return Text(
          '$dots$spaces',
          style: TextStyle(
            color: AppColors.textOnSurface,
            fontSize: _messageFontSize,
            fontWeight: FontWeight.w400,
            height: 1.625,
            letterSpacing: 2,
          ),
        );
      },
    );
  }

  // ── Helpers ──────────────────────────────────────────────────────

  Widget _buildAvatar({
    required Color background,
    required IconData icon,
    required Color shadow,
  }) {
    return Container(
      width: _avatarSize,
      height: _avatarSize,
      decoration: BoxDecoration(
        color: background,
        borderRadius: BorderRadius.circular(_avatarRadius),
        boxShadow: [
          BoxShadow(color: shadow, blurRadius: 15, offset: const Offset(0, 10)),
          BoxShadow(color: shadow, blurRadius: 6, offset: const Offset(0, 4)),
        ],
      ),
      child: Center(
        child: Icon(icon, color: AppColors.white, size: _avatarIconSize),
      ),
    );
  }

  static String _formatTime(DateTime dt) {
    final hour = dt.hour > 12 ? dt.hour - 12 : (dt.hour == 0 ? 12 : dt.hour);
    final period = dt.hour >= 12 ? 'PM' : 'AM';
    final minute = dt.minute.toString().padLeft(2, '0');
    return '${hour.toString().padLeft(2, '0')}:$minute $period';
  }
}