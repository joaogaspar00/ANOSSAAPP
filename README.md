# ANOSSAAPP — Husstandsstyring

Et privat web-baseret husstandsstyringssystem til to brugere.

## Funktioner

| Modul | Funktioner |
|---|---|
| 🏠 Dashboard | Dagsoversigt: måltider, opgaver, advarsler, forbrug |
| 💰 Økonomi | Udgiftsregistrering, kategorier, månedstrend |
| ✅ Opgaver | Opret/rediger/slet, tildeling, gentagelse (daglig/ugentlig/månedlig) |
| 📅 Kalender | Ugevisning med opgaver, måltider og begivenheder |
| 🍽 Måltider | Ugentlig madplan + opskriftsdatabase med prisberegning |
| 📦 Lager | Køleskab/spisekammer med minimumsadvarsler |
| 🛒 Indkøb | Auto-genereret liste fra madplan + lager |
| ⚙️ Indstillinger | Profil, adgangskode, husstandsnavn, prismotor |

## Teknisk stack

- **Backend:** Python 3, Flask, SQLAlchemy, Flask-Login, Flask-Bcrypt
- **Database:** SQLite (udvikling) / PostgreSQL (produktion)
- **Frontend:** Jinja2, TailwindCSS-inspireret custom CSS, minimalt JS
- **Sikkerhed:** CSRF beskyttelse, bcrypt passwords, sikre sessions

---

## Hurtig start

### 1. Klon og opret virtuelt miljø

```bash
git clone <repo-url> anossaapp
cd anossaapp
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Konfigurer miljøvariabler

```bash
cp .env.example .env
# Rediger .env — skift SECRET_KEY til noget hemmeligt!
```

### 3. Start appen

```bash
python run.py
```

Åbn `http://localhost:5000` i din browser.

### 4. Log ind

Standardbrugere oprettes automatisk ved første start:

| Brugernavn | Adgangskode |
|---|---|
| `user1` | `changeme1` |
| `user2` | `changeme2` |

**Skift adgangskoder med det samme under Indstillinger → Skift adgangskode!**

---

## Projektstruktur

```
anossaapp/
├── app/
│   ├── __init__.py              # App factory
│   ├── extensions.py            # Flask extensions (db, login, bcrypt, csrf)
│   ├── models.py                # Alle SQLAlchemy modeller
│   ├── blueprints/
│   │   ├── auth/                # Login / logout
│   │   ├── dashboard/           # Forside
│   │   ├── finance/             # Økonomi
│   │   ├── tasks/               # Opgaver
│   │   ├── calendar/            # Kalender
│   │   ├── meals/               # Måltider + opskrifter
│   │   ├── inventory/           # Lager
│   │   ├── shopping/            # Indkøbsliste
│   │   └── settings/            # Indstillinger
│   ├── services/
│   │   ├── price_service.py     # Dansk prismotor (mock + interface)
│   │   ├── shopping_service.py  # Indkøbslistegenerator
│   │   └── task_service.py      # Opgavegentagelse + kalendersynk
│   └── templates/               # Jinja2 templates
├── config.py                    # Dev/prod konfiguration
├── run.py                       # Udviklingsserver
├── Procfile                     # Gunicorn (produktion)
└── requirements.txt
```

---

## Produktion (PostgreSQL + gunicorn)

```bash
# Sæt miljøvariabler
export FLASK_ENV=production
export SECRET_KEY="meget-hemmeligt-langt-random-nøgle"
export DATABASE_URL="postgresql://user:pass@host:5432/anossa"

# Kør med gunicorn
gunicorn "run:app" --bind 0.0.0.0:8000 --workers 2
```

---

## Prismotor — udvidelse

For at tilslutte en rigtig dansk supermarked-API, opret en ny klasse i `app/services/price_service.py`:

```python
class SallingGroupPriceService(AbstractPriceService):
    def get_price(self, ingredient_name: str) -> float | None:
        # Kald Salling Group API her
        ...
```

Skift derefter i `get_price_service()`:
```python
_service_instance = SallingGroupPriceService()
```

Ingen anden kode skal ændres.

---

## Sikkerhedsnoter

- Alle ruter kræver login (`@login_required`)
- Passwords hashes med bcrypt (aldrig klartekst)
- CSRF-beskyttelse på alle formularer
- Session cookies er httpOnly + SameSite=Lax
- `SESSION_COOKIE_SECURE = True` aktiveres automatisk i production config
- Husholdningsdata er isoleret — brugere ser kun deres eget husstand

---

## Nulstil database (udvikling)

```bash
rm instance/anossa.db
python run.py   # Opretter frisk DB med standardbrugere
```
