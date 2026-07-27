# ❤️ ANOSSAAPP — A gestão do casal, simplificada

Uma aplicação web Flask para casais gerirem juntos finanças, tarefas, refeições, atividades, objetivos e calendário.

---

## Módulos

| Módulo | Funcionalidades |
|---|---|
| 🏠 **Dashboard** | Resumo diário: tarefas, eventos, refeições, saldo |
| 💰 **Finanças** | Despesas partilhadas com divisão configurável, saldo automático, liquidação, exportar CSV |
| ✅ **Tarefas** | Kanban (pendente/em curso/concluída), prioridades, recorrência automática |
| 🍽️ **Refeições** | Catálogo de receitas com custo por porção, planeamento semanal, inventário, lista de compras automática |
| 🎯 **Atividades** | Wishlist do casal, avaliações, historial |
| 🏆 **Objetivos** | Metas financeiras e pessoais com barra de progresso |
| 📅 **Calendário** | Vista mensal, eventos partilhados e pessoais |
| ⚙️ **Definições** | Perfil, convite para parceiro, moeda, household |

---

## Stack técnica

- **Framework:** Flask 3.x (blueprints)
- **Base de dados:** SQLite por omissão (ficheiro único, sem setup); PostgreSQL opcional via `DATABASE_URL`
- **ORM / Migrações:** SQLAlchemy + Flask-Migrate (Alembic)
- **Frontend:** Jinja2 + CSS puro, sem frameworks JS pesados
- **Autenticação:** Flask-Login + Flask-Bcrypt
- **Formulários:** Flask-WTF (CSRF incluído)

---

## Início rápido

### 1. Criar ambiente virtual

```bash
python -m venv .venv
.venv\Scripts\activate       # Windows
source .venv/bin/activate    # Mac/Linux
```

### 2. Instalar dependências

```bash
pip install -r requirements.txt
```

### 3. Configurar variáveis de ambiente

Edita o ficheiro `.env` (copia de `.env.example` se não existir):

```env
SECRET_KEY=coloca-aqui-uma-chave-secreta-longa-e-aleatoria
FLASK_ENV=development
PORT=5001

# Por omissão usa SQLite (instance/anossa.db) — não é preciso configurar nada.
# Para usar PostgreSQL, descomenta e ajusta (codifica caracteres especiais na password, ex: # -> %23):
# DATABASE_URL=postgresql://user:password@localhost:5432/anossaapp
```

### 4. Aplicar migrações

```bash
flask db init      # apenas na primeira vez
flask db migrate -m "initial"
flask db upgrade
```

### 5. Iniciar o servidor

```bash
python run.py
```

Abre `http://localhost:5001` no teu browser.

---

## Fluxo de utilização

1. **Utilizador A** regista-se em `/registar/` → é levado a `/onboarding` para criar o Household (nome do casal + moeda)
2. Em **Definições** (`/settings/`), copia o link de convite
3. **Utilizador B** abre o link de convite → regista-se → fica no mesmo Household
4. A partir daí, ambos veem e editam todos os dados partilhados
5. O convite desativa-se automaticamente quando o Household atinge 2 membros

---

## Produção (gunicorn)

```bash
gunicorn "run:app" --bind 0.0.0.0:8000 --workers 2
```

Muda no `.env`:

```env
FLASK_ENV=production
SECRET_KEY=chave-muito-secreta-e-longa
DATABASE_URL=postgresql://user:password@host:5432/anossaapp
```

---

## Estrutura do projeto

```
ANOSSAAPP/
├── run.py                  # Entry point de desenvolvimento
├── config.py                # Configuração (dev/produção); SQLite por omissão, PostgreSQL opcional
├── .env                     # Variáveis de ambiente (NÃO commitar)
├── requirements.txt
├── app/
│   ├── __init__.py          # App factory (create_app), registo de blueprints
│   ├── extensions.py        # db, login_manager, bcrypt, csrf, migrate
│   ├── models.py             # Modelos SQLAlchemy (Household, User, Expense, Task, …)
│   ├── utils.py               # household_required, cálculo de saldo
│   ├── services/              # Lógica de negócio (recorrência, lista de compras, preços)
│   ├── blueprints/
│   │   ├── auth/               # Login, registo, onboarding, convite
│   │   ├── dashboard/           # Resumo diário
│   │   ├── finance/              # Despesas, divisão, liquidação, CSV
│   │   ├── tasks/                 # Tarefas com kanban e recorrência
│   │   ├── calendar/               # Calendário mensal
│   │   ├── meals/                   # Receitas, planeamento, inventário
│   │   ├── inventory/                 # Despensa
│   │   ├── shopping/                   # Lista de compras
│   │   ├── goals/                       # Objetivos partilhados
│   │   ├── activities/                   # Wishlist e atividades do casal
│   │   └── settings/                      # Perfil, household, convite
│   └── templates/                          # Templates Jinja2 (CSS inline no base.html)
└── migrations/                              # Alembic (gerado por `flask db init`)
```

---

## Segurança

- Todos os dados filtrados por Household — utilizadores não veem dados de outros casais
- Passwords com hash bcrypt
- CSRF em todos os formulários (Flask-WTF)
- Token de convite (UUID) expira automaticamente quando o Household atinge 2 membros
