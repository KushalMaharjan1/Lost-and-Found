# Lost & Found Management System

A Django web application for reporting, browsing, editing, and resolving lost and found items on campus. Records are stored in a CSV file (kept in sync with a JSON copy) and rendered through a simple, card-based dashboard.

## Features

- Home dashboard with live statistics (total, lost, found, resolved items)
- Browse Items page with search (by title/location) and status filtering
- Report an Item — add a new lost or found record
- Edit an existing item's details
- Delete an item, with a confirmation prompt
- Item Details page showing the full record
- CSV data storage, automatically mirrored to JSON
- Consistent navigation bar and responsive card layout across all pages

## Installation

1. Clone or download this repository
2. Create a virtual environment:
   ```
   python -m venv venv
   ```
3. Activate it:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`
4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

Run the development server:

```
python manage.py runserver
```

Then open:

```
http://127.0.0.1:8000/
```

From the Home page you can view statistics and recent reports, jump to **Browse Items** to search/filter/edit/delete records, or use **Report Item** to add a new one.

## Project Structure

```
lost_and_found/
├── manage.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── data/
│   ├── lost_found.csv        # primary data store
│   └── lost_found.json       # kept in sync automatically
│
├── lost_and_found/            # project settings & routing
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
└── pages/                     # application logic
    ├── urls.py                # home, items, report, detail, edit, delete routes
    ├── views.py                # CSV read/write, filtering, CRUD logic
    └── templates/pages/
        ├── base.html          # shared layout & navigation
        ├── home.html          # dashboard
        ├── items.html         # browse, search, filter, edit/delete links
        ├── report.html        # add-item form
        ├── edit.html          # edit-item form
        └── detail.html        # single-item view
```

## Technologies Used

Python 3.12, Django 6.1, CSV, JSON, HTML, CSS

## Known Limitations

- Items are addressed by their row position in the CSV rather than a permanent ID, so concurrent edits by multiple users could shift indexes.
- No authentication — anyone with access to the site can add, edit, or delete records.
- No file/photo upload for items.
