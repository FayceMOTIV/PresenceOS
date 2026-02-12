#!/bin/bash
# PresenceOS - Music Library Setup (Sprint 9C)
#
# Creates the directory structure for CC0/royalty-free music tracks.
# Place your .mp3/.wav files in the appropriate mood directories.
#
# Usage:
#   chmod +x scripts/setup_music_library.sh
#   ./scripts/setup_music_library.sh [base_path]

set -e

BASE_PATH="${1:-/data/music}"

echo "🎵 Setting up PresenceOS Music Library at: $BASE_PATH"
echo ""

# Create mood directories
MOODS=(
    "energetic"
    "chill"
    "inspiring"
    "dramatic"
    "happy"
    "corporate"
    "ambient"
    "trendy"
)

for mood in "${MOODS[@]}"; do
    mkdir -p "$BASE_PATH/$mood"
    echo "  Created: $BASE_PATH/$mood"
done

# Create README
cat > "$BASE_PATH/README.md" << 'EOF'
# PresenceOS Music Library

Place CC0/royalty-free music tracks in the appropriate mood directories.

## Mood Directories

| Directory   | Description                          | Use Case                    |
|-------------|--------------------------------------|-----------------------------|
| energetic/  | Upbeat, high-energy tracks           | Fitness, sports, action     |
| chill/      | Relaxed, calm tracks                 | Food, lifestyle, nature     |
| inspiring/  | Motivational, uplifting tracks       | Success stories, growth     |
| dramatic/   | Cinematic, intense tracks            | Reveals, transformations    |
| happy/      | Fun, cheerful tracks                 | Celebrations, events        |
| corporate/  | Professional, neutral tracks         | Business, SaaS content      |
| ambient/    | Background, subtle tracks            | Minimal, abstract content   |
| trendy/     | Modern, TikTok-style tracks          | Fashion, viral content      |

## Supported Formats

- MP3 (.mp3)
- WAV (.wav)
- OGG (.ogg)
- AAC (.aac)

## Sources for CC0 Music

- https://pixabay.com/music/
- https://freesound.org
- https://incompetech.com
- https://www.bensound.com (some CC0)

## Notes

- Keep tracks between 15-120 seconds for best results
- Loops work best for background music
- The system will automatically select mood based on content AI analysis
EOF

echo ""
echo "Music library structure created."
echo ""
echo "Next steps:"
echo "  1. Add CC0 music files to the mood directories"
echo "  2. Set MUSIC_LIBRARY_PATH=$BASE_PATH in your .env"
echo "  3. Restart the backend"
echo ""
echo "Recommended sources:"
echo "  - https://pixabay.com/music/"
echo "  - https://freesound.org"
echo "  - https://incompetech.com"
