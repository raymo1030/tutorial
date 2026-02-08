# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A simple ToDo/Schedule management application with priority-based sorting. The app has two interfaces sharing the same data layer.

## Running the Application

```bash
# CLI interface
python now_time.py

# Streamlit web interface
streamlit run schedule_popup.py
```

## Dependencies

- Python 3.x
- Streamlit (for web UI only)

## Architecture

- **now_time.py** - CLI interface and core data functions (`load_schedule`, `save_schedule`, `sort_by_priority`)
- **schedule_popup.py** - Streamlit web UI that imports data functions from `now_time.py`
- **schedule.json** - JSON data storage for todos

### Data Format

Each todo item has:
- `title`: string
- `priority`: 1 (Low), 2 (Medium), 3 (High)
- `created_at`: ISO 8601 timestamp

Items are sorted by priority (highest first), then by creation date (oldest first).
