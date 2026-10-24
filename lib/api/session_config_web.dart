import 'package:dio/browser.dart';
import 'package:dio/dio.dart';

void configureSession(Dio dio) {
  final adapter = BrowserHttpClientAdapter()..withCredentials = true;
  dio.httpClientAdapter = adapter;
}
