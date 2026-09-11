import 'package:flutter/material.dart';
import '../../../../core/constants/app_assets.dart';
import '../../domain/entities/home_option.dart';

extension HomeOptionStyle on HomeOption {
  String get iconAsset => switch (type) {
    HomeOptionType.chatWithDocuments => AppAssets.documentIcon,
    HomeOptionType.subjectTutors => AppAssets.chatIcon,
    HomeOptionType.profile => AppAssets.personIcon,
  };

  List<Color> get gradientColors => switch (type) {
    HomeOptionType.chatWithDocuments => const [
      Color(0xFF2B7FFF),
      Color(0xFF00B8DB),
    ],
    HomeOptionType.subjectTutors => const [
      Color(0xFFAD46FF),
      Color(0xFFF6339A),
    ],
    HomeOptionType.profile => const [Color(0xFFFF6900), Color(0xFFFB2C36)],
  };
}
