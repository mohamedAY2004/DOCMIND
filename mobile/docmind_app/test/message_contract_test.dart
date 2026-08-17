import 'package:flutter_test/flutter_test.dart';
import 'package:docmind_app/features/chat_with_documents/data/models/send_message_response_dto.dart';

void main() {
  test('enhanced message response remains backward compatible', () {
    final response = SendMessageResponseDto.fromJson({
      'userMessage': {
        'id': 'msg_user',
        'role': 'user',
        'text': 'What is entropy?',
        'createdAt': '2026-08-17T10:00:00Z',
      },
      'reply': {
        'id': 'msg_reply',
        'role': 'assistant',
        'text': 'Entropy measures uncertainty [1].',
        'createdAt': '2026-08-17T10:00:01Z',
        'generationStatus': 'complete',
        'groundingStatus': 'grounded',
        'citations': [
          {
            'id': 'cite_1',
            'marker': 1,
            'sourceKind': 'material',
            'sourceId': 'mat_1',
            'sourceName': 'Lecture 2',
            'location': {'type': 'page', 'number': 4},
            'section': 'Entropy',
            'excerpt': 'Entropy measures uncertainty.',
            'score': 0.94,
          },
        ],
      },
    });

    expect(response.reply.generationStatus, 'complete');
    expect(response.reply.groundingStatus, 'grounded');
    expect(response.reply.citations.single.locationNumber, 4);
    expect(response.userMessage.citations, isEmpty);
  });
}
