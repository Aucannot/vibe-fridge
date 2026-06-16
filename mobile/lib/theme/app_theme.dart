import 'package:flutter/material.dart';

class AppColors {
  static const primary = Color(0xFF7A8F6A);
  static const primaryDark = Color(0xFF5E6F54);
  static const secondary = Color(0xFF8B9466);
  static const accent = Color(0xFFB7A7D6);
  static const success = Color(0xFF7A8F6A);
  static const warning = Color(0xFFF4A261);
  static const error = Color(0xFFE57373);
  static const background = Color(0xFFFAF7F1);
  static const surface = Color(0xFFFFFFFF);
  static const surfaceWarm = Color(0xFFFFFDF8);
  static const surfaceVariant = Color(0xFFF4EEE4);
  static const textPrimary = Color(0xFF2B2A24);
  static const textSecondary = Color(0xFF68645C);
  static const textHint = Color(0xFF9C968B);
  static const divider = Color(0xFFE8DED1);
  static const warningContainer = Color(0xFFFFE5B8);
  static const errorContainer = Color(0xFFFFE3DF);
  static const successContainer = Color(0xFFE4EDDD);
  static const primaryContainer = Color(0xFFE5F1D9);
  static const secondaryContainer = Color(0xFFF0ECD4);
  static const accentContainer = Color(0xFFEDE7F7);
}

class AppSpacing {
  static const pageHorizontal = 20.0;
  static const pageBottom = 24.0;
  static const pageTopCompact = 8.0;
  static const pageTopComfortable = 12.0;
  static const sectionGap = 20.0;
  static const cardGap = 12.0;
  static const fieldGap = 14.0;
  static const cardPadding = 16.0;
  static const compactPadding = 12.0;

  static const pageListPadding = EdgeInsets.only(bottom: pageBottom);
  static const detailListPadding = EdgeInsets.fromLTRB(
    pageHorizontal,
    pageTopCompact,
    pageHorizontal,
    pageBottom,
  );
  static const reviewListPadding = EdgeInsets.fromLTRB(
    pageHorizontal,
    pageTopComfortable,
    pageHorizontal,
    pageBottom,
  );
}

class AppRadii {
  static const small = 10.0;
  static const medium = 14.0;
  static const card = 20.0;
  static const large = 24.0;
  static const pill = 999.0;
}

class AppSizes {
  static const controlHeight = 48.0;
  static const iconContainer = 36.0;
  static const emptyIconContainer = 54.0;
  static const navigationBarHeight = 72.0;
}

class AppBreakpoints {
  static const contentMaxWidth = 960.0;
  static const wideGrid = 720.0;
}

class AppShadows {
  static const card = [
    BoxShadow(
      color: Color(0x0F5E4B2E),
      blurRadius: 22,
      offset: Offset(0, 12),
    ),
    BoxShadow(
      color: Color(0x0AE6D2B8),
      blurRadius: 2,
      offset: Offset(0, 1),
    ),
  ];
}

class AppTheme {
  static const supportsDarkMode = false;

  static ThemeData light() {
    final colorScheme = ColorScheme.fromSeed(
      seedColor: AppColors.primary,
      brightness: Brightness.light,
      primary: AppColors.primary,
      secondary: AppColors.secondary,
      tertiary: AppColors.accent,
      error: AppColors.error,
      surface: AppColors.surface,
    );

    return ThemeData(
      useMaterial3: true,
      colorScheme: colorScheme,
      scaffoldBackgroundColor: AppColors.background,
      fontFamilyFallback: const [
        'PingFang SC',
        'Noto Sans CJK SC',
        'Microsoft YaHei',
        'Roboto',
      ],
      appBarTheme: const AppBarTheme(
        centerTitle: false,
        elevation: 0,
        backgroundColor: AppColors.background,
        foregroundColor: AppColors.textPrimary,
        surfaceTintColor: Colors.transparent,
      ),
      cardTheme: CardThemeData(
        color: AppColors.surface,
        elevation: 0,
        margin: EdgeInsets.zero,
        shadowColor: const Color(0x1A5E4B2E),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppRadii.card),
          side: const BorderSide(color: AppColors.divider),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: AppColors.surfaceWarm,
        contentPadding:
            const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppRadii.medium),
          borderSide: const BorderSide(color: AppColors.divider),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppRadii.medium),
          borderSide: const BorderSide(color: AppColors.divider),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppRadii.medium),
          borderSide: const BorderSide(color: AppColors.primary, width: 1.5),
        ),
      ),
      navigationBarTheme: NavigationBarThemeData(
        height: AppSizes.navigationBarHeight,
        backgroundColor: AppColors.surfaceWarm,
        indicatorColor: AppColors.primaryContainer,
        labelTextStyle: WidgetStateProperty.resolveWith((states) {
          final selected = states.contains(WidgetState.selected);
          return TextStyle(
            color: selected ? AppColors.primary : AppColors.textSecondary,
            fontSize: 12,
            fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
          );
        }),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: AppColors.primaryDark,
          foregroundColor: AppColors.surface,
          minimumSize: const Size(
            AppSizes.controlHeight,
            AppSizes.controlHeight,
          ),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(AppRadii.medium),
          ),
          textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          minimumSize: const Size(
            AppSizes.controlHeight,
            AppSizes.controlHeight,
          ),
          foregroundColor: AppColors.primary,
          side: const BorderSide(color: AppColors.divider),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(AppRadii.medium),
          ),
        ),
      ),
      chipTheme: ChipThemeData(
        backgroundColor: AppColors.surface,
        selectedColor: AppColors.primaryContainer,
        side: const BorderSide(color: AppColors.divider),
        labelStyle: const TextStyle(color: AppColors.textSecondary),
        secondaryLabelStyle: const TextStyle(
          color: AppColors.primary,
          fontWeight: FontWeight.w700,
        ),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppRadii.pill),
        ),
      ),
      snackBarTheme: SnackBarThemeData(
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppRadii.medium),
        ),
      ),
    );
  }
}
