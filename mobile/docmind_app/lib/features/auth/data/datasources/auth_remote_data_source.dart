import 'package:dio/dio.dart';
import '../../../../core/network/api_constants.dart';
import '../models/login_request.dart';
import '../models/login_response.dart';

class AuthRemoteDataSource {
  const AuthRemoteDataSource(this._dio);
  final Dio _dio;

  Future<LoginResponse> login(LoginRequest request) async {
    final response = await _dio.post(
      ApiConstants.login,
      data: request.toJson(),
    );
    return LoginResponse.fromJson(response.data as Map<String, dynamic>);
  }

  Future<void> logout() async {
    await _dio.post(ApiConstants.logout);
  }
}
