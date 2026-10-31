import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class AppTheme {
  // Colors
  static const Color panelBg = Color(0xFFE9E4D6);
  static const Color panelRaised = Color(0xFFF6F2E7);
  static const Color panelMid = Color(0xFFDDD6C2);
  static const Color panelWell = Color(0xFFD8D0BA);
  static const Color panelWellDk = Color(0xFFC4BB9F);
  static const Color seam = Color(0xFFB7AC8D);
  static const Color seamDark = Color(0xFF8F846A);

  static const Color ink = Color(0xFF2A2418);
  static const Color inkSoft = Color(0xFF665C48);
  static const Color inkFaint = Color(0xFF948A6F);
  static const Color inkInvert = Color(0xFFF6F2E7);

  static const Color copper = Color(0xFFB0632C);
  static const Color copperLight = Color(0xFFD68F52);
  static const Color copperDeep = Color(0xFF7E451E);

  static const Color steel = Color(0xFF3D6A86);
  static const Color steelLight = Color(0xFF6A97B2);
  static const Color steelDeep = Color(0xFF274A5F);

  static const Color riskHigh = Color(0xFFA6392C);
  static const Color riskHighDim = Color(0xFF7C2C22);
  static const Color riskMed = Color(0xFFB17A1C);
  static const Color riskMedDim = Color(0xFF8A5F14);
  static const Color riskLow = Color(0xFF3F6B45);
  static const Color riskLowDim = Color(0xFF2F5133);

  static const Color alertAmber = Color(0xFFC89228);
  static const Color alertAmberDeep = Color(0xFF93690F);
  static const Color alertAmberText = Color(0xFF3A2A08);

  // Spacing
  static const double sp1 = 4.0;
  static const double sp2 = 8.0;
  static const double sp3 = 12.0;
  static const double sp4 = 16.0;
  static const double sp5 = 24.0;
  static const double sp6 = 32.0;
  static const double sp7 = 48.0;
  static const double sp8 = 64.0;

  // Radii
  static const double rPanel = 12.0;
  static const double rBtn = 7.0;
  static const double rChip = 20.0;
  static const double rWell = 8.0;

  // ThemeData
  static ThemeData get themeData {
    return ThemeData(
      scaffoldBackgroundColor: panelBg,
      primaryColor: copper,
      colorScheme: const ColorScheme.light(
        primary: copper,
        secondary: steel,
        error: riskHigh,
        surface: panelRaised,
        onPrimary: Colors.white,
        onSecondary: Colors.white,
        onError: Colors.white,
        onSurface: ink,
      ),
      textTheme: GoogleFonts.ibmPlexSansTextTheme().apply(
        bodyColor: ink,
        displayColor: ink,
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: Color(0xFF221F16), // Linear gradient substitute
        foregroundColor: inkInvert,
        elevation: 0,
        centerTitle: true,
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: copper,
          foregroundColor: Colors.white,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(rBtn),
          ),
          padding: const EdgeInsets.symmetric(vertical: 13, horizontal: 18),
          textStyle: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: inkSoft,
          side: const BorderSide(color: seamDark),
          backgroundColor: panelRaised,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(rBtn),
          ),
          padding: const EdgeInsets.symmetric(vertical: 13, horizontal: 18),
          textStyle: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: panelWell,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8.0),
          borderSide: const BorderSide(color: panelWellDk),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8.0),
          borderSide: const BorderSide(color: panelWellDk),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8.0),
          borderSide: const BorderSide(color: steel),
        ),
        contentPadding: const EdgeInsets.all(13),
      ),
    );
  }

  static TextStyle get urduTextStyle => GoogleFonts.notoNastaliqUrdu();
  static TextStyle get monoTextStyle => GoogleFonts.ibmPlexMono();
}
