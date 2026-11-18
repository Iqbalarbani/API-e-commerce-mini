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

_METHOD_TONES: dict[str, tuple[str, str]] = {
    "GET": ("#dbe7ff", "#2c4a86"),
    "POST": ("#d5f1e2", "#1c6a49"),
    "PATCH": ("#ffe9c9", "#8a5a12"),
    "DELETE": ("#ffdbe3", "#93304a"),
}
_DEFAULT_TONE = ("#e8eaf1", "#4b5563")


def _render_card(method: str, path: str, desc: str, direct: bool) -> str:
    bg, fg = _METHOD_TONES.get(method, _DEFAULT_TONE)
    if direct:
        action = f'<a class="go" href="{path}" target="_blank" rel="noopener">Buka</a>'
    else:
        action = (
            '<a class="go alt" href="/docs" target="_blank" rel="noopener">'
            "Coba di Swagger</a>"
        )
    return (
        '<div class="row">'
        f'<span class="method" style="background:{bg};color:{fg}">{method}</span>'
        '<div class="info">'
        f"<code>{path}</code>"
        f'<span class="desc">{desc}</span>'
        "</div>"
        f"{action}"
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
            f"<h2>{title}</h2><p class=\"sub\">{subtitle}</p>{rows}</section>"
        )

    return f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{app_name} - Dashboard</title>
