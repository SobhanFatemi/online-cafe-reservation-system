# Online Cafe Reservation System

A Django-based web application for running a cafe's table reservations and ordering online. Customers browse the menu, book a table for a specific time slot, pre-order food, and leave reviews after their visit. Staff manage everything — tables, time slots, working hours, menu, discounts, reservations, and reviews — through a custom admin dashboard.

## Features

### Customer-facing
- **Account management** — sign up with email-based account activation, log in, and reset passwords. Inactive accounts automatically receive a fresh activation link on login attempt.
- **Menu browsing** — view food items by category with descriptions, images, prices, and discounted prices.
- **Table reservations** — pick a date and an available time slot for a table, choosing the number of people (validated against table capacity).
- **Food pre-ordering** — attach food items to a reservation; the total price is recalculated automatically (table price per person + discounted food prices).
- **Reservation management** — view your reservations, see details, and cancel them while cancellation is allowed.
- **Reviews** — leave a rating and comment after a completed, attended reservation, and edit or delete your own comments (until staff have replied).

### Staff dashboard (`/admin-panel/`)
- **Reservations** — list, inspect, and cancel reservations (with a configurable cancellation window).
- **Tables** — create, edit, and delete cafe tables (number, capacity, price per person, active state).
- **Time slots & working hours** — define weekly working hours, auto-generate time slots for upcoming days, manually create/edit/delete slots, and clear generated slots.
- **Menu** — manage categories and food items, including images and availability.
- **Discounts** — create percent or fixed-amount discounts and attach them to food items or whole categories (discounts stack: item-level then category-level).
- **Reviews** — read customer comments and post one staff reply per comment.
- **Cafe settings** — a single settings record controls cancellation rules, slot duration, how many days ahead slots are generated, and whether reservations are enabled.

### Under the hood
- **Soft delete** — most models inherit a `BaseModel` with an `is_deleted` flag; the default manager hides soft-deleted rows while `all_objects` exposes them.
- **Slot-generation engine** — `reservations/utils.py` builds time slots from working hours and the configured slot duration for each active table.
- **Automatic price recalculation** — signals keep a reservation's total in sync whenever its food items change.

## Tech stack

- **Python** 3.14 / **Django** 6.0
- **PostgreSQL** (via `psycopg2`)
- **Pillow** for image uploads
- **python-dotenv** for environment configuration
- Server-rendered Django templates with plain CSS/JS (no frontend framework)

## Project layout

```
config/         Project settings, root URLConf, WSGI/ASGI entrypoints
common/         Shared BaseModel (soft delete) and base admin
users/          Authentication: signup, email activation, login, password reset
menu/           Category, FoodItem, Discount models and menu views
seating/        CafeTable, TimeSlot, WorkingHour models
reservations/   Reservation, ReservationFood, Comment, Reply + booking flow
dashboard/      Custom staff admin panel and CafeSetting
templates/      HTML templates grouped by app
static/         CSS and JavaScript
seeds/          Sample data script
ERD.png         Entity-relationship diagram
```

## Getting started

### Prerequisites
- Python 3.14+
- PostgreSQL

### 1. Clone and create a virtual environment

```bash
git clone <repo-url>
cd online-cafe-reservation-system
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

Copy the example file and fill in your values:

```bash
cp .env.example .env
```

| Variable | Description |
| --- | --- |
| `SECRET_KEY` | Django secret key |
| `DEBUG` | `True` for development |
| `DB_NAME` | PostgreSQL database name |
| `DB_USER` | PostgreSQL user |
| `DB_PASSWORD` | PostgreSQL password |
| `DB_HOST` | Database host (default `localhost`) |
| `DB_PORT` | Database port (default `5432`) |
| `EMAIL_USER` | SMTP username for sending activation/reset emails |
| `EMAIL_PASSWORD` | SMTP password / app password |

> Email is configured for Gmail SMTP (`smtp.gmail.com:587`, TLS). Set `EMAIL_USER`/`EMAIL_PASSWORD` to enable account-activation and password-reset emails.

### 4. Set up the database

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 5. (Optional) Load sample menu data

```bash
python manage.py shell < seeds/full_seed.py
```

### 6. Run the development server

```bash
python manage.py runserver
```

The app is now available at http://127.0.0.1:8000/.

## Key URLs

| Path | Purpose |
| --- | --- |
| `/` | Landing page |
| `/menu/` | Browse the menu |
| `/accounts/signup/`, `/accounts/login/` | Authentication |
| `/reservations/create/` | Make a reservation |
| `/reservations/my/` | Your reservations |
| `/admin-panel/` | Staff dashboard |
| `/admin/` | Django admin |

## Data model overview

- **Reservation** ↔ one **TimeSlot** (which belongs to a **CafeTable**), owned by a **User**, with a status and attendance status.
- **ReservationFood** links a reservation to **FoodItem**s with quantities and computed final prices.
- **FoodItem** belongs to a **Category**; both can carry a **Discount** (percent or fixed).
- **Comment** (rating + text) is left per reservation; staff add one **Reply** per comment.
- **WorkingHour** (per weekday) drives time-slot generation; **CafeSetting** holds global rules.

See [ERD.png](ERD.png) for the full entity-relationship diagram.

## License

Released under the [MIT License](LICENSE).
