"""Self-contained landing dashboard listing every built feature.

GET endpoints are linked directly so they can be clicked from the browser.
Endpoints that need a body or auth (POST/PATCH/DELETE) link to Swagger UI.
"""

FEATURES: list[tuple[str, str, list[tuple[str, str, str, bool]]]] = [
    (
        "Sistem",
        "Status layanan dan dokumentasi interaktif.",
        [
            ("GET", "/health", "Health check + status database", True),
            ("GET", "/docs", "Swagger UI (coba endpoint langsung)", True),
            ("GET", "/redoc", "ReDoc (dokumentasi rapi)", True),
            ("GET", "/openapi.json", "Spesifikasi OpenAPI", True),
        ],
    ),
    (
        "Autentikasi",
        "Register, login JWT, profil, dan cek role admin.",
        [
            ("POST", "/api/v1/auth/register", "Registrasi customer baru", False),
            ("POST", "/api/v1/auth/login", "Login, dapatkan JWT (rate-limited)", False),
            ("GET", "/api/v1/auth/me", "Profil user saat ini (butuh token)", False),
            ("GET", "/api/v1/auth/admin-check", "Contoh endpoint khusus admin", False),
        ],
    ),
    (
        "Katalog",
        "Kategori dan produk dengan filter, sort, dan paginasi.",
        [
            ("GET", "/api/v1/categories", "Daftar kategori", True),
            ("POST", "/api/v1/categories", "Buat kategori (admin)", False),
            ("GET", "/api/v1/products", "List produk (search/filter/sort/page)", True),
            ("GET", "/api/v1/products/{product_id}", "Detail produk", False),
            ("POST", "/api/v1/products", "Buat produk (admin)", False),
            ("PATCH", "/api/v1/products/{product_id}", "Ubah produk (admin)", False),
        ],
    ),
    (
        "Keranjang",
        "Kelola item keranjang dengan validasi stok.",
        [
            ("GET", "/api/v1/cart", "Lihat keranjang (butuh token)", False),
            ("POST", "/api/v1/cart/items", "Tambah item", False),
            ("PATCH", "/api/v1/cart/items/{item_id}", "Ubah jumlah item", False),
            ("DELETE", "/api/v1/cart/items/{item_id}", "Hapus item", False),
        ],
    ),
    (
        "Order & Checkout",
        "Checkout atomik, riwayat, detail, dan manajemen status admin.",
        [
            ("POST", "/api/v1/checkout", "Checkout keranjang jadi order", False),
            ("GET", "/api/v1/orders", "Riwayat order saya", False),
            ("GET", "/api/v1/orders/{order_id}", "Detail order saya", False),
            ("GET", "/api/v1/admin/orders", "Semua order (admin)", False),
            ("GET", "/api/v1/admin/orders/{order_id}", "Detail order (admin)", False),
            ("PATCH", "/api/v1/admin/orders/{order_id}/status", "Update status (admin)", False),
        ],
    ),
]

_COLORS = {
    "GET": "#2563eb",
    "POST": "#16a34a",
    "PATCH": "#d97706",
    "DELETE": "#dc2626",
}


def _render_card(method: str, path: str, desc: str, direct: bool) -> str:
    color = _COLORS.get(method, "#6b7280")
    if direct:
        action = f'<a class="go" href="{path}" target="_blank">Buka</a>'
    else:
        action = '<a class="go alt" href="/docs" target="_blank">Coba di Swagger</a>'
    return (
        '<div class="row">'
        f'<span class="method" style="background:{color}">{method}</span>'
        f'<code>{path}</code>'
        f'<span class="desc">{desc}</span>'
        f'{action}'
        "</div>"
    )


def build_dashboard_html(*, app_name: str) -> str:
    """Return a single self-contained HTML dashboard page."""
    sections = []
    total = 0
    for title, subtitle, endpoints in FEATURES:
        rows = "".join(_render_card(*ep) for ep in endpoints)
        total += len(endpoints)
        sections.append(
            '<section class="card">'
            f'<h2>{title}</h2><p class="sub">{subtitle}</p>{rows}</section>'
        )

    return f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{app_name} - Dashboard</title>
<style>
  :root {{ --bg:#f6f7f9; --fg:#1f2328; --card:#ffffff; --muted:#5b6470; --border:#e4e7eb; }}
  body.dark {{ --bg:#0f1216; --fg:#e6e6e6; --card:#181c21; --muted:#9aa4af; --border:#2a2f36; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;
         background:var(--bg); color:var(--fg); transition:background .2s,color .2s; }}
  header {{ padding:28px 24px 8px; max-width:1100px; margin:0 auto; }}
  header h1 {{ margin:0 0 6px; font-size:26px; }}
  header p {{ margin:0; color:var(--muted); }}
  .badge {{ display:inline-block; margin-top:10px; font-size:12px; color:var(--muted); }}
  main {{ max-width:1100px; margin:0 auto; padding:12px 24px 60px;
          display:grid; gap:18px; grid-template-columns:repeat(auto-fit,minmax(320px,1fr)); }}
  .card {{ background:var(--card); border:1px solid var(--border); border-radius:14px;
           padding:18px; box-shadow:0 1px 3px rgba(0,0,0,.05); }}
  .card h2 {{ margin:0 0 4px; font-size:17px; }}
  .sub {{ margin:0 0 14px; color:var(--muted); font-size:13px; }}
  .row {{ display:flex; align-items:center; gap:10px; padding:7px 0;
          border-top:1px solid var(--border); }}
  .row:first-of-type {{ border-top:none; }}
  .method {{ color:#fff; font:700 10px/1 monospace; padding:5px 6px;
             border-radius:6px; min-width:52px; text-align:center; }}
  code {{ font:12px monospace; flex:0 0 auto; color:var(--fg); }}
  .desc {{ flex:1 1 auto; font-size:12px; color:var(--muted); }}
  .go {{ font-size:12px; text-decoration:none; color:#fff; background:#2563eb; padding:5px 10px;
         border-radius:8px; white-space:nowrap; }}
  .go.alt {{ background:#6b7280; }}
  #toggle {{ position:fixed; bottom:20px; right:20px; padding:9px 14px; border-radius:999px;
             border:1px solid var(--border); background:var(--card); color:var(--fg);
             font:600 13px system-ui; cursor:pointer; box-shadow:0 2px 8px rgba(0,0,0,.15); }}
</style>
</head>
<body>
<header>
  <h1>{app_name}</h1>
  <p>Dashboard fitur - klik untuk membuka. Endpoint yang butuh body/token diarahkan ke Swagger.</p>
  <span class="badge">{total} endpoint terdaftar</span>
</header>
<main>{''.join(sections)}</main>
<button id="toggle" type="button">Dark mode</button>
<script>
(function(){{
  var btn=document.getElementById('toggle'), KEY='mini-shop-theme';
  function apply(t){{ var d=t==='dark'; document.body.classList.toggle('dark',d);
                     btn.textContent=d?'Light mode':'Dark mode'; }}
  apply(localStorage.getItem(KEY)||'light');
  btn.addEventListener('click',function(){{
    var n=document.body.classList.contains('dark')?'light':'dark';
    localStorage.setItem(KEY,n); apply(n);
  }});
}})();
</script>
</body>
</html>"""
