import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../models/case_model.dart';
import '../models/inspection.dart';
import '../models/user.dart';

class ApiClient {
  // Change this to your machine's local IP if running on a real device
  // e.g. 'http://192.168.x.x:8000' — use localhost only for emulators
  static const String baseUrl = 'http://10.0.2.2:8000';

  Future<String?> _getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('jwt_token');
  }

  Future<Map<String, String>> _getHeaders() async {
    final token = await _getToken();
    if (token != null) {
      return {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      };
    }
    return {'Content-Type': 'application/json'};
  }

  Future<User?> login(String email, String password) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/login'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email, 'password': password}),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('jwt_token', data['token']);
      final userJson = data['user'];
      return User(
        id: userJson['id'].toString(),
        name: userJson['name'],
        role: userJson['role'],
        email: userJson['email'],
      );
    } else {
      final err = jsonDecode(response.body);
      throw Exception(err['detail'] ?? 'Invalid email or password. Check your details and try again.');
    }
  }

  Future<List<CaseModel>> getMyCases() async {
    final headers = await _getHeaders();
    final response = await http.get(Uri.parse('$baseUrl/cases/mine'), headers: headers);

    if (response.statusCode == 200) {
      final Map<String, dynamic> body = jsonDecode(response.body);
      // Backend returns a paginated wrapper: { items: [...], total, page, ... }
      final List<dynamic> items = body['items'] ?? [];
      return items.map((json) => CaseModel.fromListJson(json)).toList();
    } else {
      throw Exception('Failed to load cases (${response.statusCode})');
    }
  }

  Future<void> submitInspection(Inspection inspection) async {
    final headers = await _getHeaders();
    
    // For photo, we'd use a MultipartRequest, but for this mock setup we use standard post
    final response = await http.post(
      Uri.parse('$baseUrl/cases/${inspection.caseId}/inspection'),
      headers: headers,
      body: jsonEncode(inspection.toJson()),
    );

    if (response.statusCode != 200 && response.statusCode != 201) {
      throw Exception('Failed to submit inspection');
    }
  }
}
