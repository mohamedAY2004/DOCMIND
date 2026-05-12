import 'package:flutter/material.dart';
import 'package:get/get.dart';

import '../../../../core/constants/app_colors.dart';
import '../../../../core/theme/theme_service.dart';
import '../controllers/profile_controller.dart';

/// Layout constants matching Figma node 4:900.
const double _appBarHeight = 61.0;
const double _appBarPaddingH = 12.0;
const double _appBarPaddingTop = 12.0;
const double _backButtonSize = 36.0;
const double _contentPaddingH = 16.0;
const double _profileCardRadius = 16.0;
const double _avatarSize = 64.0;
const double _avatarRadius = 24.0;
const double _avatarIconSize = 32.0;
const double _infoIconBoxSize = 28.0;
const double _infoIconBoxRadius = 12.0;
const double _infoIconSize = 12.0;
const double _sectionCardRadius = 16.0;
const double _settingsRowHeight = 60.0;
const double _settingsIconBoxSize = 36.0;
const double _settingsIconBoxRadius = 16.0;
const double _settingsIconSize = 20.0;
const double _signOutCardRadius = 16.0;
const double _signOutCardHeight = 46.0;

/// Profile & Settings page — matching Figma node 4:900.
class ProfilePage extends StatelessWidget {
  const ProfilePage({super.key});

