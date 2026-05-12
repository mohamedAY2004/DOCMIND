/// Asset path constants for images and icons.
abstract final class AppAssets {
  AppAssets._();

  static const String _images = 'assets/images';
  static const String _icons = 'assets/icons';
  static const String _logo = 'assets/logo';

  /// Splash / app logo from Figma (DocMind Mobile, node 5-2612).
  /// Export as PNG from Figma and save as logo.png here.
  static const String splashLogo = '$_images/logo.png';
  static const String appLogo = '$_images/logo.png';
  static const String splashScreen = '$_images/splash.png';

  static const String docmindLogo = '$_logo/app_logo.png';
  static const String uniIcon = '$_icons/uni_icon.png';
  static const String userIdIcon = '$_icons/user_id.svg';
  static const String lockIcon = '$_icons/lock_icon.svg';
  static const String starIcon = '$_icons/star_icon.png';
  static const String documentIcon = '$_icons/document_icon.png';
  static const String personIcon = '$_icons/person_icon.png';
  static const String chatIcon = '$_icons/chat_icon.png';
}
