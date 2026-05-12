import '../entities/tutor_conversation.dart';
import '../repositories/subjects_repository.dart';

class CreateTutorConversationUseCase {
  const CreateTutorConversationUseCase(this._repository);

  final SubjectsRepository _repository;

  Future<TutorConversation> call({required String subjectId}) {
    return _repository.createTutorConversation(subjectId: subjectId);
  }
}
