# SimpleVideoAnnotator

A minimal **Python GUI** for **temporal video annotation** — quickly mark events/segments in a video and export them for downstream analysis.

---

## Features

- Play/pause and scrub through the video timeline  
- Create event **labels** (e.g., “start”, “error”, “goal”, …)  
- Mark **instant** events or **start–end** segments  
- **Export** annotations to file (e.g., CSV) for analysis  
- Lightweight, single-file app: `video_annotator.py`

> Tip: Keeping a consistent schema (e.g., `start_s,end_s,label,notes`) makes it trivial to import the annotations in Python/R/Matlab.

---

## Requirements

- **Python** 3.9+  
- OS video codecs (FFmpeg recommended, especially on Linux)  
- Python packages listed in **`requirements.txt`**

Install dependencies:

```bash
pip install -r requirements.txt
```

> If you run into video loading issues, install FFmpeg and try again. On Windows/macOS many formats work out of the box; FFmpeg broadens support.

---

## Quick Start

```bash
# 1) Clone
git clone https://github.com/gianluca-amprimo/SimpleVideoAnnotator.git
cd SimpleVideoAnnotator

# 2) (Optional) Create a virtual environment
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 3) Install dependencies
pip install -r requirements.txt

# 4) Run the app
python video_annotator.py
```

Then **open a video** from the UI and start annotating.

---

## Project Structure

```
SimpleVideoAnnotator/
├── video_annotator.py   # app entry point
├── requirements.txt     # Python dependencies
└── LICENSE              # license
```

---

## Troubleshooting

- **Video won’t open** → ensure the file plays in a media player; install FFmpeg; try `.mp4`/`.avi`.  
- **Choppy playback** → use a local SSD path; consider a lower-resolution proxy.  
- **Annotations overwritten** → version-control an `annotations/` folder or use unique filenames.

---

## Contributing

Issues and PRs are welcome—small UX improvements (hotkeys, seek/step controls, progress display, “jump to time”) are especially appreciated.

---

## License

This project is released under the **MIT License**. See `LICENSE` for details.
