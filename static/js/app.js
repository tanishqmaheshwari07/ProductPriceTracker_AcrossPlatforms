/* ================================================================
   PRICEAI — app.js
   AI-Powered Price Intelligence Platform
   Vanilla JavaScript — No frameworks, no dependencies
   Modular structure, easy to extend with Flask / FastAPI backend
================================================================ */

'use strict';

/* ----------------------------------------------------------------
   1. DEMO DATA — Replace with real API calls later
---------------------------------------------------------------- */



/** @type {Array<string>} AI chat responses for demo */
const AI_RESPONSES = {
  default: `I've analyzed **iPhone 16 Pro (256GB)** across **6 major platforms**.\n\n📊 **Current Best Price:** ₹1,14,900 on Amazon (12% off)\n🤖 **AI Recommendation:** Wait 3–4 weeks — Diwali sale likely to bring prices down to ~₹1,06,400\n📉 **Drop Probability:** 78%\n\nWould you like to see the full price history and ML forecast chart?`,

  iphone: `🔍 **iPhone 16 Pro Analysis**\n\n**Current Best:** Amazon at ₹1,14,900\n**Predicted Price (Oct 15):** ₹1,06,400\n**Expected Saving:** ₹8,500 (7.4%)\n\n⏳ **Verdict: WAIT 3–4 Weeks**\nHistorical data shows iPhone prices drop 6–10% during Diwali. Amazon and Flipkart typically offer maximum discounts. Scroll down to see the full ML forecast! 🚀`,

  macbook: `💻 **MacBook Air M3 (8GB/256GB) — Live Comparison**\n\n| Store | Price | Discount |\n|---|---|---|\n🛒 Amazon | ₹1,09,900 | ₹10,000 off |\n🏪 Flipkart | ₹1,11,499 | 8% off |\n🍎 Apple | ₹1,19,900 | — |\n\n🤖 **AI Says:** Amazon is ₹1,599 cheaper. **Best time to buy is NOW** — price trend shows an upward spike expected next month due to MacBook Pro launch.`,

  ps5: `🎮 **PS5 Slim Price Prediction — Next 30 Days**\n\n📈 **Current Price:** ₹54,990 (Amazon)\n🔮 **Predicted (Nov 1):** ₹49,990 — ₹51,500\n📉 **Drop Probability:** 82%\n⏰ **Best Buy Window:** Oct 20 – Nov 10\n\nThe ML model (LSTM) has analyzed 3 years of PS5 pricing data. Diwali + year-end stock clearance typically creates a 9–14% price window. **Strong recommendation: Wait 3 weeks.** 🎯`,

  tv: `📺 **Samsung QLED TV — Seasonal Buy Analysis**\n\nBest months to buy TVs in India:\n🏆 **#1 October** — Diwali (avg 18% off)\n🥈 **#2 January** — New Year clearance (12%)\n🥉 **#3 July** — Amazon Prime Day (9%)\n\nRight now it's ₹89,990 on Amazon vs ₹97,500 on Flipkart. **Amazon is currently 8.2% cheaper.** AI says wait 3 weeks for Diwali deals to hit ₹74,000–₹78,000 range. 🎯`,

  headphones: `🎧 **Sony WH-1000XM5 Price History**\n\n📊 **12-Month Price Range:** ₹24,990 – ₹34,990\n📍 **Current Price:** ₹28,990 (Amazon)\n📈 **3-Month Avg:** ₹31,200\n\n✅ **AI Verdict: BUY NOW**\nCurrently trading 7% below 3-month average. Price is likely to rise ₹3,000–₹4,000 before festival demand peaks. This is a rare dip — 91% confidence this is a good time to buy. ⚡`,

  jordan: `👟 **Nike Air Jordan 1 Retro High OG**\n\n⚡ **FLASH SALE ACTIVE — Amazon**\nNormal: ₹12,995 → **Now: ₹7,797 (40% OFF)**\nOnly 7 pairs remaining in popular sizes!\n\n⚠️ **Urgency Alert:** This sale expires in ~2 hours. AI tracks Nike discount patterns — 40% off is extremely rare, happening only ~2×/year. Historical data says: **Do not wait.** 🔥`
};

