# Mini Shop API

E-Commerce REST API yang dibangun dengan **FastAPI**, **SQLAlchemy 2.x**, **Alembic**, **Pydantic v2**, dan **PostgreSQL**, sepenuhnya di-container dengan **Docker Compose**. Proyek ini dibuat sebagai portofolio backend dengan arsitektur berlapis (Route -> Service -> Repository) dan penanganan race condition pada stok saat checkout.
<img width="1917" height="978" alt="image" src="https://github.com/user-attachments/assets/0fb56dd2-ec56-401a-934d-1477f1b3f4a8" />

---

## Deskripsi

Mini Shop API menyediakan alur e-commerce inti: registrasi & login pengguna (JWT), katalog produk & kategori, keranjang belanja, checkout yang aman terhadap race condition, serta manajemen order oleh admin. Seluruh endpoint mengembalikan format error yang konsisten:

```json
{ "error": { "code": "INVALID_CREDENTIALS", "message": "Email atau password salah." } }
```

## Fitur

- **Autentikasi**: register, login JWT, dependency `get_current_user` dan `require_admin`.
- **Rate limiting** pada `/auth/login` (default `5/minute`, dapat diatur lewat `LOGIN_RATE_LIMIT`).
- **Validasi password** minimal 8 karakter.
- **Katalog**: list & detail produk, filter `search`, `category_id`, `min_price`, `max_price`, `sort` (`price_asc`, `price_desc`, `newest`), paginasi `page`/`limit`; CRUD kategori & produk (admin).
- **Keranjang**: tambah/ubah/hapus item dengan validasi quantity minimal 1, produk aktif, dan jumlah tidak melebihi stok.
- **Checkout**: satu transaksi atomik, row-level lock (`SELECT ... FOR UPDATE`) pada produk, snapshot nama & harga di `order_items`.
- **Order**: riwayat order, detail order, update status oleh admin dengan validasi transisi status.
- **Health check** dengan verifikasi koneksi database.
- **Seeder idempoten** (`python -m scripts.seed`) aman dijalankan berulang.

## Tech Stack

| Komponen | Teknologi |
|---|---|
| Framework | FastAPI |
| ORM | SQLAlchemy 2.x |
| Migrasi | Alembic |
| Validasi | Pydantic v2 |
| Database | PostgreSQL 16 |
| Auth | JWT (PyJWT) + bcrypt |
| Rate limit | slowapi |
| Container | Docker & Docker Compose |
| Test | pytest, pytest-cov, httpx |
| Lint | ruff |

## Arsitektur

```
app/
  api/            # Lapisan Route (HTTP, dependency injection)
  services/       # Lapisan Service (business rules)
  repositories/   # Lapisan Repository (akses database)
  models/         # ORM SQLAlchemy
  schemas/        # Pydantic (request/response)
  core/           # config, database, security, dependencies, exceptions, rate_limit
alembic/          # Migrasi database
scripts/seed.py   # Seeder idempoten
tests/            # unit & integration tests
```

Alur request: **Route** memanggil **Service**, Service memanggil **Repository**, Repository berbicara ke database. Route tidak pernah menyentuh ORM secara langsung.

## Cara Menjalankan (satu perintah)

Prasyarat: Docker & Docker Compose terpasang.

```bash
cp .env.example .env   # opsional: sesuaikan nilai
python -m venv .venv && .venv/Scripts/activate  # Windows (opsional, untuk seed lokal)
```

Jalankan seluruh stack:

```bash
docker compose up --build
```

Container `api` otomatis menjalankan `alembic upgrade head` sebelum `uvicorn` (lihat `command` di `docker-compose.yml`), sehingga **migrasi berjalan otomatis** saat `docker compose up`.

Setelah container sehat:

- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- Health: http://localhost:8000/health

Isi data contoh (idempoten, aman diulang):

```bash
docker compose exec api python -m scripts.seed
```

Akun seed default (dapat diubah lewat `SEED_*` di `.env`):
- Admin: `admin@example.com` / `Admin12345`
- Customer: `customer@example.com` / `Customer12345`

### Mengecek tabel sudah terbentuk

```bash
docker compose exec db psql -U minishop -d minishop_db -c "\dt"
```

Atau cek versi migrasi:

```bash
docker compose exec api alembic current
```

## Contoh cURL

**Register**

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"budi@example.com","password":"Password123","full_name":"Budi"}'
```

**Login**

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"budi@example.com","password":"Password123"}'
```

Respons berisi `access_token`. Gunakan pada endpoint terproteksi:

```bash
TOKEN="<access_token_dari_login>"
curl http://localhost:8000/api/v1/auth/me -H "Authorization: Bearer $TOKEN"
```

**List produk dengan filter**

```bash
curl "http://localhost:8000/api/v1/products?search=headphone&min_price=100000&max_price=1000000&sort=price_asc&page=1&limit=10"
```

**Tambah ke keranjang & checkout**

```bash
curl -X POST http://localhost:8000/api/v1/cart/items \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"product_id":"<uuid_produk>","quantity":2}'

curl -X POST http://localhost:8000/api/v1/checkout \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"shipping_address":"Jl. Merdeka No. 1, Jakarta"}'
```

## Tabel Endpoint

