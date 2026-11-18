"""Custom Swagger UI page with a light/dark theme toggle.

FastAPI's default docs page is reused (so asset versions and OpenAPI wiring
stay correct), then a small, self-contained toggle is injected before
``</body>``. The choice is persisted in ``localStorage``.
"""

from fastapi.openapi.docs import get_swagger_ui_html

_THEME_SNIPPET = """
<style>
  #theme-toggle {
    position: fixed; bottom: 20px; right: 20px; z-index: 10000;
    padding: 8px 14px; border-radius: 999px; cursor: pointer;
    font: 600 13px/1.2 system-ui, sans-serif; border: 1px solid #bbb;
    background: #fff; color: #222; box-shadow: 0 2px 8px rgba(0,0,0,.15);
  }
  #theme-toggle:hover { opacity: .9; }
  body.dark-mode { background: #121212 !important; }
  body.dark-mode .swagger-ui { color: #e6e6e6; }
  body.dark-mode .swagger-ui .info .title,
  body.dark-mode .swagger-ui .opblock-tag,
  body.dark-mode .swagger-ui label,
  body.dark-mode .swagger-ui .tab li,
  body.dark-mode .swagger-ui .model-title,
  body.dark-mode .swagger-ui table thead tr th,
  body.dark-mode .swagger-ui .parameter__name,
  body.dark-mode .swagger-ui .parameter__type,
  body.dark-mode .swagger-ui .prop-type,
  body.dark-mode .swagger-ui .prop-format,
  body.dark-mode .swagger-ui .markdown p,
  body.dark-mode .swagger-ui .renderedMarkdown p,
  body.dark-mode .swagger-ui .response-col_status { color: #e6e6e6; }
  body.dark-mode .swagger-ui .opblock,
  body.dark-mode .swagger-ui section.models,
  body.dark-mode .swagger-ui .model-box { background: #1e1e1e; border-color: #333; }
  body.dark-mode .swagger-ui .opblock .opblock-summary { border-color: #333; }
  body.dark-mode .swagger-ui input[type=text],
  body.dark-mode .swagger-ui textarea,
  body.dark-mode .swagger-ui select { background: #1e1e1e; color: #e6e6e6; border-color: #444; }
  body.dark-mode .swagger-ui .btn { border-color: #555; color: #e6e6e6; }
  body.dark-mode .swagger-ui .topbar { background: #1a1a1a; }
  body.dark-mode .swagger-ui .highlight-code,
  body.dark-mode .swagger-ui .microlight { background: #111 !important; }
</style>
<button id="theme-toggle" type="button" aria-label="Toggle dark mode">Dark mode</button>
<script>
(function () {
  var btn = document.getElementById('theme-toggle');
  var KEY = 'mini-shop-theme';
  function apply(theme) {
    var dark = theme === 'dark';
    document.body.classList.toggle('dark-mode', dark);
    if (btn) { btn.textContent = dark ? 'Light mode' : 'Dark mode'; }
  }
  apply(localStorage.getItem(KEY) || 'light');
  if (btn) {
    btn.addEventListener('click', function () {
      var next = document.body.classList.contains('dark-mode') ? 'light' : 'dark';
      localStorage.setItem(KEY, next);
      apply(next);
    });
  }
})();
</script>
"""


def build_swagger_docs_html(*, openapi_url: str, title: str) -> str:
    """Return FastAPI's Swagger UI HTML with a dark-mode toggle injected."""
    response = get_swagger_ui_html(openapi_url=openapi_url, title=title)
    html = response.body.decode("utf-8")
    return html.replace("</body>", _THEME_SNIPPET + "</body>")
