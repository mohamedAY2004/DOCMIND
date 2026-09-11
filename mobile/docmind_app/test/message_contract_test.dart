import 'package:flutter_test/flutter_test.dart';
import 'package:docmind_app/features/live_chat/data/models/send_message_response_dto.dart';
import 'package:dio/dio.dart';
import 'package:docmind_app/features/live_chat/data/datasources/live_chat_remote_data_source.dart';
import 'package:docmind_app/features/live_chat/data/repositories/live_chat_repository_impl.dart';
import 'package:docmind_app/features/live_chat/domain/entities/chat_session.dart';

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

  test('sending and descending history use the same metadata mapper', () async {
    final reply = <String, dynamic>{
      'id': 'reply',
      'role': 'assistant',
      'text': 'Partial answer',
      'createdAt': '2026-09-09T12:00:00Z',
      'generationStatus': 'cancelled',
      'groundingStatus': 'grounded',
      'citations': [
        {
          'id': 'cite',
          'marker': 1,
          'sourceKind': 'document',
          'sourceId': 'file',
          'sourceName': 'Lecture',
          'location': {'type': 'page', 'number': 9},
          'section': 'Summary',
          'excerpt': 'Quoted passage',
          'score': 0.8,
        },
      ],
    };
    final user = {...reply, 'id': 'user', 'role': 'user', 'citations': []};
    final dio = Dio()
      ..interceptors.add(
        InterceptorsWrapper(
          onRequest: (request, handler) {
            if (request.method == 'GET') {
              expect(request.queryParameters['order'], 'desc');
            }
            handler.resolve(
              Response(
                requestOptions: request,
                statusCode: 200,
                data: request.method == 'GET'
                    ? {
                        'items': [reply, user],
                        'page': 1,
                        'pageSize': 50,
                        'total': 2,
                        'totalPages': 1,
                      }
                    : {'userMessage': user, 'reply': reply},
              ),
            );
          },
        ),
      );
    final repository = LiveChatRepositoryImpl(LiveChatRemoteDataSource(dio));
    final sent = await repository.sendMessage(
      conversationId: 'chat',
      message: 'Question',
      sourceType: KnowledgeSourceType.document,
    );
    final history = await repository.getConversationMessages(
      conversationId: 'chat',
      sourceType: KnowledgeSourceType.document,
    );
    final newReply = sent.getOrElse((failure) => throw failure).reply;
    final messages = history.getOrElse((failure) => throw failure).items;
    expect(messages.map((message) => message.id), ['user', 'reply']);
    for (final message in [newReply, messages.last]) {
      expect(message.interrupted, isTrue);
      expect(message.groundingStatus, 'grounded');
      expect(message.citations.single.locationNumber, 9);
      expect(message.citations.single.section, 'Summary');
      expect(message.citations.single.excerpt, 'Quoted passage');
    }
  });
}
