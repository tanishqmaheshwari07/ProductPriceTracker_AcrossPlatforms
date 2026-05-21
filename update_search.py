import os
import sys

# FIX #8: use __file__ so script works from any directory, not just repo root
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_JS_PATH = os.path.join(BASE_DIR, 'static', 'js', 'app.js')

# FIX #9: Added main guard so the script doesn't run on import
if __name__ == '__main__':

    with open(APP_JS_PATH, 'r', encoding='utf-8') as f:
        code = f.read()

    # ── FIX #10: Idempotency check — skip if already patched ──────────────────
    if 'async function refresh(query' in code:
        print("update_search.py: app.js already patched — skipping.")
        sys.exit(0)

    # ── Patch 1: Make refresh accept a query parameter ────────────────────────
    old_refresh = """ async function refresh() {
        grid.innerHTML = `
        <div class="skeleton-card"><div class="skeleton-shine"></div><div class="sk-block sk-tall"></div><div class="sk-block sk-med"></div><div class="sk-block sk-short"></div></div>
        <div class="skeleton-card"><div class="skeleton-shine"></div><div class="sk-block sk-tall"></div><div class="sk-block sk-med"></div><div class="sk-block sk-short"></div></div>
        <div class="skeleton-card"><div class="skeleton-shine"></div><div class="sk-block sk-tall"></div><div class="sk-block sk-med"></div><div class="sk-block sk-short"></div></div>
        `;
        try {
            const res = await fetch('/api/products');"""

    new_refresh = """ async function refresh(query = '') {
        grid.innerHTML = `
        <div class="skeleton-card"><div class="skeleton-shine"></div><div class="sk-block sk-tall"></div><div class="sk-block sk-med"></div><div class="sk-block sk-short"></div></div>
        <div class="skeleton-card"><div class="skeleton-shine"></div><div class="sk-block sk-tall"></div><div class="sk-block sk-med"></div><div class="sk-block sk-short"></div></div>
        <div class="skeleton-card"><div class="skeleton-shine"></div><div class="sk-block sk-tall"></div><div class="sk-block sk-med"></div><div class="sk-block sk-short"></div></div>
        `;
        try {
            const url = query ? `/api/products?q=${encodeURIComponent(query)}` : '/api/products';
            const res = await fetch(url);"""

    # FIX #11: Validate replacement succeeded instead of silently failing
    new_code = code.replace(old_refresh, new_refresh)
    if new_code == code:
        print("ERROR: Patch 1 failed — 'old_refresh' string not found in app.js.")
        print("The file may have changed. Please patch manually.")
        sys.exit(1)
    code = new_code
    print("Patch 1 applied: refresh() now accepts a query parameter.")

    # ── Patch 2: Expose refresh in Products return ────────────────────────────
    old_products_return = "return { init };"
    new_products_return = "return { init, refresh };"

    new_code = code.replace(old_products_return, new_products_return, 1)
    if new_code == code:
        print("ERROR: Patch 2 failed — 'return { init };' not found in app.js.")
        sys.exit(1)
    code = new_code
    print("Patch 2 applied: refresh exposed in Products return.")

    # ── Patch 3: Call Products.refresh inside sendMessage ─────────────────────
    old_send_msg = """        if (data.reply) {
                appendMessage('ai', data.reply);
            } else {"""

    new_send_msg = """        if (data.reply) {
                appendMessage('ai', data.reply);
                // Also refresh the product grid with the searched query
                Products.refresh(text);
            } else {"""

    new_code = code.replace(old_send_msg, new_send_msg)
    if new_code == code:
        print("ERROR: Patch 3 failed — sendMessage block not found in app.js.")
        sys.exit(1)
    code = new_code
    print("Patch 3 applied: Products.refresh called inside sendMessage.")

    # ── Write patched file ────────────────────────────────────────────────────
    with open(APP_JS_PATH, 'w', encoding='utf-8') as f:
        f.write(code)

    print(f"\nDone! app.js successfully patched at: {APP_JS_PATH}")
