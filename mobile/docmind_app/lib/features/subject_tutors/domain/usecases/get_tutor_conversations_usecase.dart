import '../entities/tutor_conversation_page.dart';
import '../repositories/subjects_repository.dart';

class GetTutorConversationsUseCase {
  const GetTutorConversationsUseCase(this._repository);

  final SubjectsRepository _repository;

  Future<TutorConversationPage> call({
    required String subjectId,
    int page = 1,
    int pageSize = 20,
  }) {
    return _repository.getTutorConversations(
      subjectId: subjectId,
      page: page,
      pageSize: pageSize,
    );
  }
}
