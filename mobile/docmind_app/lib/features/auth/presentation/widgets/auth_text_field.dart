import 'package:flutter/material.dart';
import 'package:get/get_connect/http/src/utils/utils.dart';

import '../../../../core/constants/app_colors.dart';

/// Layout constants for auth text fields matching Figma.
const double _inputHeight = 48.0;
const double _inputBorderRadius = 10.0;
const double _inputBorderWidth = 1.275;
const double _inputFontSize = 16.0;
const double _labelFontSize = 14.0;
const double _labelIconSize = 16.0;
const double _labelGap = 8.0;
const double _fieldGap = 8.0;
const double _suffixIconSize = 20.0;

/// A reusable, Figma-matched text field for the auth screens.
///
/// Displays an optional [labelText] with an [labelIcon] above the input,
/// and a semi-transparent dark input container with a teal border.
class AuthTextField extends StatelessWidget {
  const AuthTextField({
    super.key,
    required this.controller,
    required this.hintText,
    this.labelText,
    this.labelIcon,
    this.obscureText = false,
    this.suffixIcon,
    this.validator,
    this.keyboardType,
  });

  final TextEditingController controller;
  final String hintText;
  final String? labelText;
  final Widget? labelIcon;
  final bool obscureText;
  final Widget? suffixIcon;
  final String? Function(String?)? validator;
  final TextInputType? keyboardType;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        if (labelText != null) ...[
          Row(
            children: [
              if (labelIcon != null) ...[
                SizedBox(
                  width: _labelIconSize,
                  height: _labelIconSize,
                  child: labelIcon,
                ),
                const SizedBox(width: _labelGap),
              ],
              Text(
                labelText!,
                style: TextStyle(
                  fontSize: _labelFontSize,
                  color: Theme.of(context).colorScheme.onSurface,
                  fontWeight: FontWeight.w400,
                ),
              ),
            ],
          ),
          const SizedBox(height: _fieldGap),
        ],
        SizedBox(
          height: _inputHeight,
          child: TextFormField(
            controller: controller,
            obscureText: obscureText,
            validator: validator,
            keyboardType: keyboardType,
            style: TextStyle(
              color: Theme.of(context).colorScheme.onSurface,
              fontSize: _inputFontSize,
            ),
            decoration: InputDecoration(
              hintText: hintText,
              hintStyle: const TextStyle(
                color: AppColors.hintText,
                fontSize: _inputFontSize,
              ),
              filled: true,
              fillColor: AppColors.inputBackground,
              contentPadding: const EdgeInsets.symmetric(
                horizontal: 12,
                vertical: 4,
              ),
              suffixIcon: suffixIcon != null
                  ? Padding(
                      padding: const EdgeInsets.all(14.0),
                      child: SizedBox(
                        width: _suffixIconSize,
                        height: _suffixIconSize,
                        child: suffixIcon,
                      ),
                    )
                  : null,
              enabledBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(_inputBorderRadius),
                borderSide: BorderSide(
                  color: AppColors.primary.withValues(alpha: 0.3),
                  width: _inputBorderWidth,
                ),
              ),
              focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(_inputBorderRadius),
                borderSide: BorderSide(
                  color: AppColors.primary.withValues(alpha: 0.6),
                  width: _inputBorderWidth,
                ),
              ),
              errorBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(_inputBorderRadius),
                borderSide: const BorderSide(
                  color: Colors.redAccent,
                  width: _inputBorderWidth,
                ),
              ),
              focusedErrorBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(_inputBorderRadius),
                borderSide: const BorderSide(
                  color: Colors.redAccent,
                  width: _inputBorderWidth,
                ),
              ),
              errorStyle: const TextStyle(fontSize: 0, height: 0),
            ),
          ),
        ),
      ],
    );
  }
}
