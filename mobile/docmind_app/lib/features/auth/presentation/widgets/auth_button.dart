import 'package:flutter/material.dart';
import 'package:flutter_svg/svg.dart';

import '../../../../core/constants/app_colors.dart';

/// Layout constants for auth buttons matching Figma.
const double _buttonHeight = 48.0;
const double _buttonBorderRadius = 10.0;
const double _buttonFontSize = 14.0;
const double _buttonIconSize = 16.0;
const double _iconLabelGap = 8.0;

/// A reusable, Figma-matched primary action button for auth screens.
///
/// Displays a solid teal button with an optional leading [icon],
/// a text [label], and a loading indicator when [isLoading] is true.
class AuthButton extends StatelessWidget {
  const AuthButton({
    super.key,
    required this.label,
    required this.onPressed,
    this.isLoading = false,
    this.icon,
    this.isSvg = false,
    this.svgPath,
  });

  final String label;
  final VoidCallback? onPressed;
  final bool isLoading;
  final String? icon;
  final bool isSvg;
  final String? svgPath;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: double.infinity,
      height: _buttonHeight,
      child: DecoratedBox(
        decoration: BoxDecoration(
          color: AppColors.primary,
          borderRadius: BorderRadius.circular(_buttonBorderRadius),
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
        child: Material(
          color: Colors.transparent,
          child: InkWell(
            onTap: isLoading ? null : onPressed,
            borderRadius: BorderRadius.circular(_buttonBorderRadius),
            child: Center(
              child: isLoading
                  ? const SizedBox(
                      width: 22,
                      height: 22,
                      child: CircularProgressIndicator(
                        color: AppColors.white,
                        strokeWidth: 2.5,
                      ),
                    )
                  : Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        if (icon != null) ...[
                          isSvg && svgPath != null
                              ? SvgPicture.asset(
                                  svgPath!,
                                  // color: AppColors.white,
                                  width: _buttonIconSize,
                                  height: _buttonIconSize,
                                )
                              : Image.asset(
                                  icon!,
                                  color: AppColors.white,
                                  width: _buttonIconSize,
                                  height: _buttonIconSize,
                                ),
                          const SizedBox(width: _iconLabelGap),
                        ],
                        Text(
                          label,
                          style: const TextStyle(
                            color: AppColors.white,
                            fontSize: _buttonFontSize,
                            fontWeight: FontWeight.w400,
                          ),
                        ),
                      ],
                    ),
            ),
          ),
        ),
      ),
    );
  }
}
