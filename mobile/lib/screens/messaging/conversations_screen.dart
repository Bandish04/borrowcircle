import 'package:flutter/material.dart';
import '../../services/messaging_service.dart';
import '../../theme.dart';
import 'chat_screen.dart'; // We will create this screen in the next step

class ConversationsScreen extends StatefulWidget {
  const ConversationsScreen({super.key});

  @override
  State<ConversationsScreen> createState() => _ConversationsScreenState();
}

class _ConversationsScreenState extends State<ConversationsScreen> {
  late Future<List<dynamic>> _conversationsFuture;

  @override
  void initState() {
    super.initState();
    _conversationsFuture = MessagingService.getConversations();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Messages')),
      body: FutureBuilder<List<dynamic>>(
        future: _conversationsFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          } else if (snapshot.hasError) {
            return Center(child: Text('Error: ${snapshot.error}'));
          } else if (!snapshot.hasData || snapshot.data!.isEmpty) {
            return const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.chat_bubble_outline, size: 64, color: Colors.grey),
                  SizedBox(height: 16),
                  Text('No conversations yet.', style: TextStyle(color: Colors.grey)),
                ],
              ),
            );
          }

          final conversations = snapshot.data!;
          return ListView.builder(
            itemCount: conversations.length,
            itemBuilder: (context, index) {
              final chat = conversations[index];
              final otherUser = chat['participant_one_username'] ?? 'User';

              return ListTile(
                leading: const CircleAvatar(
                  backgroundColor: BorrowCircleTheme.primary,
                  child: Icon(Icons.person, color: Colors.white),
                ),
                title: Text('Chat with $otherUser', style: const TextStyle(fontWeight: FontWeight.bold)),
                subtitle: Text('Reservation ID: ${chat['reservation']}'),
                trailing: const Icon(Icons.chevron_right),
                onTap: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (context) => ChatScreen(conversation: chat),
                    ),
                  );
                },
              );
            },
          );
        },
      ),
    );
  }
}