<style>
  :root {{
    --fg:#2b2f38; --muted:#6b7280; --card:#ffffff; --border:#ece7f2;
    --accent-a:#8fb4ff; --accent-b:#c9a7f5; --accent-c:#ffb3c7;
  }}
  body.dark {{
    --fg:#eceef4; --muted:#a6adbb; --card:#1b1e26; --border:#2c313c;
    --accent-a:#6d8ce0; --accent-b:#a387d8; --accent-c:#e093ab;
  }}
  * {{ box-sizing:border-box; }}
  body {{
    margin:0; min-height:100vh; color:var(--fg);
    font-family:system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;
    background:
      radial-gradient(1100px 520px at 8% -8%, #ffe4ef 0%, rgba(255,228,239,0) 60%),
      radial-gradient(900px 480px at 96% 0%, #e2eeff 0%, rgba(226,238,255,0) 55%),
      linear-gradient(180deg,#fbfaff 0%,#f6f6fc 55%,#faf6fb 100%);
    background-attachment:fixed;
    transition:color .2s, background .3s;
  }}
  body.dark {{
    background:
      radial-gradient(1100px 520px at 8% -8%, #2b2437 0%, rgba(43,36,55,0) 60%),
      radial-gradient(900px 480px at 96% 0%, #1e2a3d 0%, rgba(30,42,61,0) 55%),
      linear-gradient(180deg,#12141a 0%,#151820 60%,#16131b 100%);
  }}
  .hero {{ max-width:1120px; margin:0 auto; padding:56px 24px 8px; }}
  .kicker {{
    display:inline-block; margin:0 0 16px; padding:7px 15px; border-radius:999px;
    font:600 11px/1 system-ui; letter-spacing:.14em; text-transform:uppercase;
    color:#5b4b8a; border:1px solid rgba(255,255,255,.7);
    background:linear-gradient(120deg,#e6dcff,#d8ecff 60%,#ffe1ea);
  }}
  h1 {{
    margin:0 0 14px; font:700 clamp(30px,5vw,44px)/1.12 Georgia,'Times New Roman',serif;
    letter-spacing:.2px;
    background:linear-gradient(110deg,#6d8ce0,#a387d8 45%,#ef9ab1);
    -webkit-background-clip:text; background-clip:text; color:transparent;
  }}
  h1::after {{
    content:""; display:block; width:76px; height:4px; margin-top:12px; border-radius:99px;
    background:linear-gradient(90deg,var(--accent-a),var(--accent-b),var(--accent-c));
  }}
  .lede {{
    margin:0 0 18px; max-width:640px; font-size:15px; line-height:1.65;
    color:var(--muted);
  }}
  .tagline {{
    margin:-6px 0 16px; font:italic 500 15px/1.4 Georgia,'Times New Roman',serif;
    letter-spacing:.3px; color:#8b7bb8;
  }}
  body.dark .tagline {{ color:#b7a9dc; }}
  .badge {{
    display:inline-block; font:600 12px/1 system-ui; color:#4b5563;
    padding:9px 15px; border-radius:999px; border:1px solid var(--border);
    background:linear-gradient(120deg,#eef2ff,#fdeef5);
  }}
  body.dark .kicker {{ color:#cdbff0; background:linear-gradient(120deg,#31284a,#25334a 60%,#3d2733); }}
  body.dark .badge {{ color:#c7cdd8; background:linear-gradient(120deg,#232a3a,#2e2333); }}
  main {{
    max-width:1120px; margin:0 auto; padding:22px 24px 80px;
    display:grid; gap:20px;
    grid-template-columns:repeat(auto-fit, minmax(340px, 1fr));
    align-items:start;
  }}
  .card {{
    position:relative; overflow:hidden; background:var(--card);
    border:1px solid var(--border); border-radius:22px; padding:22px 20px 10px;
    box-shadow:0 12px 34px -24px rgba(76,60,120,.55), 0 2px 6px -3px rgba(76,60,120,.22);
  }}
  .card::before {{
    content:""; position:absolute; inset:0 0 auto 0; height:5px;
    background:linear-gradient(90deg,var(--accent-a),var(--accent-b),var(--accent-c));
  }}
  .card h2 {{
    margin:0 0 4px; font:700 17px/1.3 Georgia,'Times New Roman',serif;
  }}
  .sub {{ margin:0 0 12px; color:var(--muted); font-size:13px; line-height:1.5; }}
  .row {{
    display:grid; grid-template-columns:auto minmax(0,1fr) auto;
    gap:4px 12px; align-items:center; padding:11px 0;
    border-top:1px dashed var(--border);
  }}
  .row:first-of-type {{ border-top:none; }}
  .method {{
    justify-self:start; font:700 10px/1 ui-monospace,monospace; letter-spacing:.06em;
    padding:6px 8px; border-radius:8px; min-width:56px; text-align:center;
  }}
  .info {{ min-width:0; display:flex; flex-direction:column; gap:3px; }}
  code {{
    font:12px/1.45 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
    color:var(--fg); overflow-wrap:anywhere;
  }}
  .desc {{ font-size:12px; line-height:1.45; color:var(--muted); overflow-wrap:anywhere; }}
  .go {{
    justify-self:end; white-space:nowrap; font:600 12px/1 system-ui;
    text-decoration:none; color:#fff; padding:9px 14px; border-radius:999px;
    background:linear-gradient(135deg,#8fb4ff,#a78bfa);
    box-shadow:0 8px 16px -10px rgba(120,110,220,.9);
  }}
  .go.alt {{
    color:#5b4b8a; background:linear-gradient(135deg,#e7e3f7,#f6dce8);
    box-shadow:0 8px 16px -12px rgba(150,120,180,.8);
  }}
  body.dark .go.alt {{ color:#d6ccf2; background:linear-gradient(135deg,#2b2740,#3a2735); }}
  #toggle {{
    position:fixed; bottom:20px; right:20px; padding:10px 16px; border-radius:999px;
    border:1px solid var(--border); color:var(--fg); cursor:pointer;
    font:600 13px system-ui;
    background:linear-gradient(135deg,#f4eefb,#e6f0ff);
    box-shadow:0 10px 24px -14px rgba(76,60,120,.9);
  }}
  body.dark #toggle {{ background:linear-gradient(135deg,#262033,#1d2739); }}
  @media (max-width:560px) {{
    .hero {{ padding:40px 16px 4px; }}
    main {{ grid-template-columns:1fr; padding:16px 16px 76px; }}
    .row {{ grid-template-columns:auto minmax(0,1fr); }}
    .go {{ grid-column:1 / -1; justify-self:start; margin-top:6px; }}
  }}
</style>
</head>
<body>
<header class="hero">
  <p class="kicker">Dashboard Fitur</p>
  <h1>{app_name}</h1>
  <p class="tagline">E-Commerce REST API</p>
  <p class="lede">Klik tombol untuk membuka endpoint. Endpoint yang butuh body atau token diarahkan ke Swagger.</p>
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