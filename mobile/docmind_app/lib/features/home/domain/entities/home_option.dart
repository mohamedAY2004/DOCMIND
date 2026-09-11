/// The type of action a home option card represents.
enum HomeOptionType { chatWithDocuments, subjectTutors, profile }

/// A single option displayed on the Home screen.
///
/// Appearance belongs to the presentation layer.
class HomeOption {
  const HomeOption({
    required this.id,
    required this.title,
    required this.subtitle,
    required this.type,
  });

  /// Unique identifier for the option.
  final String id;

  /// Display title shown on the card.
  final String title;

  /// Short description shown below the title.
  final String subtitle;

  /// Determines the navigation target when tapped.
  final HomeOptionType type;
}
