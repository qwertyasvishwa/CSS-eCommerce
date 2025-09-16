# Chat Archive (Flask)

A minimal web app to save prompts and responses and view/export a long-lived document.

## Setup

1. Create a virtual environment (recommended):

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python app.py
```

The app runs at http://localhost:5000

## Features

- Add entries with prompt, response, model, and tags
- Browse and filter entries by text, tag, and date range
- Long document view of all entries in chronological order
- Export all entries as Markdown (`/export.md`) or JSON (`/export.json`)

## Notes

- Data is stored in `chat_archive.sqlite3` in project root.
- To reset data, delete the SQLite file.