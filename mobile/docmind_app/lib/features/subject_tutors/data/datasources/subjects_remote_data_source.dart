import 'package:dio/dio.dart';

import '../../../../core/network/dio_client.dart';
import '../../../auth/data/datasources/auth_local_data_source.dart';
import '../../domain/errors/subjects_failure.dart';
import '../../domain/errors/tutor_conversation_failure.dart';
import '../models/subject_dto.dart';
import '../models/tutor_conversation_dto.dart';
import '../models/tutor_conversation_page_dto.dart';

class SubjectsRemoteDataSource {
  SubjectsRemoteDataSource({
    Dio? dio,
    AuthLocalDataSource? authLocal,
  })  : _dio = dio ?? DioClient.instance,
        _authLocal = authLocal ?? AuthLocalDataSource();

  final Dio _dio;
  final AuthLocalDataSource _authLocal;

  Future<List<SubjectDto>> getStudentSubjects() async {
    final token = await _authLocal.getToken();
    if (token == null || token.isEmpty) {
      throw const SubjectsFailure('You are not logged in.');
    }

    try {
      final response = await _dio.get(
        '/subjects/student',
        options: Options(headers: {'Authorization': 'Bearer $token'}),
      );

      if (response.data is List) {
        return (response.data as List<dynamic>)
            .map((e) => SubjectDto.fromJson(e as Map<String, dynamic>))
            .toList();
      }

      throw const SubjectsFailure('Unexpected server response.');
    } on DioException catch (e) {
      throw SubjectsFailure(_mapDioError(e));
    } catch (_) {
      throw const SubjectsFailure('Failed to load subjects.');
    }
  }

  Future<TutorConversationDto> createTutorConversation({
    required String subjectId,
  }) async {
    final token = await _authLocal.getToken();
    if (token == null || token.isEmpty) {
      throw const TutorConversationFailure('You are not logged in.');
    }

    try {
      final response = await _dio.post(
        '/chat/tutor/conversations',
        data: {'subjectId': subjectId},
        options: Options(headers: {'Authorization': 'Bearer $token'}),
      );

      if (response.data is Map<String, dynamic>) {
        return TutorConversationDto.fromJson(
          response.data as Map<String, dynamic>,
        );
      }

      throw const TutorConversationFailure('Unexpected server response.');
    } on DioException catch (e) {
      throw TutorConversationFailure(_mapConversationError(e));
    } catch (_) {
      throw const TutorConversationFailure(
        'Failed to create conversation. Please try again.',
      );
    }
  }

  Future<TutorConversationPageDto> getTutorConversations({
    required String subjectId,
    int page = 1,
    int pageSize = 20,
  }) async {
    final token = await _authLocal.getToken();
    if (token == null || token.isEmpty) {
      throw const TutorConversationFailure('You are not logged in.');
    }

    try {
      final response = await _dio.get(
        '/chat/tutor/conversations',
        queryParameters: {
          'subjectId': subjectId,
          'page': page,
          'pageSize': pageSize,
        },
        options: Options(headers: {'Authorization': 'Bearer $token'}),
      );

      if (response.data is Map<String, dynamic>) {
        return TutorConversationPageDto.fromJson(
          response.data as Map<String, dynamic>,
        );
      }

      throw const TutorConversationFailure('Unexpected server response.');
    } on DioException catch (e) {
      throw TutorConversationFailure(_mapConversationError(e));
    } catch (_) {
      throw const TutorConversationFailure('Failed to load history.');
    }
  }

  String _mapDioError(DioException e) {
    final status = e.response?.statusCode;
    final data = e.response?.data;

    if (status == 401 && data is Map<String, dynamic>) {
      return data['message'] as String? ?? 'Token has been revoked.';
    }

    return 'Failed to load subjects.';
  }

  String _mapConversationError(DioException e) {
    final status = e.response?.statusCode;
    final data = e.response?.data;

    if (status == 422 && data is Map<String, dynamic>) {
      final detail = data['detail'];
      if (detail is List && detail.isNotEmpty) {
        final first = detail.first;
        if (first is Map<String, dynamic>) {
          return first['msg'] as String? ?? 'Invalid input.';
        }
      }
      return 'Invalid input.';
    }

    return 'Failed to create conversation.';
  }
}
