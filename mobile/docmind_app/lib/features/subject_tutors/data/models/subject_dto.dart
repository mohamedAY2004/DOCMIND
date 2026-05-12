class SubjectDto {
  const SubjectDto({
    required this.id,
    required this.title,
    required this.description,
    required this.courseCode,
    required this.semesterId,
    required this.pdfCount,
    required this.instructorIds,
    required this.studentIds,
    required this.studentCount,
  });

  final String id;
  final String title;
  final String description;
  final String courseCode;
  final String semesterId;
  final String pdfCount;
  final List<String> instructorIds;
  final List<String> studentIds;
  final int studentCount;

  factory SubjectDto.fromJson(Map<String, dynamic> json) {
    return SubjectDto(
      id: json['id'] as String? ?? '',
      title: json['title'] as String? ?? '',
      description: json['description'] as String? ?? '',
      courseCode: json['courseCode'] as String? ?? '',
      semesterId: json['semesterId'] as String? ?? '',
      pdfCount: json['pdfCount'] as String? ?? '',
      instructorIds: (json['instructorIds'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          const [],
      studentIds: (json['studentIds'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          const [],
      studentCount: json['studentCount'] as int? ?? 0,
    );
  }
}
