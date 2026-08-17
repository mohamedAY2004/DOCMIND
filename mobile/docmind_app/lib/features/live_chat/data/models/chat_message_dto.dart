class ChatMessageDto {
  const ChatMessageDto({
    required this.id,
    required this.role,
    required this.text,
    required this.createdAt,
    this.citations = const [],
    this.generationStatus = 'complete',
    this.groundingStatus,
  });

  final String id;
  final String role;
  final String text;
  final DateTime createdAt;
  final List<CitationDto> citations;
  final String generationStatus;
  final String? groundingStatus;

  factory ChatMessageDto.fromJson(Map<String, dynamic> json) {
    return ChatMessageDto(
      id: json['id'] as String? ?? '',
      role: json['role'] as String? ?? '',
      text: json['text'] as String? ?? '',
      createdAt: DateTime.tryParse(json['createdAt'] as String? ?? '') ??
          DateTime.now(),
      citations: (json['citations'] as List<dynamic>? ?? const [])
          .whereType<Map<String, dynamic>>()
          .map(CitationDto.fromJson)
          .toList(growable: false),
      generationStatus: json['generationStatus'] as String? ?? 'complete',
      groundingStatus: json['groundingStatus'] as String?,
    );
  }
}

class CitationDto {
  const CitationDto({
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

  factory CitationDto.fromJson(Map<String, dynamic> json) {
    final location = json['location'] as Map<String, dynamic>? ?? const {};
    return CitationDto(
      id: json['id'] as String? ?? '',
      marker: (json['marker'] as num?)?.toInt() ?? 0,
      sourceKind: json['sourceKind'] as String? ?? '',
      sourceId: json['sourceId'] as String? ?? '',
      sourceName: json['sourceName'] as String? ?? '',
      locationType: location['type'] as String? ?? 'chunk',
      locationNumber: (location['number'] as num?)?.toInt() ?? 0,
      section: json['section'] as String?,
      excerpt: json['excerpt'] as String? ?? '',
      score: (json['score'] as num?)?.toDouble() ?? 0,
    );
  }
}
