import 'package:flutter_test/flutter_test.dart';
import 'package:career_lens_ai/main.dart';

void main() {
  test('CareerLens exposes all core career tools', () {
    expect(tools.length, 7);
    expect(tools.map((tool) => tool.id), containsAll([
      'ats',
      'cover',
      'interview',
      'skills',
      'roadmap',
      'internship',
      'improve',
    ]));
  });
}
