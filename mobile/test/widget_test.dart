
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/main.dart';

void main() {
  testWidgets('BorrowCircle app launches successfully', (WidgetTester tester) async {
    await tester.pumpWidget(const BorrowCircleApp());

    expect(find.text('BorrowCircle'), findsOneWidget);
  });
}
