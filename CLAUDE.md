# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

ANOSSAAPP is a Flask web app for couples to jointly manage finances, tasks, meals, activities, goals, and a shared calendar. All content is written in European Portuguese (model choices, routes, templates, UI strings); keep new code consistent with that. Database is SQLite by default (`instance/anossa.db`, zero setup); set `DATABASE_URL` to point at PostgreSQL instead if needed — both work through the same SQLAlchemy models.

## Commands

```bash
# activate venv (already created at .venv)
source .venv/bin/activate

# install deps
pip install -r requirements.txt

# migrations (Flask-Migrate / Alembic)
flask db init          # only once, creates migrations/
flask db migrate -m "message"
flask db upgrade

# run dev server
python run.py           # http://localhost:5001 (PORT env var)

# production
gunicorn "run:app" --bind 0.0.0.0:8000 --workers 2
```

Config is via `.env` (loaded with `python-dotenv`, read in `config.py`). `DATABASE_URL` is optional — unset, it defaults to `sqlite:///instance/anossa.db`; set it to a `postgresql://...` URL to use Postgres instead (percent-encode special characters in the password or the URL parses incorrectly). `SECRET_KEY` and `FLASK_ENV` (`development`/`production`, selects the class in `config.py`'s `config` dict) round out the essentials.

There is no test suite in this repo yet — verify changes by running the app and exercising the affected blueprint's routes (or with a throwaway `sqlite:///:memory:` `DATABASE_URL` + `db.create_all()` inside an app context for a quick smoke check, without touching the real dev database).

## Architecture

**Household-scoped multi-tenancy is the central concept.** Every domain model (`Task`, `Expense`, `MealPlan`, `Activity`, `Goal`, `CalendarEvent`, …) has a `household_id` FK and every view must filter queries by `current_user.household_id`. There is no other tenant boundary — a missing household filter is a data-leak bug between couples. `User.household_id` is nullable (a user can exist account-only, before creating or joining a household); every household-scoped route is decorated with both `@login_required` and `@household_required` (`app/utils.py`) — the latter redirects to `auth.onboarding` when the user has no household yet. Don't add a new blueprint route without both decorators.

- `app/__init__.py`: the app factory (`create_app`). Registers all blueprints and initializes extensions (`app/extensions.py`: `db`, `login_manager`, `bcrypt`, `csrf`, `migrate`). No implicit `db.create_all()`/seeding — schema changes go through Flask-Migrate.
- `app/models.py`: all SQLAlchemy models in one file. `Household` (currency, UUID `invite_token`/`invite_active`, capped at 2 members via `is_complete()`) and `User` (Flask-Login `UserMixin`, `household_id` nullable). `household.members()` / `household.partner(user)` are the standard ways to get the other partner — member ordering (`members()[0]` vs `[1]`) is significant for `Expense.amount_a/amount_b` and `Activity.rating_a/rating_b`, which are keyed by position, not by a stored "which user" reference.
- `app/utils.py`: `household_required` decorator, and `calculate_balance(household, user, partner)` — nets `Expense` splits against `Settlement` records between the two members. This is the one balance-calculation implementation; both `dashboard` and `finance` blueprints call it rather than recomputing.
- `app/blueprints/auth/`: registration (optionally carrying an invite token via `?convite=<uuid>` or session), `onboarding` (create a `Household` for a user with none), `accept_invite` (join an existing one). The invite token deactivates once a household reaches 2 members.
- `app/blueprints/dashboard/routes.py` is the integration point that reads across `tasks`, `finance`, `meals`, `inventory`, `activities` to build the daily summary — expect to touch it when adding a new cross-cutting widget.
- Each blueprint follows the same shape: `__init__.py` (Blueprint + route import), `forms.py` (Flask-WTF), `routes.py` (function-based views), own `templates/<blueprint>/`. Follow this pattern for new blueprints.
- Recurrence pattern (`app/services/task_service.py`): a `RecurrenceRule` (frequency/interval) is referenced by `Task`; `complete_task()` marks the current one done and, if recurring, computes the next due date and creates the next `Task` + syncs a `CalendarEvent` — recurrence advancement lives in the service, not the route.
- Shopping-list generation (`app/services/shopping_service.py`) derives items from planned meals' recipe ingredients (minus current inventory) and from low/recurring inventory items; `sync_shopping_list()` is the persisting entry point, called from the `shopping` blueprint's `/generate` route. Ingredient pricing goes through `app/services/price_service.py`, an abstract `PriceService` with a mock implementation — swap the concrete class in `get_price_service()` to plug in a real pricing API later.
- `CalendarEvent.visibility` (`shared`/`personal`) + `owner_id` gate what a household member sees; always filter through `event.visible_to(user)` rather than querying visibility directly, so the rule stays in one place.
- Money is stored as `Float` in the household's configured currency (`Household.currency`, symbol via `currency_symbol()`) — there's no per-user currency, and no multi-currency support within one household.
- Templates are Jinja2 with a single design system defined inline in `app/templates/base.html` (CSS custom properties, `.card`/`.btn`/`.badge`/`.form-*` classes, a desktop topbar + mobile bottom nav). Unauthenticated pages (`login.html`, `register.html`, `onboarding.html`) don't extend `base.html` — they're standalone since there's no household/nav context yet.
