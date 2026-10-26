import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'api_service.dart';

class MessagingService {
  static final _storage = const FlutterSecureStorage();

  // Fetch all conversations for the logged-in user
  static Future<List<dynamic>> getConversations() async {
    String? token = await _storage.read(key: 'access_token');
    
    final response = await http.get(
      Uri.parse('${ApiService.baseUrl}/messaging/conversations/'),
      headers: {'Authorization': 'Bearer $token'},
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Failed to load conversations');
    }
  }

  // Send a message inside a conversation
  static Future<Map<String, dynamic>> sendMessage({
    required String conversationId,
    required String body,
  }) async {
    String? token = await _storage.read(key: 'access_token');

    final response = await http.post(
      Uri.parse('${ApiService.baseUrl}/messaging/messages/'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
      body: jsonEncode({
        'conversation': conversationId,
        'body': body,
      }),
    );

    return {
      'statusCode': response.statusCode,
      'body': jsonDecode(response.body),
    };
  }
}