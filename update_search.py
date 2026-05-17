with open('static/js/app.js', 'r', encoding='utf-8') as f:
    code = f.read()

# Make refresh accept a query parameter
old_refresh = """  async function refresh() {
    grid.innerHTML = `
      <div class="skeleton-card"><div class="skeleton-shine"></div><div class="sk-block sk-tall"></div><div class="sk-block sk-med"></div><div class="sk-block sk-short"></div></div>
      <div class="skeleton-card"><div class="skeleton-shine"></div><div class="sk-block sk-tall"></div><div class="sk-block sk-med"></div><div class="sk-block sk-short"></div></div>
      <div class="skeleton-card"><div class="skeleton-shine"></div><div class="sk-block sk-tall"></div><div class="sk-block sk-med"></div><div class="sk-block sk-short"></div></div>
    `;
    try {
      const res = await fetch('/api/products');"""

new_refresh = """  async function refresh(query = '') {
    grid.innerHTML = `
      <div class="skeleton-card"><div class="skeleton-shine"></div><div class="sk-block sk-tall"></div><div class="sk-block sk-med"></div><div class="sk-block sk-short"></div></div>
      <div class="skeleton-card"><div class="skeleton-shine"></div><div class="sk-block sk-tall"></div><div class="sk-block sk-med"></div><div class="sk-block sk-short"></div></div>
      <div class="skeleton-card"><div class="skeleton-shine"></div><div class="sk-block sk-tall"></div><div class="sk-block sk-med"></div><div class="sk-block sk-short"></div></div>
    `;
    try {
      const url = query ? `/api/products?q=${encodeURIComponent(query)}` : '/api/products';
      const res = await fetch(url);"""

code = code.replace(old_refresh, new_refresh)

# Expose refresh in Products
old_products_return = "return { init };"
new_products_return = "return { init, refresh };"
code = code.replace(old_products_return, new_products_return, 1) # Only the first one which is Products

# Call Products.refresh inside sendMessage
old_send_msg = """      if (data.reply) {
        appendMessage('ai', data.reply);
      } else {"""
new_send_msg = """      if (data.reply) {
        appendMessage('ai', data.reply);
        // Also refresh the product grid with the searched query
        Products.refresh(text);
      } else {"""
code = code.replace(old_send_msg, new_send_msg)

with open('static/js/app.js', 'w', encoding='utf-8') as f:
    f.write(code)
