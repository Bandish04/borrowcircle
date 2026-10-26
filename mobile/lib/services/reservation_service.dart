import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'api_service.dart';

class ReservationService {
  static final _storage = const FlutterSecureStorage();

  static Future<Map<String, dynamic>> createReservation({
    required String itemId,
    required String startDate,
    required String endDate,
  }) async {
    // Get the stored JWT token
    String? token = await _storage.read(key: 'access_token');
    
    final response = await http.post(
      Uri.parse('${ApiService.baseUrl}/reservations/'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token', // Crucial for authenticated actions
      },
      body: jsonEncode({
        'item': itemId,
        'start_date': startDate,
        'end_date': endDate,
      }),
    );

    return {
      'statusCode': response.statusCode,
      'body': jsonDecode(response.body),
    };
  }
}