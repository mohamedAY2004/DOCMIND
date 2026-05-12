import 'package:flutter/material.dart';

/// The type of action a home option card represents.
enum HomeOptionType { chatWithDocuments, subjectTutors, profile }

/// A single option displayed on the Home screen.
///
/// Carries both the content data (title, subtitle) and the visual
/// presentation data (icon, gradient) so that the UI layer can render
/// it without any conditional logic.
class HomeOption {
  const HomeOption({
    required this.id,
    required this.title,
    required this.subtitle,
    required this.type,
    required this.iconAsset,
    required this.gradientColors,
  });

  /// Unique identifier for the option.
  final String id;

  /// Display title shown on the card.
  final String title;

  /// Short description shown below the title.
  final String subtitle;

  /// Determines the navigation target when tapped.
  final HomeOptionType type;

  /// Asset path for the card icon (PNG).
  final String iconAsset;

  /// Two-color gradient used for the icon container.
  final List<Color> gradientColors;
}
