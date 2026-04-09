# dupeGuru - Web Evolution

![Project Banner](https://img.shields.io/badge/dupeGuru-v4.0.0_Web-blue?style=for-the-badge&logo=python&logoColor=white)
![Stack](https://img.shields.io/badge/FLASK-000000?style=for-the-badge&logo=flask&logoColor=white)
![UI](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)

**dupeGuru** is a powerful cross-platform tool to find duplicate files on your system. This version represents a complete architectural overhaul, evolving from a legacy desktop application into a lean, headless web service with a premium, state-of-the-art interface.

## 🚀 The Web Evolution

We've stripped away the PyQt dependencies and legacy GUI code to create a modern, high-performance web experience.

*   **Headless Architecture**: The core engine now runs as a Flask-based backend, making it deployable on servers or locally.
*   **Premium Interface**: A stunning dark-mode UI built with TailwindCSS, featuring glassmorphism, fluid animations, and a focus on visual clarity.
*   **Dynamic Workflows**: Real-time folder management, interactive cluster galleries, and instant similarity adjustments.
*   **Audit-Ready**: Integrated Excel reporting for safe, documented duplicate management.

## 🧠 Advanced Scanning Engines

dupeGuru features three specialized modes, each equipped with industry-leading algorithms:

### 📸 Picture Mode (Visual Analysis)
*   **Fuzzy Block**: Advanced block-based visual comparison.
*   **Perceptual Hash (pHash)**: Semantic hashing that ignores scaling and minor edits.
*   **Difference Hash (dHash)**: High-speed gradient-based matching.
*   **Average Hash (aHash)**: Optimized visual analysis for large collections.
*   **Histogram Comparison**: Deep color-distribution analysis.
*   **EXIF Metadata**: Precise matching based on camera timestamps.

### 🎵 Music Mode (Acoustic & Tag Analysis)
*   **Audio Fingerprinting**: Powered by **Chromaprint** for content-based identification regardless of file name.
*   **Tag Matching**: Deep analysis of Artist, Album, and Title metadata.

### 📄 Standard Mode (Files & Folders)
*   **Byte-for-byte**: Guaranteed exact matches using MD5/SHA-1 hashing.
*   **Filename/Folder Logic**: Smart heuristic matching for file and directory names.

## 🛠️ Technical Stack

*   **Backend**: Python 3.10+ / Flask
*   **Frontend**: HTML5 / ES6+ JavaScript / TailwindCSS
*   **Storage**: SQLite (High-speed hashing cache)
*   **Safety**: `send2trash` integration for non-destructive deletion.

## 🏁 Getting Started

### Prerequisites
*   Python 3.10 or higher.
*   `pip` for dependency management.

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/manrajidevi91/dupeguru.git
   cd dupeguru
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the App
Launch the web server:
```bash
python app.py
```
Or use the provided batch file on Windows:
```bash
run.bat
```

Open your browser and navigate to:
**`http://localhost:5010`**

## 📂 Project Structure

*   `app.py`: The Flask entry point and RESTful API layer.
*   `core/`: Optimized scanning logic (ported from original dupeGuru).
*   `templates/`: Modern web frontend components.
*   `hscommon/`: Shared utility libraries for cross-toolkit compatibility.

---
*Maintained with ❤️ for the next generation of file management.*
