import 'package:flutter/material.dart';
import '../../services/item_service.dart';
import '../../services/marketplace_service.dart';
import '../../theme.dart';

class AddItemScreen extends StatefulWidget {
  const AddItemScreen({super.key});

  @override
  State<AddItemScreen> createState() => _AddItemScreenState();
}

class _AddItemScreenState extends State<AddItemScreen> {
  final _formKey = GlobalKey<FormState>();
  final _titleController = TextEditingController();
  final _descriptionController = TextEditingController();
  final _depositController = TextEditingController();
  final _pickupAreaController = TextEditingController();
  final _maxDaysController = TextEditingController(text: '14');

  List<dynamic> _categories = [];
  String? _selectedCategoryId;
  String _selectedCondition = 'good';
  bool _isLoading = false;
  bool _isFetchingCategories = true;

  @override
  void initState() {
    super.initState();
    _loadCategories();
  }

  Future<void> _loadCategories() async {
    try {
      final categories = await MarketplaceService.fetchCategories();
      setState(() {
        _categories = categories;
        if (categories.isNotEmpty) {
          _selectedCategoryId = categories[0]['id'].toString();
        }
        _isFetchingCategories = false;
      });
    } catch (e) {
      setState(() => _isFetchingCategories = false);
    }
  }

  @override
  void dispose() {
    _titleController.dispose();
    _descriptionController.dispose();
    _depositController.dispose();
    _pickupAreaController.dispose();
    _maxDaysController.dispose();
    super.dispose();
  }

  Future<void> _handleSubmit() async {
    if (!_formKey.currentState!.validate() || _selectedCategoryId == null) return;

    setState(() => _isLoading = true);

    try {
      final response = await ItemService.addItem({
        'title': _titleController.text.trim(),
        'description': _descriptionController.text.trim(),
        'deposit_amount': double.tryParse(_depositController.text.trim()) ?? 0.0,
        'pickup_area': _pickupAreaController.text.trim(),
        'max_loan_days': int.tryParse(_maxDaysController.text.trim()) ?? 14,
        'condition': _selectedCondition,
        'category': _selectedCategoryId,
      });

      if (!mounted) return;

      if (response['statusCode'] == 201) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Item listed successfully!')),
        );
        Navigator.pop(context); // Go back to home
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed: ${response['body']}')),
        );
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('An error occurred. Check your connection.')),
      );
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('List an Item for Sharing')),
      body: _isFetchingCategories
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(24.0),
              child: Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    // Title
                    TextFormField(
                      controller: _titleController,
                      decoration: const InputDecoration(labelText: 'Item Title', border: OutlineInputBorder()),
                      validator: (value) => value!.isEmpty ? 'Please enter a title' : null,
                    ),
                    const SizedBox(height: 16),

                    // Category Dropdown
                    DropdownButtonFormField<String>(
                      value: _selectedCategoryId,
                      decoration: const InputDecoration(labelText: 'Category', border: OutlineInputBorder()),
                      items: _categories.map<DropdownMenuItem<String>>((cat) {
                        return DropdownMenuItem<String>(
                          value: cat['id'].toString(),
                          child: Text(cat['name']),
                        );
                      }).toList(),
                      onChanged: (val) => setState(() => _selectedCategoryId = val),
                    ),
                    const SizedBox(height: 16),

                    // Condition Dropdown
                    DropdownButtonFormField<String>(
                      value: _selectedCondition,
                      decoration: const InputDecoration(labelText: 'Condition', border: OutlineInputBorder()),
                      items: const [
                        DropdownMenuItem(value: 'new', child: Text('New')),
                        DropdownMenuItem(value: 'good', child: Text('Good')),
                        DropdownMenuItem(value: 'fair', child: Text('Fair')),
                        DropdownMenuItem(value: 'worn', child: Text('Worn')),
                      ],
                      onChanged: (val) => setState(() => _selectedCondition = val!),
                    ),
                    const SizedBox(height: 16),

                    // Deposit Amount
                    TextFormField(
                      controller: _depositController,
                      keyboardType: TextInputType.number,
                      decoration: const InputDecoration(labelText: 'Security Deposit (\$)', border: OutlineInputBorder()),
                      validator: (value) => value!.isEmpty ? 'Please enter a deposit amount' : null,
                    ),
                    const SizedBox(height: 16),

                    // Pickup Area
                    TextFormField(
                      controller: _pickupAreaController,
                      decoration: const InputDecoration(labelText: 'Pickup Area / Neighborhood', border: OutlineInputBorder()),
                      validator: (value) => value!.isEmpty ? 'Please enter a pickup area' : null,
                    ),
                    const SizedBox(height: 16),

                    // Max Loan Days
                    TextFormField(
                      controller: _maxDaysController,
                      keyboardType: TextInputType.number,
                      decoration: const InputDecoration(labelText: 'Max Loan Duration (Days)', border: OutlineInputBorder()),
                    ),
                    const SizedBox(height: 16),

                    // Description
                    TextFormField(
                      controller: _descriptionController,
                      maxLines: 4,
                      decoration: const InputDecoration(labelText: 'Description', border: OutlineInputBorder()),
                      validator: (value) => value!.isEmpty ? 'Please enter a description' : null,
                    ),
                    const SizedBox(height: 24),

                    // Submit Button
                    ElevatedButton(
                      onPressed: _isLoading ? null : _handleSubmit,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: BorrowCircleTheme.primary,
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(vertical: 16),
                      ),
                      child: _isLoading
                          ? const CircularProgressIndicator(color: Colors.white)
                          : const Text('Publish Item', style: TextStyle(fontSize: 16)),
                    ),
                  ],
                ),
              ),
            ),
    );
  }
}