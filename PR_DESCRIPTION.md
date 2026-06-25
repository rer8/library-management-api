# Library Management API — Pull Request

## What was done

This PR implements a fully-featured **Library Management REST API** built with Django REST Framework.

---

## New models / DB changes

Five new models introduced (see `db_diagram.png` in the repo root):

| Model | Description |
|-------|-------------|
| `User` | Custom user model with email as login field, bio, avatar |
| `Genre` | Book genre/category |
| `Author` | Book author with photo |
| `Book` | Core model — title, cover type (HARD/SOFT), inventory count, daily fee, M2M to authors & genres |
| `Borrowing` | Tracks who borrowed which book, with return date, status, and automatic fine calculation |
| `Review` | One review per user per book, rating 1–5 |

---

## New endpoints

### Authentication (`/api/user/`)
- `POST /register/` — register new user
- `POST /token/` — obtain JWT access + refresh tokens
- `POST /token/refresh/` — refresh access token
- `GET/PUT/PATCH /me/` — view and update own profile
- `POST /change-password/` — change password

### Library (`/api/library/`)
- **Genres** — full CRUD (admin write, public read)
- **Authors** — full CRUD (admin write, public read)
- **Books** — full CRUD (admin write, public read) + `GET /books/{id}/reviews/`
- **Borrowings** — create, list (own), retrieve, `POST /return/`, `GET /active/`
- **Reviews** — create (1 per book per user), list, retrieve, delete own

---

## Custom logic implemented

- **Auto-inventory management** — inventory decrements on borrow, increments on return
- **Fine calculation** — overdue books incur 2× daily fee per overdue day
- **Ownership-scoped queries** — regular users see only their own borrowings/reviews; admins see all
- **Advanced filtering** — books by genre, author, cover type, availability, price range; borrowings by status
- **Full-text search** — books searchable by title, author, description

---

## Optional additions

- `IsAdminOrReadOnly` custom permission — public can browse, only admins can modify catalogue
- `wait_for_db` management command — Docker-safe startup
- `library_fixture.json` — sample data with 7 books, 5 authors, 6 genres, 4 borrowings, 4 reviews
- Full test suite covering models, API endpoints, filters, permissions

---

## Screenshots

> Add Browsable API screenshots here before submitting

- Swagger UI at `/api/doc/swagger/`
- Book list with filters
- Create borrowing
- Return book endpoint
- Admin panel

---

## DB diagram

See `db_diagram.png` (also rendered in README.md).
