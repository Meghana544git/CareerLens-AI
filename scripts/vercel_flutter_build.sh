#!/usr/bin/env bash
set -euo pipefail

# Build the Flutter web client in Vercel's build container.
# Keep the SDK outside the repository so build output stays in build/web.
FLUTTER_PARENT="/tmp/careerlens-flutter-sdk"
FLUTTER_BIN="$FLUTTER_PARENT/flutter/bin"
META_FILE="/tmp/careerlens-flutter-releases.json"

if [ ! -x "$FLUTTER_BIN/flutter" ]; then
  mkdir -p "$FLUTTER_PARENT"
  echo "Downloading Flutter stable SDK metadata..."
  curl --fail --silent --show-error --location \
    "https://storage.googleapis.com/flutter_infra_release/releases/releases_linux.json" \
    --output "$META_FILE"

  ARCHIVE_PATH="$(python3 - <<'PY'
import json
from pathlib import Path
data = json.loads(Path("/tmp/careerlens-flutter-releases.json").read_text())
stable = [item for item in data["releases"] if item.get("channel") == "stable" and item.get("archive")]
stable.sort(key=lambda item: item.get("release_date", ""), reverse=True)
if not stable:
    raise SystemExit("No stable Flutter Linux SDK release was found.")
print(stable[0]["archive"])
PY
)"
  echo "Downloading Flutter SDK: $ARCHIVE_PATH"
  curl --fail --silent --show-error --location \
    "https://storage.googleapis.com/flutter_infra_release/releases/$ARCHIVE_PATH" \
    --output /tmp/careerlens-flutter-sdk.tar.xz
  tar -xJf /tmp/careerlens-flutter-sdk.tar.xz -C "$FLUTTER_PARENT"
  rm -f /tmp/careerlens-flutter-sdk.tar.xz "$META_FILE"
fi

export PATH="$FLUTTER_BIN:$PATH"
export CI=true
flutter --version
flutter pub get
flutter build web --release --base-href /
