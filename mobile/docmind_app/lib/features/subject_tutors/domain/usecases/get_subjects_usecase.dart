import '../entities/subject.dart';
import '../repositories/subjects_repository.dart';

/// Returns the list of subjects available for AI tutoring.
///
/// Pure Dart — no repository or Flutter UI dependencies.
/// TODO(backend): Replace with real API call when backend is ready.
class GetSubjectsUseCase {
  const GetSubjectsUseCase(this._repository);

  final SubjectsRepository _repository;

  Future<List<Subject>> call() => _repository.getStudentSubjects();
}