| Method | Path | Auth | Deskripsi |
|---|---|---|---|
| GET | `/health` | - | Health check + koneksi DB |
| POST | `/api/v1/auth/register` | - | Registrasi customer |
| POST | `/api/v1/auth/login` | - | Login, dapatkan JWT (rate-limited) |
| GET | `/api/v1/auth/me` | User | Profil user saat ini |
| GET | `/api/v1/auth/admin-check` | Admin | Contoh endpoint admin |
| GET | `/api/v1/categories` | - | Daftar kategori |
| POST | `/api/v1/categories` | Admin | Buat kategori |
| GET | `/api/v1/products` | - | List produk (search/filter/sort/paginasi) |
| GET | `/api/v1/products/{id}` | - | Detail produk |
| POST | `/api/v1/products` | Admin | Buat produk |
| PATCH | `/api/v1/products/{id}` | Admin | Ubah produk |
| GET | `/api/v1/cart` | User | Lihat keranjang |
| POST | `/api/v1/cart/items` | User | Tambah item |
| PATCH | `/api/v1/cart/items/{id}` | User | Ubah jumlah item |
| DELETE | `/api/v1/cart/items/{id}` | User | Hapus item |
| POST | `/api/v1/checkout` | User | Checkout keranjang jadi order |
| GET | `/api/v1/orders` | User | Riwayat order saya |
| GET | `/api/v1/orders/{id}` | User | Detail order saya |
| GET | `/api/v1/admin/orders` | Admin | Semua order |
| GET | `/api/v1/admin/orders/{id}` | Admin | Detail order (admin) |
| PATCH | `/api/v1/admin/orders/{id}/status` | Admin | Update status order |

## Bagaimana Race Condition Dicegah

Saat checkout, service mengunci baris produk yang terlibat memakai `SELECT ... FOR UPDATE` (PostgreSQL row-level lock) **sebelum** membaca atau mengurangi stok, di dalam satu transaksi. Jika dua checkout bersamaan menyentuh produk yang sama, checkout kedua akan menunggu hingga transaksi pertama commit, lalu membaca stok yang sudah berkurang dan gagal dengan bersih (`INSUFFICIENT_STOCK`) alih-alih membuat stok menjadi negatif. Jika terjadi error, seluruh transaksi di-rollback sehingga tidak ada perubahan setengah jadi.

## Cara Menjalankan Test

Test memakai database terpisah (`TEST_DATABASE_URL`). `tests/conftest.py` mengarahkan engine aplikasi ke database test sebelum import.

Dengan Docker (disarankan):

```bash
docker compose exec api pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

Atau lokal (butuh PostgreSQL berjalan & dependency terpasang):

```bash
pip install -e ".[dev]"
pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

Cakupan test wajib:
- register/login gagal (password salah, email duplikat, password < 8)
- akses tanpa token (401) dan role salah (403)
- stok tidak cukup saat tambah keranjang & checkout
- checkout sukses (snapshot + stok berkurang)
- dua checkout bersamaan pada stok terbatas (hanya satu yang sukses)

> **Hasil pengujian (output nyata, dijalankan di container dengan PostgreSQL 16):**
> ```
> 32 passed, 3 warnings in 16.55s
> Required test coverage of 80% reached. Total coverage: 85.06%
> ```
> Seluruh 32 test (17 unit + 15 integration) lulus dan coverage 85% melewati target 80%. Reproduksi:
> ```bash
> docker compose exec -e TEST_DATABASE_URL=postgresql+psycopg://minishop:minishop_secret@db:5432/minishop_test_db \
>   api pytest --cov=app --cov-report=term-missing --cov-fail-under=80
> ```

## CI

Workflow `.github/workflows/ci.yml` menjalankan:
1. `ruff check .`
2. `pytest --cov=app --cov-fail-under=80` dengan service PostgreSQL
3. `docker build` image aplikasi

## Screenshot

Placeholder gambar tersedia di `docs/screenshots/`. Tambahkan screenshot Swagger UI, contoh response, dan hasil coverage ke folder tersebut.

| Screenshot | File |
|---|---|
| Swagger UI | `docs/screenshots/swagger.png` |
| Contoh response produk | `docs/screenshots/products.png` |
| Hasil coverage | `docs/screenshots/coverage.png` |

## Lisensi

Kode proyek ini dilisensikan di bawah **MIT** (lihat `LICENSE`). Daftar lisensi
dependensi pihak ketiga beserta kewajibannya ada di `THIRD_PARTY_NOTICES.md`.

> Perhatian: dependensi `psycopg`/`psycopg-binary` berlisensi **LGPL-3.0-only**
dan `certifi` berlisensi **MPL-2.0**. Keduanya dipakai tanpa modifikasi (menautkan
secara dinamis), yang umumnya aman untuk penggunaan komersial, tetapi tinjau
sendiri dengan penasihat hukum sebelum distribusi.

## Yang Saya Pelajari

- Merancang arsitektur berlapis Route -> Service -> Repository agar logic mudah dites dengan fake repository.
- Menangani race condition stok dengan row-level lock PostgreSQL dan transaksi atomik.
- Menyimpan snapshot harga & nama produk di `order_items` agar riwayat order tidak berubah saat katalog berubah.
- Menerapkan JWT auth, dependency injection untuk otorisasi, dan rate limiting.
- Menulis migrasi Alembic dan seeder idempoten yang aman diulang.
- Menyiapkan CI dengan service database dan quality gate coverage.