/* ----------------------------------------------------------------
   2. UTILITY HELPERS
---------------------------------------------------------------- */

/**
 * Format a number as Indian Rupees with commas
 * @param {number} amount
 * @returns {string}
 */
function formatINR(amount) {
  return amount.toLocaleString('en-IN');
}

/**
 * Generate star rating string
 * @param {number} rating  e.g. 4.6
 * @returns {string}
 */
function generateStars(rating) {
  const full  = Math.floor(rating);
  const half  = rating % 1 >= 0.5 ? 1 : 0;
  const empty = 5 - full - half;
  return '★'.repeat(full) + (half ? '⯨' : '') + '☆'.repeat(empty);
}

/**
 * Sleep for a given number of milliseconds
 * @param {number} ms
 * @returns {Promise<void>}
 */
const sleep = ms => new Promise(res => setTimeout(res, ms));

/**
 * Animate a number counter from 0 to target
 * @param {HTMLElement} el
 * @param {number} target
 * @param {number} duration ms
 */
function animateCounter(el, target, duration = 1200) {
  let start = null;
  const step = (timestamp) => {
    if (!start) start = timestamp;
    const progress = Math.min((timestamp - start) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3); // ease-out-cubic
    el.textContent = Math.floor(eased * target);
    if (progress < 1) requestAnimationFrame(step);
    else el.textContent = target;
  };
  requestAnimationFrame(step);
}

/* ----------------------------------------------------------------
   3. SIDEBAR MODULE
---------------------------------------------------------------- */
const Sidebar = (() => {
  const sidebar      = document.getElementById('sidebar');
  const toggleBtn    = document.getElementById('sidebarToggle');
  const mainContent  = document.getElementById('mainContent');
  const footer       = document.querySelector('.footer');

  let isCollapsed = false;

  /** Toggle collapsed state */
  function toggle() {
    isCollapsed = !isCollapsed;
    sidebar.classList.toggle('collapsed', isCollapsed);
    mainContent.classList.toggle('sidebar-collapsed', isCollapsed);
    if (footer) footer.classList.toggle('sidebar-collapsed', isCollapsed);
    localStorage.setItem('sidebar-collapsed', isCollapsed);
  }

  /** Restore from localStorage */
  function restore() {
    const saved = localStorage.getItem('sidebar-collapsed') === 'true';
    if (saved) {
      isCollapsed = true;
      sidebar.classList.add('collapsed');
      mainContent.classList.add('sidebar-collapsed');
      if (footer) footer.classList.add('sidebar-collapsed');
    }
  }

  /** Activate sidebar item matching current hash */
  function syncActiveItem() {
    const hash = window.location.hash || '#dashboard';
    document.querySelectorAll('.sidebar-item').forEach(item => {
      item.classList.toggle('active', item.getAttribute('href') === hash);
    });
  }

  function init() {
    restore();
    syncActiveItem();
    toggleBtn.addEventListener('click', toggle);
    window.addEventListener('hashchange', syncActiveItem);

    // Sidebar nav link → also highlight in top nav
    document.querySelectorAll('.sidebar-item, .nav-link').forEach(link => {
      link.addEventListener('click', function () {
        const section = this.getAttribute('data-section') || this.getAttribute('href')?.replace('#', '');
        document.querySelectorAll('.nav-link').forEach(l => {
          l.classList.toggle('active', l.getAttribute('data-section') === section);
        });
      });
    });
  }

  return { init };
})();

