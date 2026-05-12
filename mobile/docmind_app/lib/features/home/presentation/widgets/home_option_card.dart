import 'package:flutter/material.dart';

import '../../../../core/constants/app_colors.dart';
import '../../domain/entities/home_option.dart';

/// Layout constants matching Figma.
const double _cardHeight = 75.0;
const double _cardBorderRadius = 16.0;
const double _cardBorderWidth = 1.275;
const double _cardPaddingH = 12.0;
const double _iconBoxSize = 48.0;
const double _iconBoxRadius = 16.0;
const double _iconSize = 28.0;
const double _contentGap = 12.0;
const double _titleFontSize = 14.0;
const double _subtitleFontSize = 12.0;
const double _chevronSize = 16.0;

/// A reusable card that renders a single [HomeOption].
///
/// All visual data (icon, gradient, text) comes from the entity,
/// so this widget has zero conditional logic.
class HomeOptionCard extends StatelessWidget {
  const HomeOptionCard({super.key, required this.option, required this.onTap});

  final HomeOption option;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        height: _cardHeight,
        decoration: BoxDecoration(
          color: AppColors.formCardBackground,
          borderRadius: BorderRadius.circular(_cardBorderRadius),
          border: Border.all(
            color: AppColors.primary.withValues(alpha: 0.2),
            width: _cardBorderWidth,
          ),
          boxShadow: [
            BoxShadow(
              color: AppColors.black.withValues(alpha: 0.1),
              blurRadius: 15,
              spreadRadius: -3,
              offset: const Offset(0, 10),
            ),
            BoxShadow(
              color: AppColors.black.withValues(alpha: 0.1),
              blurRadius: 6,
              spreadRadius: -4,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: _cardPaddingH),
          child: Row(
            children: [
              // ── Gradient icon box ──
              Container(
                width: _iconBoxSize,
                height: _iconBoxSize,
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(_iconBoxRadius),
                  gradient: LinearGradient(
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                    colors: option.gradientColors,
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
                    option.iconAsset,
                    width: _iconSize,
                    height: _iconSize,
                    color: AppColors.white,
                    errorBuilder: (_, __, ___) => const Icon(
                      Icons.help_outline,
                      color: AppColors.white,
                      size: _iconSize,
                    ),
                  ),
                ),
              ),
              const SizedBox(width: _contentGap),

              // ── Text content ──
              Expanded(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      option.title,
                      style: TextStyle(
                        color: AppColors.textOnSurface,
                        fontSize: _titleFontSize,
                        fontWeight: FontWeight.w400,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      option.subtitle,
                      style: TextStyle(
                        color: AppColors.textSecondary,
                        fontSize: _subtitleFontSize,
                        fontWeight: FontWeight.w400,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              ),

              // ── Chevron ──
              Icon(
                Icons.chevron_right,
                color: AppColors.textSecondary,
                size: _chevronSize,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
