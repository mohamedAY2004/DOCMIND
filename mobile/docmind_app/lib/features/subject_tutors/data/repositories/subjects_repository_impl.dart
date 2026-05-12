import 'package:flutter/material.dart';

import '../../domain/entities/subject.dart';
import '../../domain/entities/tutor_conversation.dart';
import '../../domain/entities/tutor_conversation_page.dart';
import '../../domain/repositories/subjects_repository.dart';
import '../datasources/subjects_remote_data_source.dart';

class SubjectsRepositoryImpl implements SubjectsRepository {
  SubjectsRepositoryImpl({SubjectsRemoteDataSource? remote})
      : _remote = remote ?? SubjectsRemoteDataSource();

  final SubjectsRemoteDataSource _remote;

  static const _palette = [
    [Color(0xFF2B7FFF), Color(0xFF00B8DB)],
    [Color(0xFF00C950), Color(0xFF00BC7D)],
    [Color(0xFFAD46FF), Color(0xFFF6339A)],
    [Color(0xFFFF6900), Color(0xFFFE9A00)],
  ];

  static const _icons = [
    Icons.calculate_outlined,
    Icons.science_outlined,
    Icons.account_tree_outlined,
    Icons.hub_outlined,
  ];

  @override
  Future<List<Subject>> getStudentSubjects() async {
    final dtos = await _remote.getStudentSubjects();

    return dtos.asMap().entries.map((entry) {
      final index = entry.key;
      final dto = entry.value;
      final palette = _palette[index % _palette.length];
      final icon = _icons[index % _icons.length];

      return Subject(
        id: dto.id,
        name: dto.title,
        description: dto.description,
        gradientColors: palette,
        icon: icon,
      );
    }).toList();
  }

  @override
  Future<TutorConversation> createTutorConversation({
    required String subjectId,
  }) async {
    final dto = await _remote.createTutorConversation(subjectId: subjectId);

    return TutorConversation(
      id: dto.id,
      title: dto.title,
      subjectId: dto.subjectId,
      createdAt: dto.createdAt,
      updatedAt: dto.updatedAt,
      messageCount: dto.messageCount,
    );
  }

  @override
  Future<TutorConversationPage> getTutorConversations({
    required String subjectId,
    int page = 1,
    int pageSize = 20,
  }) async {
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
  }
}