/* ----------------------------------------------------------------
   4. SEARCH MODULE (Replaces Chat)
---------------------------------------------------------------- */
const Search = (() => {
  const inputEl       = document.getElementById('chatInput');
  const sendBtn       = document.getElementById('sendBtn');
  const suggestedEl   = document.getElementById('suggestedPrompts');
  const promptsRow    = document.getElementById('promptsRow');

  let hasInteracted = false;

  async function performSearch(text) {
    text = (text || inputEl.value).trim();
    if (!text) return;

    if (!hasInteracted) {
      suggestedEl.style.opacity = '0';
      await sleep(200);
      suggestedEl.style.display = 'none';
      hasInteracted = true;
    }

    inputEl.value = '';
    
    // Call the Products refresh directly
    Products.refresh(text);
  }

  function init() {
    sendBtn.addEventListener('click', () => performSearch());

    inputEl.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        performSearch();
      }
    });

    promptsRow.querySelectorAll('.prompt-chip').forEach(chip => {
      chip.addEventListener('click', () => performSearch(chip.dataset.prompt));
    });
  }

    // Keyboard shortcut ⌘K / Ctrl+K to focus input
    document.addEventListener('keydown', (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        inputEl.focus();
      }
    });

  return { init };
})();
/* ----------------------------------------------------------------
   5. PRODUCTS MODULE
---------------------------------------------------------------- */
const Products = (() => {
  const grid = document.getElementById('productsGrid');
  const sortSelect = document.getElementById('sortSelect');
  const refreshBtn = document.getElementById('refreshBtn');
  let currentProductData = [];

  /** Build HTML for a single product card */
  function buildCard(p, index) {
    const badgesHtml = p.badges.map(b => {
      const labels = { 'best-deal': '🏆 Best Deal', lowest: '💚 Lowest Price', official: '✅ Official', sale: '🔥 Sale' };
      const classes = { 'best-deal': 'badge-best', lowest: 'badge-lowest', official: 'badge-official', sale: 'badge-sale' };
      return `<span class="badge ${classes[b]}">${labels[b]}</span>`;
    }).join('');

    const discountHtml = p.discount > 0
      ? `<span class="pc-orig-price">₹${formatINR(p.originalPrice)}</span>
         <span class="pc-discount">-${p.discount}%</span>`
      : '';

    const cashbackHtml = p.cashback
      ? `<div class="pc-cashback">
           <svg width="12" height="12" viewBox="0 0 24 24" fill="none"><line x1="12" y1="1" x2="12" y2="23" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
           ${p.cashback}
         </div>` : '';

    const availHtml = p.availability === 'Out of Stock Online'
      ? `<span class="pc-no-stock">⚠️ ${p.availability}</span>`
      : `<div class="pc-delivery">
           <svg width="12" height="12" viewBox="0 0 24 24" fill="none"><rect x="1" y="3" width="15" height="13" rx="1" stroke="currentColor" stroke-width="2"/><path d="M16 8h4l3 3v5h-7V8z" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><circle cx="5.5" cy="18.5" r="2.5" stroke="currentColor" stroke-width="2"/><circle cx="18.5" cy="18.5" r="2.5" stroke="currentColor" stroke-width="2"/></svg>
           ${p.delivery}
         </div>`;

    const ctaText = p.availability === 'Out of Stock Online' ? 'Check Availability' : `Buy on ${p.store} →`;

    return `
      <div class="product-card ${p.isBestDeal ? 'best-deal' : ''}" style="animation-delay:${index * 0.08}s">
        <div class="pc-glow"></div>
        <div class="pc-top">
          <div class="pc-store-info">
            <div class="pc-store-emoji">${p.emoji}</div>
            <div>
              <div class="pc-store-name">${p.store}</div>
              <div class="pc-store-type">${p.seller_name || 'Verified Seller'}</div>
            </div>
          </div>
          <div class="pc-badges">${badgesHtml}</div>
        </div>
        <div class="pc-price-row">
          <div class="pc-price"><span class="currency">₹</span>${formatINR(p.price)}</div>
          ${discountHtml}
        </div>
        <div class="pc-rating">
          <span class="stars">${generateStars(p.rating)}</span>
          <span class="pc-rating-num">${p.rating}</span>
          <span class="pc-review-count">(${formatINR(p.reviewCount)} reviews)</span>
        </div>
        ${availHtml}
        ${cashbackHtml}
        <div class="pc-trend">
          <span class="trend-chip ${p.trend}">${p.trendText}</span>
        </div>
        <button class="pc-cta" onclick="window.open('${p.buyUrl}','_blank')">${ctaText}</button>
      </div>
    `;
  }

  /** Render all product cards */
  function render(data) {
    grid.innerHTML = data.map((p, i) => buildCard(p, i)).join('');
  }

  /** Sort products by given key */
  function sortProducts(key, data) {
    const sorted = [...data];
    switch (key) {
      case 'price-asc':  return sorted.sort((a, b) => a.price - b.price);
      case 'price-desc': return sorted.sort((a, b) => b.price - a.price);
      case 'rating':     return sorted.sort((a, b) => b.rating - a.rating);
      case 'discount':   return sorted.sort((a, b) => b.discount - a.discount);
      default:           return sorted;
    }
  }

  /** Simulate a refresh with skeleton effect */
  async function refresh(query = '') {
    grid.innerHTML = `
      <div class="skeleton-card"><div class="skeleton-shine"></div><div class="sk-block sk-tall"></div><div class="sk-block sk-med"></div><div class="sk-block sk-short"></div></div>
      <div class="skeleton-card"><div class="skeleton-shine"></div><div class="sk-block sk-tall"></div><div class="sk-block sk-med"></div><div class="sk-block sk-short"></div></div>
      <div class="skeleton-card"><div class="skeleton-shine"></div><div class="sk-block sk-tall"></div><div class="sk-block sk-med"></div><div class="sk-block sk-short"></div></div>
    `;
    try {
      const url = query ? `/api/products?q=${encodeURIComponent(query)}` : '/api/products';
      const res = await fetch(url);
      const data = await res.json();
      currentProductData = data;
      
      // Update the page title
      if (query) {
        const titleEl = document.getElementById('productTitle');
        if (titleEl) {
          // Capitalize first letter
          titleEl.innerText = query.charAt(0).toUpperCase() + query.slice(1);
        }
      }
      
      render(sortProducts(sortSelect.value, currentProductData));
    } catch (e) {
      console.error(e);
      grid.innerHTML = '<p style="color: #ff6b6b; padding: 20px;">Error loading products from server.</p>';
    }
  }

  function init() {
    refresh();

    sortSelect.addEventListener('change', () => {
      render(sortProducts(sortSelect.value, currentProductData));
    });

    refreshBtn.addEventListener('click', () => refresh());
    
    // Add event listener for the top search bar
    const searchBar = document.getElementById('searchBar');
    if (searchBar) {
      searchBar.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          refresh(searchBar.value.trim());
        }
      });
    }
  }

  return { init, refresh };
})();

