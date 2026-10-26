import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'api_service.dart';

class ItemService {
  static final _storage = const FlutterSecureStorage();

  static Future<Map<String, dynamic>> addItem(Map<String, dynamic> itemData) async {
    String? token = await _storage.read(key: 'access_token');
    
    final response = await http.post(
      Uri.parse('${ApiService.baseUrl}/items/'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
      body: jsonEncode(itemData),
    );

    return {
      'statusCode': response.statusCode,
      'body': jsonDecode(response.body),
    };
  }
}