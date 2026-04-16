# AI Safe HTML Editor

A lightweight Python desktop editor for XML-style prompt content, built with `pywebview`.

## Overview

This project provides a two-mode editor:

- **True WYSIWYG Mode**: edits rendered prompt content inside a WebView iframe.
- **Safe Structure Mode**: shows a read-only, serialized prompt structure for inspection.

The editor supports loading and saving HTML files, and can insert custom XML tag pairs into the visual editor.

## Requirements

- Python 3.8+
- `pywebview`

Install dependencies with:

```bash
pip install pywebview
```

## Usage

Run the app from the project directory:

```bash
python ai_safe_html_editor.py
```

Or open a specific HTML file:

```bash
python ai_safe_html_editor.py path/to/file.html
```

## Features

- Load/save HTML documents via desktop file dialogs
- Switch between visual editing and safe structure inspection
- Insert custom XML-style tags into the visual prompt editor
- Auto-sync visual edits to the safe structure view

## Notes

- The current implementation is Windows-friendly and targets `pywebview` with WebView2.
- The safe structure view is intended for text-based prompt inspection and preservation of custom tags.

## Git

This repository is linked to `https://github.com/oywino/ai_safe_html_editor.git`.
