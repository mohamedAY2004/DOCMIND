import 'package:flutter/material.dart';

/// Represents an academic subject available for AI tutoring.
///
/// Pure Dart — no framework dependencies.
class Subject {
  const Subject({
    required this.id,
    required this.name,
    required this.description,
    required this.gradientColors,
    required this.icon,
  });

  final String id;
  final String name;
  final String description;

  /// Two colors used to build the subject icon gradient (topLeft → bottomRight).
  final List<Color> gradientColors;

  /// Material icon displayed inside the gradient icon box.
  final IconData icon;
}
