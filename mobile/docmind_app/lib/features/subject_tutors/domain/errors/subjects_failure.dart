/// Domain-level failure for subjects.
class SubjectsFailure implements Exception {
  const SubjectsFailure(this.message);

  final String message;

  @override
  String toString() => message;
}
