import '../entities/subject.dart';
import '../entities/tutor_conversation.dart';
import '../entities/tutor_conversation_page.dart';

abstract class SubjectsRepository {
  Future<List<Subject>> getStudentSubjects();

  Future<TutorConversation> createTutorConversation({
    required String subjectId,
  });

  Future<TutorConversationPage> getTutorConversations({
    required String subjectId,
    int page = 1,
    int pageSize = 20,
  });
}