/* ----------------------------------------------------------------
   6. ALERTS MODULE
---------------------------------------------------------------- */
const Alerts = (() => {
  const grid = document.getElementById('alertsGrid');

  function buildAlert(a, index) {
    return `
      <div class="alert-card ${a.type}" style="animation-delay:${index * 0.1}s">
        <div class="alert-top">
          <div class="alert-left">
            <div class="alert-icon">${a.icon}</div>
            <div class="alert-meta">
              <span class="alert-product">${a.product}</span>
              <span class="alert-title">${a.title}</span>
            </div>
          </div>
          <span class="alert-time">${a.time}</span>
        </div>
        <p class="alert-message">${a.message}</p>
        <div class="alert-footer">
          <span class="alert-store-tag">${a.store}</span>
          <button class="alert-action">${a.action}</button>
        </div>
      </div>
    `;
  }

  async function init() {
    if (!grid) return;
    try {
      const res = await fetch('/api/alerts');
      const data = await res.json();
      grid.innerHTML = data.map((a, i) => buildAlert(a, i)).join('');
    } catch (e) {
      console.error(e);
    }
  }

  return { init };
})();

/* ----------------------------------------------------------------
   7. CHARTS MODULE (Canvas-based, no external library)
---------------------------------------------------------------- */
const Charts = (() => {

  /* -- Color palette for charts -- */
  const C = {
    teal:   '#00d4ff',
    mint:   '#00ff9d',
    amber:  '#ffb84d',
    coral:  '#ff6b6b',
    purple: '#c084fc',
    grid:   'rgba(255,255,255,0.06)',
    text:   'rgba(238,238,255,0.5)',
    textHi: 'rgba(238,238,255,0.85)',
  };

  /* -- Easing -- */
  function easeOutCubic(t) { return 1 - Math.pow(1 - t, 3); }

  /**
   * Animated line chart renderer
   * @param {HTMLCanvasElement} canvas
   * @param {Object} config
   */
  function drawLineChart(canvas, config) {
    const ctx = canvas.getContext('2d');
    let animProgress = 0;
    let animFrame;

    function resize() {
      const dpr = window.devicePixelRatio || 1;
      const rect = canvas.parentElement.getBoundingClientRect();
      canvas.width  = rect.width  * dpr;
      canvas.height = rect.height * dpr;
      canvas.style.width  = rect.width  + 'px';
      canvas.style.height = rect.height + 'px';
      ctx.scale(dpr, dpr);
    }

    function draw(progress) {
      const W = canvas.clientWidth;
      const H = canvas.clientHeight;
      const PAD = { top: 20, right: 16, bottom: 40, left: 52 };
      const plotW = W - PAD.left - PAD.right;
      const plotH = H - PAD.top  - PAD.bottom;

      ctx.clearRect(0, 0, W, H);

      // Collect all values to determine Y range
      let allVals = [];
      config.datasets.forEach(ds => allVals = allVals.concat(ds.data));
      const minVal = Math.min(...allVals) * 0.975;
      const maxVal = Math.max(...allVals) * 1.015;
      const range  = maxVal - minVal;

      const toX = (i) => PAD.left + (i / (config.labels.length - 1)) * plotW;
      const toY = (v) => PAD.top  + (1 - (v - minVal) / range) * plotH;

      // Draw grid lines
      const gridCount = 5;
      ctx.strokeStyle = C.grid;
      ctx.lineWidth = 1;
      for (let i = 0; i <= gridCount; i++) {
        const y = PAD.top + (i / gridCount) * plotH;
        ctx.beginPath();
        ctx.moveTo(PAD.left, y);
        ctx.lineTo(W - PAD.right, y);
        ctx.stroke();

        // Y axis label
        const val = maxVal - (i / gridCount) * range;
        ctx.fillStyle = C.text;
        ctx.font = `11px 'DM Mono', monospace`;
        ctx.textAlign = 'right';
        ctx.fillText('₹' + Math.round(val / 1000) + 'K', PAD.left - 8, y + 4);
      }

      // X axis labels
      const labelStep = Math.ceil(config.labels.length / 8);
      config.labels.forEach((lbl, i) => {
        if (i % labelStep !== 0) return;
        ctx.fillStyle = C.text;
        ctx.font = `10px 'DM Mono', monospace`;
        ctx.textAlign = 'center';
        ctx.fillText(lbl, toX(i), H - PAD.bottom + 16);
      });

      // Draw each dataset
      config.datasets.forEach(ds => {
        const pts = ds.data.map((v, i) => ({ x: toX(i), y: toY(v) }));
        const cutoff = Math.floor((pts.length - 1) * progress);

        if (pts.length < 2) return;

        // Fill gradient under line
        ctx.save();
        ctx.beginPath();
        ctx.moveTo(pts[0].x, toY(minVal));
        for (let i = 0; i <= cutoff; i++) {
          if (i === 0) ctx.lineTo(pts[0].x, pts[0].y);
          else {
            const prev = pts[i - 1];
            const curr = pts[i];
            const cpx = (prev.x + curr.x) / 2;
            ctx.bezierCurveTo(cpx, prev.y, cpx, curr.y, curr.x, curr.y);
          }
        }
        ctx.lineTo(pts[cutoff].x, toY(minVal));
        ctx.closePath();
        const grad = ctx.createLinearGradient(0, PAD.top, 0, H - PAD.bottom);
        grad.addColorStop(0,   hexToRgba(ds.color, 0.18));
        grad.addColorStop(1,   hexToRgba(ds.color, 0.01));
        ctx.fillStyle = grad;
        ctx.fill();
        ctx.restore();

        // Draw line
        ctx.save();
        ctx.beginPath();
        ctx.strokeStyle = ds.color;
        ctx.lineWidth = 2.5;
        ctx.lineJoin = 'round';
        ctx.lineCap  = 'round';
        for (let i = 0; i <= cutoff; i++) {
          if (i === 0) ctx.moveTo(pts[0].x, pts[0].y);
          else {
            const prev = pts[i - 1];
            const curr = pts[i];
            const cpx = (prev.x + curr.x) / 2;
            ctx.bezierCurveTo(cpx, prev.y, cpx, curr.y, curr.x, curr.y);
          }
        }
        ctx.stroke();
        ctx.restore();

        // Data point dots at cutoff
        if (progress >= 1) {
          pts.forEach((pt, i) => {
            if (i % labelStep !== 0 && i !== pts.length - 1) return;
            ctx.beginPath();
            ctx.arc(pt.x, pt.y, 4, 0, Math.PI * 2);
            ctx.fillStyle = ds.color;
            ctx.fill();
            ctx.strokeStyle = '#06060f';
            ctx.lineWidth = 2;
            ctx.stroke();
          });
        }
      });
    }

    function animate() {
      animProgress = Math.min(animProgress + 0.025, 1);
      draw(easeOutCubic(animProgress));
      if (animProgress < 1) animFrame = requestAnimationFrame(animate);
    }

    resize();
    window.addEventListener('resize', () => { cancelAnimationFrame(animFrame); resize(); animProgress = 0; animate(); });
    animate();
  }

  /**
   * Animated bar chart renderer
   * @param {HTMLCanvasElement} canvas
   * @param {Object} config
   */
  function drawBarChart(canvas, config) {
    const ctx = canvas.getContext('2d');
    let prog = 0;
    let animFrame;

    function resize() {
      const dpr = window.devicePixelRatio || 1;
      const rect = canvas.parentElement.getBoundingClientRect();
      canvas.width  = rect.width  * dpr;
      canvas.height = rect.height * dpr;
      canvas.style.width  = rect.width  + 'px';
      canvas.style.height = rect.height + 'px';
      ctx.scale(dpr, dpr);
    }

    function draw(progress) {
      const W = canvas.clientWidth;
      const H = canvas.clientHeight;
      const PAD = { top: 16, right: 16, bottom: 48, left: 56 };
      const plotW = W - PAD.left - PAD.right;
      const plotH = H - PAD.top  - PAD.bottom;

      ctx.clearRect(0, 0, W, H);

      const maxVal = Math.max(...config.data) * 1.1;
      const barW   = (plotW / config.data.length) * 0.55;
      const gap    = (plotW / config.data.length) * 0.45;

      // Grid
      for (let i = 0; i <= 4; i++) {
        const y = PAD.top + (i / 4) * plotH;
        ctx.strokeStyle = C.grid;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(PAD.left, y);
        ctx.lineTo(W - PAD.right, y);
        ctx.stroke();

        const val = maxVal - (i / 4) * maxVal;
        ctx.fillStyle = C.text;
        ctx.font = `11px 'DM Mono', monospace`;
        ctx.textAlign = 'right';
        ctx.fillText('₹' + Math.round(val / 1000) + 'K', PAD.left - 8, y + 4);
      }

      // Bars
      config.data.forEach((val, i) => {
        const x      = PAD.left + i * (barW + gap) + gap / 2;
        const barH   = (val / maxVal) * plotH * progress;
        const y      = PAD.top + plotH - barH;
        const color  = config.colors[i] || C.teal;
        const radius = 6;

        ctx.save();
        ctx.beginPath();
        ctx.moveTo(x + radius, y);
        ctx.lineTo(x + barW - radius, y);
        ctx.quadraticCurveTo(x + barW, y, x + barW, y + radius);
        ctx.lineTo(x + barW, y + barH);
        ctx.lineTo(x, y + barH);
        ctx.lineTo(x, y + radius);
        ctx.quadraticCurveTo(x, y, x + radius, y);
        ctx.closePath();

        const grad = ctx.createLinearGradient(x, y, x, y + barH);
        grad.addColorStop(0, hexToRgba(color, 0.9));
        grad.addColorStop(1, hexToRgba(color, 0.4));
        ctx.fillStyle = grad;
        ctx.fill();

        // Glow
        ctx.shadowColor = color;
        ctx.shadowBlur  = 12;
        ctx.fill();
        ctx.shadowBlur = 0;
        ctx.restore();

        // Label below
        ctx.fillStyle = C.text;
        ctx.font = `10.5px 'Outfit', sans-serif`;
        ctx.textAlign = 'center';
        ctx.fillText(config.labels[i], x + barW / 2, H - PAD.bottom + 18);

        // Value above bar
        if (progress > 0.7) {
          ctx.fillStyle = C.textHi;
          ctx.font = `bold 11px 'Syne', sans-serif`;
          ctx.fillText('₹' + Math.round(val / 1000) + 'K', x + barW / 2, y - 8);
        }
      });
    }

    function animate() {
      prog = Math.min(prog + 0.025, 1);
      draw(easeOutCubic(prog));
      if (prog < 1) animFrame = requestAnimationFrame(animate);
    }

    resize();
    window.addEventListener('resize', () => { cancelAnimationFrame(animFrame); resize(); prog = 0; animate(); });
    animate();
  }

  /** Hex color to rgba string */
  function hexToRgba(hex, alpha) {
    const r = parseInt(hex.slice(1,3), 16);
    const g = parseInt(hex.slice(3,5), 16);
    const b = parseInt(hex.slice(5,7), 16);
    return `rgba(${r},${g},${b},${alpha})`;
  }

  /* -- Data generators -- */

  function historicalData() {
    const months = ['Oct','Nov','Dec','Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep'];
    return {
      labels: months,
      datasets: [
        {
          label: 'Amazon',
          color: C.teal,
          data: [129900,125000,121000,119900,122000,118500,116000,117500,115000,116900,114900,114900]
        },
        {
          label: 'Flipkart',
          color: C.mint,
          data: [129900,127000,123000,121500,124000,120000,118000,119500,117000,118500,116499,116499]
        },
        {
          label: 'Croma',
          color: C.amber,
          data: [129900,129900,129900,127000,127000,124990,122990,122990,121990,120990,119990,119990]
        }
      ]
    };
  }

  function predictionData() {
    const labels = ['Sep','Oct','Nov','Dec','Jan','Feb'];
    return {
      labels,
      datasets: [
        {
          label: 'Historical',
          color: C.teal,
          data: [116900, 114900, null, null, null, null]
        },
        {
          label: 'Predicted',
          color: C.purple,
          data: [null, 114900, 106400, 108000, 112000, 110500]
        }
      ]
    };
  }

  function comparisonData() {
    return {
      labels: ['Amazon', 'Flipkart', 'Apple', 'Croma', 'Vijay Sales', 'Reliance'],
      data:   [114900, 116499, 129900, 119990, 121000, 123000],
      colors: [C.teal, C.mint, C.coral, C.amber, C.purple, '#ff9f7f']
    };
  }

  function seasonalData() {
    const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
    return {
      labels: months,
      datasets: [
        {
          label: 'Avg Price',
          color: C.teal,
          data: [119000, 121000, 123000, 124000, 124500, 125000, 120000, 122000, 118000, 113000, 114000, 118000]
        }
      ]
    };
  }

  function init() {
    // Use IntersectionObserver to trigger charts when visible
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (!entry.isIntersecting) return;
        const canvas = entry.target;
        observer.unobserve(canvas);

        switch (canvas.id) {
          case 'historicalChart':
            drawLineChart(canvas, historicalData());
            break;
          case 'predictionChart': {
            const pd = predictionData();
            // Filter out nulls for each dataset
            const cleaned = {
              labels: pd.labels,
              datasets: pd.datasets.map(ds => ({
                ...ds,
                data: ds.data.map(v => v === null ? undefined : v).filter(v => v !== undefined)
              }))
            };
            // Draw historical portion
            drawLineChart(canvas, {
              labels: pd.labels,
              datasets: [
                { label: 'Historical', color: C.teal,   data: [116900, 114900, 110000, 106400, 108000, 110500] },
                { label: 'Predicted',  color: C.purple, data: [null,   null,   110000, 106400, 108000, 110500] }
              ].map(ds => ({ ...ds, data: ds.data.filter(v => v !== null) }))
            });
            drawLineChart(canvas, { labels: pd.labels, datasets: [{ label: 'ML Forecast', color: C.purple, data: [116900, 114900, 110000, 106400, 108000, 110500] }] });
            break;
          }
          case 'comparisonChart':
            drawBarChart(canvas, comparisonData());
            break;
          case 'seasonalChart':
            drawLineChart(canvas, seasonalData());
            break;
        }
      });
    }, { threshold: 0.2 });

    ['historicalChart','predictionChart','comparisonChart','seasonalChart'].forEach(id => {
      const canvas = document.getElementById(id);
      if (canvas) observer.observe(canvas);
    });
  }

  return { init };
})();

