/// Request body for sending a message in a document conversation.
class SendMessageRequest {
  const SendMessageRequest({required this.message});

  final String message;

  Map<String, dynamic> toJson() {
    return {'message': message};
  }
}
