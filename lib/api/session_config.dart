import 'package:dio/dio.dart';
import 'session_config_io.dart'
    if (dart.library.js_interop) 'session_config_web.dart' as platform;

void configureSession(Dio dio) => platform.configureSession(dio);