/* ----------------------------------------------------------------
   8. COUNTER ANIMATIONS MODULE of f
---------------------------------------------------------------- */
const Counters = (() => {
  function init() {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (!entry.isIntersecting) return;
        const el = entry.target;
        const target = parseInt(el.dataset.target, 10);
        animateCounter(el, target);
        observer.unobserve(el);
      });
    }, { threshold: 0.5 });

    document.querySelectorAll('.stat-num[data-target]').forEach(el => {
      observer.observe(el);
    });
  }

  return { init };
})();

/* ----------------------------------------------------------------
   9. TIME FILTER MODULE
---------------------------------------------------------------- */
const TimeFilter = (() => {
  function init() {
    const group = document.getElementById('timeFilter');
    if (!group) return;
    group.querySelectorAll('.tf-btn').forEach(btn => {
      btn.addEventListener('click', function () {
        group.querySelectorAll('.tf-btn').forEach(b => b.classList.remove('active'));
        this.classList.add('active');
        // In production: trigger chart re-render with new period
        // Charts.reload(this.dataset.period);
      });
    });
  }

  return { init };
})();

/* ----------------------------------------------------------------
   10. SMOOTH SCROLL ANCHORS
---------------------------------------------------------------- */
const SmoothScroll = (() => {
  function init() {
    document.querySelectorAll('a[href^="#"]').forEach(link => {
      link.addEventListener('click', function (e) {
        const id = this.getAttribute('href').replace('#', '');
        const target = document.getElementById(id);
        if (!target) return;
        e.preventDefault();
        const offset = 80; // Navbar height clearance
        const top = target.getBoundingClientRect().top + window.pageYOffset - offset;
        window.scrollTo({ top, behavior: 'smooth' });
      });
    });
  }

  return { init };
})();

