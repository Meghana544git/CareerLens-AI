# CareerLens AI Flutter client

The Flutter UI lives at the repository root and preserves the original Flask API and web frontend.

## Features
- Resume upload: PDF, DOCX, TXT using `/api/resume/upload`
- ATS scoring, cover letters, interview questions, skill-gap analysis, roadmap, internship fit, resume bullet rewriting
- Compare up to five roles, career coach chat, saved jobs
- Responsive desktop/mobile UI and configurable API base URL persisted locally

## Setup
Install Flutter 3.24+ then run from the repository root:

```bash
flutter create --project-name career_lens_ai --platforms android,ios,web,windows,macos,linux .
flutter pub get
flutter run -d chrome
```

The `flutter create` command creates platform runner folders; keep the existing `lib/main.dart` and `pubspec.yaml`.

## Connect the backend
Open Settings in the app and enter the actual running Flask API URL:
- Desktop local: `http://127.0.0.1:5000`
- Android emulator: `http://10.0.2.2:5000`
- Physical phone: `http://YOUR_COMPUTER_LAN_IP:5000`
- Hosted: the real HTTPS URL of the deployed Flask backend

A static frontend URL is not necessarily an API server. Web deployment requires CORS on Flask for the Flutter app origin and session credentials where needed. Keep IBM watsonx API secrets only on the server.
