/// Represents an academic subject available for AI tutoring.
///
/// Pure Dart — no framework dependencies.
class Subject {
  const Subject({
    required this.id,
    required this.name,
    required this.description,
  });

  final String id;
  final String name;
  final String description;
}
