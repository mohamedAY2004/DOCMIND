import 'chat_message.dart';

class ChatTurn {
  const ChatTurn({required this.userMessage, required this.reply});
  final ChatMessage userMessage;
  final ChatMessage reply;
}
