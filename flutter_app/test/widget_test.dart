import 'package:flutter_test/flutter_test.dart';

import 'package:seat_card_app/main.dart';

void main() {
  testWidgets('App renders smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(const SeatCardApp());
    expect(find.text('席卡生成系统'), findsOneWidget);
  });
}
