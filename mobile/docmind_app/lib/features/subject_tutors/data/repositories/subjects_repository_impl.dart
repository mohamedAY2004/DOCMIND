import 'package:fpdart/fpdart.dart';
import '../../../../core/domain/failure.dart';
import '../../../../core/network/repository_call.dart';

import '../../domain/entities/subject.dart';
import '../../domain/entities/tutor_conversation.dart';
import '../../domain/entities/tutor_conversation_page.dart';
import '../../domain/repositories/subjects_repository.dart';
import '../datasources/subjects_remote_data_source.dart';

class SubjectsRepositoryImpl implements SubjectsRepository {
  const SubjectsRepositoryImpl(this._remote);

  final SubjectsRemoteDataSource _remote;

  @override
  Future<Either<Failure, List<Subject>>> getStudentSubjects() =>
      repositoryCall(() async {
        final dtos = await _remote.getStudentSubjects();

        return dtos
            .map(
              (dto) => Subject(
                id: dto.id,
                name: dto.title,
                description: dto.description,
              ),
            )
            .toList();
      });

  @override
  Future<Either<Failure, TutorConversation>> createTutorConversation({
    required String subjectId,
  }) => repositoryCall(() async {
    final dto = await _remote.createTutorConversation(subjectId: subjectId);

    return TutorConversation(
      id: dto.id,
      title: dto.title,
      subjectId: dto.subjectId,
      createdAt: dto.createdAt,
      updatedAt: dto.updatedAt,
      messageCount: dto.messageCount,
    );
  });

  @override
  Future<Either<Failure, TutorConversationPage>> getTutorConversations({
    required String subjectId,
    int page = 1,
    int pageSize = 20,
  }) => repositoryCall(() async {
    final pageDto = await _remote.getTutorConversations(
      subjectId: subjectId,
      page: page,
      pageSize: pageSize,
    );

    final items = pageDto.items
        .map(
          (dto) => TutorConversation(
            id: dto.id,
            title: dto.title,
            subjectId: dto.subjectId,
            createdAt: dto.createdAt,
            updatedAt: dto.updatedAt,
            messageCount: dto.messageCount,
          ),
        )
        .toList();

    return TutorConversationPage(
      items: items,
      page: pageDto.page,
      pageSize: pageDto.pageSize,
      total: pageDto.total,
      totalPages: pageDto.totalPages,
    );
  });
}
