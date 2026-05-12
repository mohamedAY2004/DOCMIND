import 'package:dio/dio.dart';

import '../../../../core/network/dio_client.dart';
import '../../domain/errors/auth_failure.dart';
import '../models/login_request.dart';
import '../models/login_response.dart';

/// Calls the backend auth endpoints.
class AuthRemoteDataSource {
  AuthRemoteDataSource({Dio? dio}) : _dio = dio ?? DioClient.instance;

  final Dio _dio;

  Future<LoginResponse> login(LoginRequest request) async {
    try {
      final response = await _dio.post(
        '/auth/login',
        data: request.toJson(),
      );

      if (response.data is Map<String, dynamic>) {
        return LoginResponse.fromJson(response.data as Map<String, dynamic>);
      }

      throw const AuthFailure('Unexpected server response.');
    } on DioException catch (e) {
      throw AuthFailure(_mapDioError(e));
    } catch (_) {
      throw const AuthFailure('Unable to login. Please try again.');
    }
  }

  Future<void> logout({required String token}) async {
    try {
      await _dio.post(
        '/auth/logout',
        options: Options(
          headers: {'Authorization': 'Bearer $token'},
        ),
      );
    } on DioException catch (e) {
      throw AuthFailure(_mapDioError(e));
    } catch (_) {
      throw const AuthFailure('Unable to logout. Please try again.');
    }
  }

  String _mapDioError(DioException e) {
    final status = e.response?.statusCode;
    final data = e.response?.data;

    if (status == 401 && data is Map<String, dynamic>) {
      return data['message'] as String? ?? 'Invalid username or password.';
    }

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

    return 'Something went wrong. Please try again.';
  }
}
