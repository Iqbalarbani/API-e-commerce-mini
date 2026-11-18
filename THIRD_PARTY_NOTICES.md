# Third-Party Notices

Mini Shop API menggunakan dependensi open-source berikut (data diambil dari
metadata paket yang terpasang, bukan perkiraan). Berkas ini disediakan untuk
tujuan kepatuhan lisensi.

> **Disclaimer:** Ini bukan nasihat hukum. Tinjau kembali bersama penasihat
> hukum Anda sebelum distribusi komersial.

## Ringkasan Kewajiban

| Lisensi | Kewajiban utama | Paket terkait |
|---|---|---|
| MIT / BSD / ISC / Apache-2.0 / PSF / Unlicense | Permisif: sertakan notice & teks lisensi. | mayoritas |
| **LGPL-3.0-only** | Distribusi modifikasi library wajib membuka sumber modifikasi tsb; menautkan secara dinamis umumnya aman. **Jangan** menyalin/memodifikasi kode psycopg tanpa memenuhi LGPL. | `psycopg`, `psycopg-binary` |
| **MPL-2.0** | File yang dimodifikasi dari kode berlisensi MPL wajib dibuka; penggunaan tanpa modifikasi cukup menyertakan notice. | `certifi` |

## Daftar Lengkap (dari environment terpasang)

| Paket | Lisensi |
|---|---|
| Deprecated | MIT |
| Mako | MIT |
| MarkupSafe | BSD-3-Clause |
| PyJWT | MIT |
| PyYAML | MIT |
| Pygments | BSD-2-Clause |
| SQLAlchemy | MIT |
| alembic | MIT |
| annotated-doc | MIT |
| annotated-types | MIT |
| anyio | MIT |
| bcrypt | Apache-2.0 |
| certifi | MPL-2.0 |
| click | BSD-3-Clause |
| coverage | Apache-2.0 |
| dnspython | ISC |
| email-validator | Unlicense |
| fastapi | MIT |
| h11 | MIT |
| httpcore | BSD-3-Clause |
| httptools | MIT |
| httpx | BSD-3-Clause |
| idna | BSD-3-Clause |
| iniconfig | MIT |
| limits | MIT |
| opentelemetry-api | Apache-2.0 |
| packaging | Apache-2.0 OR BSD-2-Clause |
| pip | MIT |
| pluggy | MIT |
| psycopg | LGPL-3.0-only |
| psycopg-binary | LGPL-3.0-only |
| pydantic | MIT |
| pydantic-settings | MIT |
| pydantic_core | MIT |
| pytest | MIT |
| pytest-cov | MIT |
| python-dotenv | BSD-3-Clause |
| ruff | MIT |
| slowapi | MIT |
| starlette | BSD-3-Clause |
| typing-inspection | MIT |
| typing_extensions | PSF-2.0 |
| uvicorn | BSD-3-Clause |
| uvloop | MIT |
| watchfiles | MIT |
| websockets | BSD-3-Clause |
| wrapt | BSD-2-Clause |

## Aset Frontend

- **Swagger UI** (dimuat dari CDN oleh `fastapi.openapi.docs`) â€” Apache-2.0.
- **ReDoc** (dimuat dari CDN) â€” MIT.

Keduanya dimuat sebagai aset statis dari CDN resmi, bukan disalin ke repo.

## Catatan Kode Proyek

Kode aplikasi pada repo ini adalah karya asli dan dilisensikan di bawah MIT
(lihat `LICENSE`). Ganti `<NAMA ANDA>` pada `LICENSE` dengan nama/entitas Anda.
