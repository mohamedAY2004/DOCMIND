import 'package:fpdart/fpdart.dart';
import '../../../../core/domain/failure.dart';
import '../entities/subject.dart';
import '../entities/tutor_conversation.dart';
import '../entities/tutor_conversation_page.dart';

abstract class SubjectsRepository {
  Future<Either<Failure, List<Subject>>> getStudentSubjects();

  Future<Either<Failure, TutorConversation>> createTutorConversation({
    required String subjectId,
  });

  Future<Either<Failure, TutorConversationPage>> getTutorConversations({
    required String subjectId,
    int page = 1,
    int pageSize = 20,
  });
}
