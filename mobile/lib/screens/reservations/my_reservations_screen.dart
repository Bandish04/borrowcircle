import 'package:flutter/material.dart';
import '../../services/reservation_service.dart';
import '../../theme.dart';

class MyReservationsScreen extends StatefulWidget {
  const MyReservationsScreen({super.key});

  @override
  State<MyReservationsScreen> createState() => _MyReservationsScreenState();
}

class _MyReservationsScreenState extends State<MyReservationsScreen> {
  late Future<List<dynamic>> _reservationsFuture;

  @override
  void initState() {
    super.initState();
    _reservationsFuture = ReservationService.getMyReservations();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('My Reservations')),
      body: FutureBuilder<List<dynamic>>(
        future: _reservationsFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          } else if (snapshot.hasError) {
            return Center(child: Text('Error: ${snapshot.error}'));
          } else if (!snapshot.hasData || snapshot.data!.isEmpty) {
            return const Center(child: Text('No reservations found.'));
          }

          final reservations = snapshot.data!;
          return ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: reservations.length,
            itemBuilder: (context, index) {
              final res = reservations[index];
              return Card(
                margin: const EdgeInsets.only(bottom: 12),
                child: ListTile(
                  title: Text(res['item_title'] ?? 'Item'), // Assuming backend sends item_title
                  subtitle: Text('Dates: ${res['start_date']} to ${res['end_date']}'),
                  trailing: Chip(
                    label: Text(res['status'] ?? 'Pending'),
                    backgroundColor: _getStatusColor(res['status']),
                  ),
                ),
              );
            },
          );
        },
      ),
    );
  }

  Color _getStatusColor(String? status) {
    switch (status) {
      case 'approved': return Colors.green.shade100;
      case 'rejected': return Colors.red.shade100;
      default: return Colors.orange.shade100;
    }
  }
}