/// Training lifecycle status for a document chat session.
enum TrainingStatus { initial, uploading, processing, completed, failed }

/// Represents an active document-based AI chat session.
///
/// Each session is built around a single document and one chat thread.
class DocumentChatSession {
  const DocumentChatSession({
    required this.sessionId,
    required this.fileName,
    this.uploadProgress = 0.0,
    this.trainingStatus = TrainingStatus.initial,
  });

  final String sessionId;
  final String fileName;
  final double uploadProgress;
  final TrainingStatus trainingStatus;

  bool get isReadyForChat => trainingStatus == TrainingStatus.completed;

  DocumentChatSession copyWith({
    String? sessionId,
    String? fileName,
    double? uploadProgress,
    TrainingStatus? trainingStatus,
  }) {
    return DocumentChatSession(
      sessionId: sessionId ?? this.sessionId,
      fileName: fileName ?? this.fileName,
      uploadProgress: uploadProgress ?? this.uploadProgress,
      trainingStatus: trainingStatus ?? this.trainingStatus,
    );
  }
}