/* ----------------------------------------------------------------
   11. NAVBAR SCROLL EFFECT
---------------------------------------------------------------- */
const NavbarScroll = (() => {
  function init() {
    const navbar = document.getElementById('navbar');
    window.addEventListener('scroll', () => {
      navbar.style.boxShadow = window.scrollY > 20
        ? '0 4px 30px rgba(0,0,0,0.4)'
        : 'none';
    }, { passive: true });
  }
  return { init };
})();

/* ----------------------------------------------------------------
   12. MOBILE SIDEBAR OVERLAY
---------------------------------------------------------------- */
const MobileSidebar = (() => {
  function init() {
    if (window.innerWidth > 768) return;

    const sidebar = document.getElementById('sidebar');
    const toggle  = document.getElementById('sidebarToggle');
    let open = false;

    toggle.addEventListener('click', () => {
      open = !open;
      sidebar.classList.toggle('mobile-open', open);
    });

    // Close on outside click
    document.addEventListener('click', (e) => {
      if (open && !sidebar.contains(e.target) && !toggle.contains(e.target)) {
        open = false;
        sidebar.classList.remove('mobile-open');
      }
    });
  }

  return { init };
})();

/* ----------------------------------------------------------------
   13. NOTIFICATION BELL CLICK
---------------------------------------------------------------- */
const Notifications = (() => {
  function init() {
    const btn = document.getElementById('notifBtn');
    if (!btn) return;
    btn.addEventListener('click', () => {
      // Scroll to alerts section
      const alerts = document.getElementById('alerts');
      if (alerts) {
        alerts.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  }
  return { init };
})();

/* ----------------------------------------------------------------
   14. APP INIT — Bootstrap everything when DOM is ready
---------------------------------------------------------------- */
document.addEventListener('DOMContentLoaded', () => {
  Sidebar.init();
  Search.init();
  SmoothScroll.init();
  NavbarScroll.init();
  MobileSidebar.init();
  Notifications.init();
  Counters.init();
  TimeFilter.init();

  // Staggered init for data-heavy modules
  setTimeout(() => Products.init(), 100);
  setTimeout(() => Alerts.init(),   200);
  setTimeout(() => Charts.init(),   300);

  console.log('%cPriceAI v1.0 — Frontend loaded ✅', 'color:#00d4ff;font-family:monospace;font-size:14px;font-weight:bold;');
  console.log('%cReady to connect Flask/FastAPI backend via /api/* endpoints', 'color:#00ff9d;font-family:monospace;font-size:11px;');
});
