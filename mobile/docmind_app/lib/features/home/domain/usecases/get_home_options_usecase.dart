import '../entities/home_option.dart';

/// Returns the list of [HomeOption]s for the home screen.
///
/// This is the **single source of truth** for which features appear on
/// the Home screen.  All business logic lives here — neither the
/// controller nor the UI should contain user-type conditionals.
class GetHomeOptionsUseCase {
  /// Execute the use case.
  List<HomeOption> call() {
    final options = <HomeOption>[
      const HomeOption(
        id: 'chat_with_documents',
        title: 'Chat with Documents',
        subtitle: 'Upload and chat with your study materials',
        type: HomeOptionType.chatWithDocuments,
      ),
    ];

    options.add(
      const HomeOption(
        id: 'subject_tutors',
        title: 'AI Subject Tutors',
        subtitle: 'Get help from specialized AI tutors',
        type: HomeOptionType.subjectTutors,
      ),
    );

    options.add(
      const HomeOption(
        id: 'profile',
        title: 'Your Profile',
        subtitle: 'Settings, stats, and preferences',
        type: HomeOptionType.profile,
      ),
    );

    return options;
  }
}
