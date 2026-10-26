import 'package:flutter/material.dart';
import 'package:intl/intl.dart'; // Used for formatting dates
import '../../models/item.dart';
import '../../services/reservation_service.dart';
import '../../theme.dart';

class ReservationScreen extends StatefulWidget {
  final Item item;
  const ReservationScreen({super.key, required this.item});

  @override
  State<ReservationScreen> createState() => _ReservationScreenState();
}

class _ReservationScreenState extends State<ReservationScreen> {
  DateTime? _startDate;
  DateTime? _endDate;
  bool _isLoading = false;

  Future<void> _selectDate(BuildContext context, bool isStart) async {
    final DateTime? picked = await showDatePicker(
      context: context,
      initialDate: DateTime.now(),
      firstDate: DateTime.now(),
      lastDate: DateTime.now().add(const Duration(days: 365)),
    );
    if (picked != null) {
      setState(() {
        if (isStart) {
          _startDate = picked;
          // Ensure end date is not before start date
          if (_endDate != null && _endDate!.isBefore(_startDate!)) {
            _endDate = null;
          }
        } else {
          _endDate = picked;
        }
      });
    }
  }

  Future<void> _confirmReservation() async {
    if (_startDate == null || _endDate == null) return;

    setState(() => _isLoading = true);

    try {
      final response = await ReservationService.createReservation(
        itemId: widget.item.id,
        startDate: DateFormat('yyyy-MM-dd').format(_startDate!),
        endDate: DateFormat('yyyy-MM-dd').format(_endDate!),
      );

      if (!mounted) return;

      if (response['statusCode'] == 201) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Reservation request sent successfully!')),
        );
        Navigator.pop(context); // Go back to details
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed: ${response['body']}')),
        );
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Error connecting to server.')),
      );
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Request to Borrow')),
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          children: [
            ListTile(
              title: Text(_startDate == null ? 'Select Start Date' : DateFormat.yMd().format(_startDate!)),
              trailing: const Icon(Icons.calendar_today),
              onTap: () => _selectDate(context, true),
            ),
            ListTile(
              title: Text(_endDate == null ? 'Select End Date' : DateFormat.yMd().format(_endDate!)),
              trailing: const Icon(Icons.calendar_today),
              onTap: _startDate == null ? null : () => _selectDate(context, false),
            ),
            const SizedBox(height: 32),
            ElevatedButton(
              onPressed: (_startDate != null && _endDate != null && !_isLoading) 
                  ? _confirmReservation : null,
              style: ElevatedButton.styleFrom(
                backgroundColor: BorrowCircleTheme.primary,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(horizontal: 48, vertical: 16),
              ),
              child: _isLoading ? const CircularProgressIndicator(color: Colors.white) : const Text('Confirm Reservation'),
            ),
          ],
        ),
      ),
    );
  }
}