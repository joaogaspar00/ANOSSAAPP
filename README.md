# ❤️ ANOSSAAPP — A gestão do casal, simplificada

Uma aplicação web Django para casais gerirem juntos finanças, tarefas, refeições, atividades, objetivos e calendário.

---

## Módulos

| Módulo | Funcionalidades |
|---|---|
| 🏠 **Dashboard** | Resumo diário: tarefas, eventos, refeições, saldo |
| 💰 **Finanças** | Despesas partilhadas, saldo automático, exportar CSV |
| ✅ **Tarefas** | Kanban, prioridades, recorrência automática |
| 🍽️ **Refeições** | Planeamento semanal, inventário, lista de compras automática |
| 🎯 **Atividades** | Wishlist do casal, avaliações, historial |
| 🏆 **Objetivos** | Metas financeiras e pessoais com barra de progresso |
| 📅 **Calendário** | Vista mensal, eventos partilhados e pessoais |
| ⚙️ **Definições** | Perfil, convite para parceiro, moeda, household |

---

## Stack técnica

- **Framework:** Django 6.x
- **Base de dados:** SQLite (dev) / PostgreSQL (produção)
- **Frontend:** HTML + CSS puro, sem frameworks JS pesados
- **Autenticação:** Django Auth com UserProfile estendido
- **Ficheiros estáticos:** WhiteNoise

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

Edita o ficheiro `.env` (já existe no projeto):

```env
SECRET_KEY=coloca-aqui-uma-chave-secreta-longa-e-aleatoria
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# SQLite (padrão para desenvolvimento):
DB_ENGINE=sqlite

# PostgreSQL (para produção):
# DB_ENGINE=postgresql
# DB_NAME=anossaapp
# DB_USER=postgres
# DB_PASSWORD=a_tua_password
# DB_HOST=localhost
# DB_PORT=5432
```

### 4. Aplicar migrações

```bash
python manage.py migrate
```

### 5. Criar superutilizador (opcional, para acesso ao admin)

```bash
python manage.py createsuperuser
```

### 6. Iniciar o servidor

```bash
python manage.py runserver
```

Abre `http://localhost:8000` no teu browser.

---

## Fluxo de utilização

1. **Utilizador A** regista-se em `/registar/` → cria o Household (nome do casal + moeda)
2. Em **Definições** (`/definicoes/`), copia o link de convite
3. **Utilizador B** abre o link de convite → regista-se → fica no mesmo Household
4. A partir daí, ambos veem e editam todos os dados partilhados

---

## Mudar para PostgreSQL

1. Edita `.env`:
   ```env
   DB_ENGINE=postgresql
   DB_NAME=anossaapp
   DB_USER=postgres
   DB_PASSWORD=a_tua_password
   DB_HOST=localhost
   DB_PORT=5432
   ```
2. Cria a base de dados: `createdb anossaapp`
3. Aplica migrações: `python manage.py migrate`

---

## Produção (gunicorn)

```bash
gunicorn anossaapp.wsgi:application --bind 0.0.0.0:8000 --workers 2
```

Muda no `.env`:
```env
DEBUG=False
SECRET_KEY=chave-muito-secreta-e-longa
ALLOWED_HOSTS=o-teu-dominio.com
```

---

## Estrutura do projeto

```
anossaapp/
├── manage.py
├── .env                    # Variáveis de ambiente (NÃO commitar em produção)
├── requirements.txt
├── anossaapp/              # Configuração Django
│   ├── settings.py
│   └── urls.py
├── core/                   # User, Household, autenticação, onboarding
├── financas/               # Despesas e liquidações
├── tarefas/                # Tarefas com kanban e recorrência
├── refeicoes/              # Refeições, inventário, lista de compras
├── atividades/             # Wishlist e atividades do casal
├── objetivos/              # Objetivos partilhados
├── calendario/             # Calendário mensal
├── static/css/main.css     # Estilos CSS
└── templates/              # Templates HTML
```

---

## Segurança

- Todos os dados filtrados por Household — utilizadores não veem dados de outros casais
- Passwords com hash Django (PBKDF2)
- CSRF em todos os formulários
- Middleware de segurança Django ativo
- Token de convite expira automaticamente quando o Household atinge 2 membros
