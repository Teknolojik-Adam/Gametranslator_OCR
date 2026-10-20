#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

dotnet build GameTranslatorOCR.sln -c Release --nologo
for rid in linux-x64 win-x64; do
  destination="$ROOT/dist/$rid"
  dotnet publish src/GameTranslatorOCR.Cli/GameTranslatorOCR.Cli.csproj \
    -c Release -r "$rid" --self-contained false -o "$destination" --nologo
  mkdir -p "$destination/models" "$destination/licenses"
  cp -a "$ROOT/models/latin" "$destination/models/"
  cp -a "$ROOT/models/latin-v6-hybrid" "$destination/models/"
  cp -a "$ROOT/licenses/." "$destination/licenses/"
  cp "$ROOT/THIRD_PARTY.md" "$destination/THIRD_PARTY.md"
  echo "Created: $destination"
done

echo "Note: Windows output still needs an actual Windows runtime test."
