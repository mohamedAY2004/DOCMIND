abstract final class ApiConstants {
  // Android emulator default; physical devices pass --dart-define=API_BASE_URL=...
  static const baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000/api',
  );
  static const login = '/auth/login';
  static const logout = '/auth/logout';
  static const studentSubjects = '/subjects/student';
  static const docConversations = '/chat/doc/conversations';
  static const tutorConversations = '/chat/tutor/conversations';
  static String docConversation(String id) =>
      '$docConversations/${Uri.encodeComponent(id)}';
  static String tutorConversation(String id) =>
      '$tutorConversations/${Uri.encodeComponent(id)}';
  static String docFiles(String id) => '${docConversation(id)}/files';
  static String docFile(String id, String fileId) =>
      '${docFiles(id)}/${Uri.encodeComponent(fileId)}';
  static String messages(String id, {required bool document}) =>
      '${document ? docConversation(id) : tutorConversation(id)}/messages';
}
