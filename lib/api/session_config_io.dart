import 'package:cookie_jar/cookie_jar.dart';
import 'package:dio/dio.dart';
import 'package:dio_cookie_manager/dio_cookie_manager.dart';

void configureSession(Dio dio) {
  dio.interceptors.add(CookieManager(CookieJar()));
}
