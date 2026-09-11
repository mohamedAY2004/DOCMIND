enum MessageSender { user, ai }

enum DeliveryStatus { sent, sending, failed }

class ChatMessage {
  const ChatMessage({
    required this.id,
    required this.content,
    required this.sender,
    required this.timestamp,
    this.isThinking = false,
    this.citations = const [],
    this.generationStatus = 'complete',
    this.groundingStatus,
    this.deliveryStatus = DeliveryStatus.sent,
  });

  final String id;
  final String content;
  final MessageSender sender;
  final DateTime timestamp;
  final bool isThinking;
  final List<Citation> citations;
  final String generationStatus;
  final String? groundingStatus;
  final DeliveryStatus deliveryStatus;
  bool get isUser => sender == MessageSender.user;
  bool get interrupted =>
      generationStatus == 'failed' ||
      generationStatus == 'cancelled' ||
      generationStatus == 'generating';

  ChatMessage withDelivery(DeliveryStatus status) => ChatMessage(
    id: id,
    content: content,
    sender: sender,
    timestamp: timestamp,
    citations: citations,
    generationStatus: generationStatus,
    groundingStatus: groundingStatus,
    deliveryStatus: status,
  );
}

class Citation {
  const Citation({
    required this.id,
    required this.marker,
    required this.sourceKind,
    required this.sourceId,
    required this.sourceName,
    required this.locationType,
    required this.locationNumber,
    required this.excerpt,
    required this.score,
    this.section,
  });
  final String id;
  final int marker;
  final String sourceKind;
  final String sourceId;
  final String sourceName;
  final String locationType;
  final int locationNumber;
  final String? section;
  final String excerpt;
  final double score;
}
