# PWAT

## Kanban overload warning animation (MP4)

Generates an **8-second, 1920×1080 MP4** showing a modern hand-drawn Kanban with **too many cards in WIP** and a **flashing red warning light**.

### Prerequisites
- Python 3.10+ (3.8+ often works)
- `ffmpeg` installed and on your PATH

### Render
```bash
chmod +x scripts/render.sh
./scripts/render.sh
```

Output: `output/kanban_warning.mp4`
