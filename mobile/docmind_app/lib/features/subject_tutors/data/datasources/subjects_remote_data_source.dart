import 'package:dio/dio.dart';
import '../../../../core/network/api_constants.dart';
import '../models/subject_dto.dart';
import '../models/tutor_conversation_dto.dart';
import '../models/tutor_conversation_page_dto.dart';

class SubjectsRemoteDataSource {
  const SubjectsRemoteDataSource(this._dio);
  final Dio _dio;

  Future<List<SubjectDto>> getStudentSubjects() async {
    final response = await _dio.get(ApiConstants.studentSubjects);
    return (response.data as List)
        .map((item) => SubjectDto.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  Future<TutorConversationDto> createTutorConversation({
    required String subjectId,
  }) async {
    final response = await _dio.post(
      ApiConstants.tutorConversations,
      data: {'subjectId': subjectId},
    );
    return TutorConversationDto.fromJson(response.data as Map<String, dynamic>);
  }

  Future<TutorConversationPageDto> getTutorConversations({
    required String subjectId,
    int page = 1,
    int pageSize = 20,
  }) async {
    final response = await _dio.get(
      ApiConstants.tutorConversations,
      queryParameters: {
        'subjectId': subjectId,
        'page': page,
        'pageSize': pageSize,
      },
    );
    return TutorConversationPageDto.fromJson(
      response.data as Map<String, dynamic>,
    );
  }
}
