import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:feather_icons/feather_icons.dart';
import '../theme.dart';
import '../providers/providers.dart';
import 'my_cases_screen.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final TextEditingController _emailController = TextEditingController(text: 'bilal.ahmed@iesco.gov.pk');
  final TextEditingController _passwordController = TextEditingController(text: '••••••••');
  bool _isLoading = false;
  String? _errorMessage;

  void _handleLogin() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      await ref.read(authProvider.notifier).login(
        _emailController.text,
        _passwordController.text,
      );
      if (mounted) {
        Navigator.of(context).pushReplacement(
          MaterialPageRoute(builder: (_) => const MyCasesScreen()),
        );
      }
    } catch (e) {
      setState(() {
        _errorMessage = 'Invalid email or password. Check your details and try again.';
      });
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF1C1A12), // Background approx from CSS
      body: Container(
        decoration: const BoxDecoration(
          gradient: RadialGradient(
            center: Alignment(-0.6, -0.7),
            radius: 1.5,
            colors: [Color(0xFF3A3521), Color(0xFF1C1A12)],
            stops: [0.0, 0.65],
          ),
        ),
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 32.0),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                _buildBrandMark(),
                const SizedBox(height: 12),
                _buildLoginCard(),
                const SizedBox(height: 18),
                Text(
                  'IESCO · Field Inspection Division',
                  style: AppTheme.monoTextStyle.copyWith(
                    fontSize: 10.5,
                    color: const Color(0xFFA49A7C),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildBrandMark() {
    return Container(
      width: 56,
      height: 56,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(15),
        border: Border.all(color: const Color(0xFF5A3216)),
        gradient: const RadialGradient(
          center: Alignment(-0.3, -0.4),
          colors: [AppTheme.copperLight, AppTheme.copper, AppTheme.copperDeep],
          stops: [0.0, 0.55, 1.0],
        ),
        boxShadow: const [
          BoxShadow(
            color: Colors.black45,
            blurRadius: 6,
            offset: Offset(0, 3),
          ),
        ],
      ),
      alignment: Alignment.center,
      child: Text(
        'GG',
        style: AppTheme.monoTextStyle.copyWith(
          color: Colors.white,
          fontSize: 21,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }

  Widget _buildLoginCard() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(24.0),
      decoration: BoxDecoration(
        color: AppTheme.panelRaised,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppTheme.seamDark),
        boxShadow: const [
          BoxShadow(
            color: Colors.black45,
            blurRadius: 45,
            offset: Offset(0, 20),
          ),
        ],
        gradient: const LinearGradient(
          colors: [AppTheme.panelRaised, AppTheme.panelBg],
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const Text(
            'Grid-Guard AI',
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: 19, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 2),
          Text(
            'FIELD INSPECTION APP',
            textAlign: TextAlign.center,
            style: AppTheme.monoTextStyle.copyWith(
              fontSize: 11,
              color: AppTheme.inkSoft,
              letterSpacing: 1.5,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 22),
          if (_errorMessage != null)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
              margin: const EdgeInsets.only(bottom: 14),
              decoration: BoxDecoration(
                color: const Color(0xFFF1DCD8),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: AppTheme.riskHigh),
              ),
              child: Row(
                children: [
                  const Icon(FeatherIcons.alertTriangle, color: AppTheme.riskHighDim, size: 15),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      _errorMessage!,
                      style: const TextStyle(color: AppTheme.riskHighDim, fontSize: 12, fontWeight: FontWeight.bold),
                    ),
                  ),
                ],
              ),
            ),
          _buildField('EMAIL', _emailController, TextInputType.emailAddress),
          const SizedBox(height: 14),
          _buildField('PASSWORD', _passwordController, TextInputType.visiblePassword, obscureText: true),
          const SizedBox(height: 14),
          ElevatedButton(
            onPressed: _isLoading ? null : _handleLogin,
            child: _isLoading 
                ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                : const Text('Sign In'),
          ),
          const SizedBox(height: 12),
          const Text(
            'You\'ll stay signed in on this device.',
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: 11, color: AppTheme.inkFaint),
          ),
        ],
      ),
    );
  }

  Widget _buildField(String label, TextEditingController controller, TextInputType type, {bool obscureText = false}) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, letterSpacing: 0.5, color: AppTheme.inkSoft),
        ),
        const SizedBox(height: 6),
        TextField(
          controller: controller,
          keyboardType: type,
          obscureText: obscureText,
          decoration: const InputDecoration(
            isDense: true,
          ),
        ),
      ],
    );
  }
}