  @override
  Widget build(BuildContext context) {
    final themeService = Get.find<ThemeService>();
    final controller = Get.put(ProfileController());

    // Obx wrapper to rebuild on theme changes
    return Obx(() {
      // Access the reactive variable to register observer
      final isDark = themeService.isDarkMode.value;

      return Scaffold(
        body: Container(
          width: double.infinity,
          height: double.infinity,
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
              colors: [
                AppColors.screenBackgroundGradientTop,
                AppColors.screenBackgroundGradientCenter,
                AppColors.screenBackgroundGradientBottom,
              ],
              stops: [0.0, 0.5, 1.0],
            ),
          ),
          child: Stack(
            children: [
              Column(
                children: [
                  _buildAppBar(context),
                  Expanded(
                    child: SingleChildScrollView(
                      padding: const EdgeInsets.fromLTRB(
                        _contentPaddingH,
                        16,
                        _contentPaddingH,
                        24,
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.center,
                        children: [
                          // Profile card (Figma 4:914)
                          _buildProfileCard(controller),
                          const SizedBox(height: 24),
                          // Settings & Preferences section (Figma 4:979)
                          _buildSettingsSection(controller),
                          const SizedBox(height: 24),
                          // Sign Out button (Figma 4:1034)
                          _buildSignOutButton(controller),
                          const SizedBox(height: 24),
                          // Version footer (Figma 4:1042)
                          _buildVersionFooter(),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      );
    });
  }

  // ── App Bar (Figma 4:905) ────────────────────────────────────────

  Widget _buildAppBar(BuildContext context) {
    final topPadding = MediaQuery.of(context).padding.top;
    final onSurfaceColor = Theme.of(context).colorScheme.onSurface;

    return Container(
      height: _appBarHeight + topPadding,
      padding: EdgeInsets.only(
        top: topPadding + _appBarPaddingTop,
        left: _appBarPaddingH,
        right: _appBarPaddingH,
      ),
      decoration: BoxDecoration(
        color: AppColors.surfaceContainer,
        border: Border(
          bottom: BorderSide(
            color: AppColors.primary.withValues(alpha: 0.2),
            width: 1.275,
          ),
        ),
      ),
      child: Row(
        children: [
          // Back button (Figma 4:907)
          GestureDetector(
            onTap: () => Get.back(),
            child: SizedBox(
              width: _backButtonSize,
              height: _backButtonSize,
              child: Center(
                child: Icon(Icons.arrow_back, color: onSurfaceColor, size: 16),
              ),
            ),
          ),
          const SizedBox(width: 12),
          // Title (Figma 4:911)
          Text(
            'Profile & Settings',
            style: TextStyle(
              color: onSurfaceColor,
              fontSize: 20,
              fontWeight: FontWeight.w400,
              height: 1.5,
            ),
          ),
        ],
      ),
    );
  }

  // ── Profile Card (Figma 4:914) ───────────────────────────────────

  Widget _buildProfileCard(ProfileController controller) {
    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(_profileCardRadius),
        gradient: LinearGradient(
          begin: const Alignment(0.0, -1.0),
          end: const Alignment(0.866, 0.5),
          colors: [
            AppColors.formCardBackground,
            AppColors.formCardBackground.withValues(alpha: 0.6),
          ],
        ),
        border: Border.all(
          color: AppColors.primary.withValues(alpha: 0.2),
          width: 1.275,
        ),
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(_profileCardRadius - 1),
        child: Stack(
          children: [
            Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Avatar + name row (Figma 4:917)
                  Obx(
                    () => Row(
                      children: [
                        // Avatar (Figma 4:918)
                        Container(
                          width: _avatarSize,
                          height: _avatarSize,
                          decoration: BoxDecoration(
                            color: AppColors.primary,
                            borderRadius: BorderRadius.circular(_avatarRadius),
                            boxShadow: [
                              BoxShadow(
                                color: AppColors.primary.withValues(alpha: 0.3),
                                blurRadius: 50,
                                offset: const Offset(0, 25),
                              ),
                            ],
                          ),
                          child: const Center(
                            child: Icon(
                              Icons.person_outline,
                              color: AppColors.white,
                              size: _avatarIconSize,
                            ),
                          ),
                        ),
                        const SizedBox(width: 12),
                        // Name + plan (Figma 4:922)
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                controller.userName.value,
                                style: TextStyle(
                                  color: AppColors.textOnSurface,
                                  fontSize: 14,
                                  fontWeight: FontWeight.w400,
                                  height: 1.43,
                                ),
                              ),
                              const SizedBox(height: 2),
                              Text(
                                controller.userPlan.value,
                                style: TextStyle(
                                  color: AppColors.textSecondary,
                                  fontSize: 12,
                                  fontWeight: FontWeight.w400,
                                  height: 1.33,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                 // const SizedBox(height: 16),
                  // Divider (Figma 4:933)
                 /* Container(
                    height: 1,
                    color: AppColors.primary.withValues(alpha: 0.1),
                  ),
                  const SizedBox(height: 8),*/
                  // Email row (Figma 4:935)
                 /* Obx(
                    () => _buildInfoRow(
                      icon: Icons.mail_outline,
                      text: controller.userEmail.value,
                    ),
                  ),
                  const SizedBox(height: 8),*/
                  // Joined date row (Figma 4:942)
                 /* Obx(
                    () => _buildInfoRow(
                      icon: Icons.calendar_today_outlined,
                      text: controller.joinedDate.value,
                    ),
                  ),*/
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildInfoRow({required IconData icon, required String text}) {
    return Row(
      children: [
        Container(
          width: _infoIconBoxSize,
          height: _infoIconBoxSize,
          decoration: BoxDecoration(
            color: AppColors.primary.withValues(alpha: 0.1),
            borderRadius: BorderRadius.circular(_infoIconBoxRadius),
          ),
          child: Center(
            child: Icon(icon, size: _infoIconSize, color: AppColors.primary),
          ),
        ),
        const SizedBox(width: 8),
        Text(
          text,
          style: TextStyle(
            color: AppColors.textSecondary,
            fontSize: 12,
            fontWeight: FontWeight.w400,
            height: 1.33,
          ),
        ),
      ],
    );
  }

  // ── Settings & Preferences (Figma 4:979) ────────────────────────

  Widget _buildSettingsSection(ProfileController controller) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Section title (Figma 4:980)
        Row(
          children: [
            Icon(
              Icons.settings_outlined,
              size: 12,
              color: AppColors.primary.withValues(alpha: 0.8),
            ),
            const SizedBox(width: 8),
            Text(
              'Settings & Preferences',
              style: TextStyle(
                color: AppColors.textOnSurface,
                fontSize: 14,
                fontWeight: FontWeight.w400,
                height: 1.43,
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        // Settings card (Figma 4:984)
        Container(
          decoration: BoxDecoration(
            color: AppColors.surfaceContainer,
            borderRadius: BorderRadius.circular(_sectionCardRadius),
            border: Border.all(
              color: AppColors.primary.withValues(alpha: 0.2),
              width: 1.275,
            ),
          ),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(_sectionCardRadius - 1),
            child: Obx(
              () => Column(
                children: [
                  // Dark Mode (Figma 4:986)
                  _buildToggleRow(
                    icon: Icons.dark_mode_outlined,
                    title: 'Dark Mode',
                    subtitle: 'Toggle dark/light theme',
                    value: controller.isDarkMode.value,
                    onChanged: controller.toggleDarkMode,
                    showDivider: true,
                  ),
                  // Notifications (Figma 4:999)
                 /* _buildToggleRow(
                    icon: Icons.notifications_outlined,
                    title: 'Notifications',
                    subtitle: 'Manage notification preferences',
                    value: controller.isNotificationsEnabled.value,
                    onChanged: controller.toggleNotifications,
                    showDivider: true,
                  ),*/
                  // Privacy (Figma 4:1013)
                  _buildTappableRow(
                    icon: Icons.shield_outlined,
                    title: 'Privacy',
                    subtitle: 'Privacy and security settings',
                    onTap: controller.onPrivacyTapped,
                    showDivider: true,
                  ),
                  // Help & Support (Figma 4:1023)
                  _buildTappableRow(
                    icon: Icons.help_outline,
                    title: 'Help & Support',
                    subtitle: 'Get help and contact support',
                    onTap: controller.onHelpTapped,
                    showDivider: false,
                  ),
                ],
              ),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildToggleRow({
    required IconData icon,
    required String title,
    required String subtitle,
    required bool value,
    required ValueChanged<bool> onChanged,
    required bool showDivider,
  }) {
    return Column(
      children: [
        SizedBox(
          height: _settingsRowHeight,
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12),
            child: Row(
              children: [
                // Icon box
                Container(
                  width: _settingsIconBoxSize,
                  height: _settingsIconBoxSize,
                  decoration: BoxDecoration(
                    color: AppColors.primary.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(_settingsIconBoxRadius),
                  ),
                  child: Center(
                    child: Icon(
                      icon,
                      size: _settingsIconSize,
                      color: AppColors.primary,
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                // Title + subtitle
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(
                        title,
                        style: TextStyle(
                          color: AppColors.textOnSurface,
                          fontSize: 12,
                          fontWeight: FontWeight.w400,
                          height: 1.33,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        subtitle,
                        style: TextStyle(
                          color: AppColors.textSecondary,
                          fontSize: 12,
                          fontWeight: FontWeight.w400,
                          height: 1.33,
                        ),
                      ),
                    ],
                  ),
                ),
                // Toggle (Figma 4:995)
                Switch(
                  value: value,
                  onChanged: onChanged,
                  activeThumbColor: AppColors.white,
                  activeTrackColor: AppColors.primary,
                  inactiveThumbColor: AppColors.textSecondary,
                  inactiveTrackColor: AppColors.primary.withValues(alpha: 0.2),
                  materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                ),
              ],
            ),
          ),
        ),
        if (showDivider)
          Container(height: 1, color: AppColors.primary.withValues(alpha: 0.1)),
      ],
    );
  }

  Widget _buildTappableRow({
    required IconData icon,
    required String title,
    required String subtitle,
    required VoidCallback onTap,
    required bool showDivider,
  }) {
    return Column(
      children: [
        GestureDetector(
          onTap: onTap,
          child: SizedBox(
            height: _settingsRowHeight,
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12),
              child: Row(
                children: [
                  // Icon box
                  Container(
                    width: _settingsIconBoxSize,
                    height: _settingsIconBoxSize,
                    decoration: BoxDecoration(
                      color: AppColors.primary.withValues(alpha: 0.1),
                      borderRadius: BorderRadius.circular(
                        _settingsIconBoxRadius,
                      ),
                    ),
                    child: Center(
                      child: Icon(
                        icon,
                        size: _settingsIconSize,
                        color: AppColors.primary,
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  // Title + subtitle
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text(
                          title,
                          style: TextStyle(
                            color: AppColors.textOnSurface,
                            fontSize: 12,
                            fontWeight: FontWeight.w400,
                            height: 1.33,
                          ),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          subtitle,
                          style: TextStyle(
                            color: AppColors.textSecondary,
                            fontSize: 12,
                            fontWeight: FontWeight.w400,
                            height: 1.33,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
        if (showDivider)
          Container(height: 1, color: AppColors.primary.withValues(alpha: 0.1)),
      ],
    );
  }

  // ── Sign Out Button (Figma 4:1034) ───────────────────────────────

  Widget _buildSignOutButton(ProfileController controller) {
    return GestureDetector(
      onTap: controller.signOut,
      child: Container(
        height: _signOutCardHeight,
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(_signOutCardRadius),
          gradient: const LinearGradient(
            colors: [
              Color(0x1AD4183D), // rgba(212,24,61,0.1)
              Color(0x0DD4183D), // rgba(212,24,61,0.05)
            ],
          ),
          border: Border.all(
            color: const Color(0xFFD4183D).withValues(alpha: 0.3),
            width: 1.275,
          ),
        ),
        child: const Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.logout, color: Color(0xFFD4183D), size: 16),
            SizedBox(width: 8),
            Text(
              'Sign Out',
              style: TextStyle(
                color: Color(0xFFD4183D),
                fontSize: 14,
                fontWeight: FontWeight.w400,
                height: 1.43,
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ── Version Footer (Figma 4:1042) ────────────────────────────────

  Widget _buildVersionFooter() {
    return Column(
      children: [
        Text(
          'DocMind v1.0.0',
          style: TextStyle(
            color: AppColors.textSecondary,
            fontSize: 16,
            fontWeight: FontWeight.w400,
            height: 1.5,
          ),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 2),
        Text(
          'Powered by Advanced AI',
          style: TextStyle(
            color: AppColors.textSecondary,
            fontSize: 10,
            fontWeight: FontWeight.w400,
            height: 1.5,
          ),
          textAlign: TextAlign.center,
        ),
      ],
    );
  }
}
