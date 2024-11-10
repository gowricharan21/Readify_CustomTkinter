# 📚 Readify - Modern E-book Reader Application

Readify is a **feature-rich, cross-platform e-book reader application** built with Python and Tkinter, designed to support both PDF and text files. It offers an **intuitive interface** with advanced **reading and annotation capabilities** to enhance your reading experience. 🌟

![Readify Logo](./readify.png)

## Features ✨

- **Multi-Format Support** 📄📖
  - 📑 PDF files with zoom capabilities
  - 📜 Text files with wrap text support
  - 🕐 Maintains reading position across sessions

- **Advanced Search Capabilities** 🔍
  - 🖋️ Full-text search with highlighting
  - 🔡 Case-sensitive search option
  - 🔎 Whole word matching
  - 📜 Search history tracking
  - 🚀 Navigation through search results

- **Bookmarking System** 📚
  - ✅ Add/remove bookmarks
  - 📌 Quick navigation through bookmarks
  - 💾 Persistent bookmark storage
  - 🔄 Cross-file bookmark support

- **Annotation System** 📝
  - 🖊️ Create and manage notes
  - 📤 Export annotations to JSON
  - 📂 Organize notes by categories
  - 🗂️ Quick note navigation

- **Reading Progress Tracking** 📊
  - 📅 Reading history
  - 📈 Statistics dashboard
  - 🕹️ Progress indicators
  - 🔄 Recent files tracking

- **User Interface** 🎨
  - 💻 Modern and intuitive design
  - 🌗 Customizable themes (Light/Dark)
  - 🖥️ Responsive layout
  - ⌨️ Keyboard shortcuts
  - 📂 Sidebar for quick access to features

## Usage 📖
Starting the Application

📂 Use Ctrl+O or click the Open button
📚 Supported formats: PDF, TXT
Navigation

⬅️➡️ Left/Right arrows for page navigation
Ctrl++/Ctrl+- for zoom
🔍 Ctrl+F for search
📑 Ctrl+B for bookmarks
Keyboard Shortcuts

🔍 Ctrl+F: Focus search
📂 Ctrl+B: Toggle sidebar
📜 Ctrl+H: Show search history
💾 Ctrl+S: Save current state
🔄 Ctrl+R: Reset view
🌗 Ctrl+T: Toggle theme

## Installation 🚀

### Prerequisites

Make sure you have **Python 3.7 or higher** installed:

```bash
# Check your Python version
python --version
pip install PyMuPDF
pip install Pillow 
pip install customtkinter
pip install PyPDF2

readify/
├── readify.py     # Main application file
├── requirements.txt    # Package dependencies
├── README.md          # Documentation
└── data/              # Configuration files
    ├── bookmarks.json
    └── ebook_reader_data.pkl
