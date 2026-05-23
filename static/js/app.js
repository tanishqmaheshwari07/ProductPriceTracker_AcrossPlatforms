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
/* ----------------------------------------------------------------
   2.5. PHASE 4 FRONTEND MODULES (Auth, Watchlist, recommendations)
---------------------------------------------------------------- */
const Auth = (() => {
  const overlay = document.getElementById('authModalOverlay');
  const closeBtn = document.getElementById('authCloseBtn');
  const userChip = document.getElementById('userChip');
  
  const tabLoginBtn = document.getElementById('tabLoginBtn');
  const tabRegisterBtn = document.getElementById('tabRegisterBtn');
  const loginForm = document.getElementById('loginForm');
  const registerForm = document.getElementById('registerForm');
  
  const loginErrorMsg = document.getElementById('loginErrorMsg');
  const registerErrorMsg = document.getElementById('registerErrorMsg');
  
  const userNameEl = document.getElementById('userName');
  const userPlanEl = document.getElementById('userPlan');
  const userAvatarEl = document.getElementById('userAvatar');
  
  let userObject = null;

  function showModal() {
    overlay.style.display = 'flex';
    switchTab('login');
  }

  function hideModal() {
    overlay.style.display = 'none';
  }

  function switchTab(tab) {
    if (tab === 'login') {
      tabLoginBtn.classList.add('active');
      tabRegisterBtn.classList.remove('active');
      loginForm.style.display = 'flex';
      registerForm.style.display = 'none';
    } else {
      tabLoginBtn.classList.remove('active');
      tabRegisterBtn.classList.add('active');
      loginForm.style.display = 'none';
      registerForm.style.display = 'flex';
    }
  }

  async function checkStatus() {
    try {
      const res = await fetch('/api/auth/status');
      const data = await res.json();
      if (data.authenticated) {
        userObject = data.user;
        userNameEl.textContent = userObject.name || userObject.email;
        userPlanEl.textContent = userObject.plan || 'Free Plan';
        userAvatarEl.textContent = (userObject.name || userObject.email).substring(0, 2).toUpperCase();
        
        document.getElementById('recFeedContainer').style.display = 'block';
        PersonalizedRecommendations.load();
        WatchlistModule.load();
      } else {
        userObject = null;
        userNameEl.textContent = 'Guest User';
        userPlanEl.textContent = 'Sign In / Register';
        userAvatarEl.textContent = 'G';
        document.getElementById('recFeedContainer').style.display = 'none';
        document.getElementById('watchlistGrid').innerHTML = `
          <p style="color: #aaa; padding: 20px; grid-column: 1/-1; text-align: center;">Sign in to view and manage your watchlist.</p>
        `;
        const countBadge = document.getElementById('watchlistSidebarCount');
        if (countBadge) countBadge.textContent = '0';
        const trackedCount = document.getElementById('wlTrackedCount');
        if (trackedCount) trackedCount.textContent = '0 Items';
        const savingsEl = document.getElementById('wlPotentialSavings');
        if (savingsEl) savingsEl.textContent = '₹0';
      }
    } catch (e) {
      console.error("Auth status check failed:", e);
    }
  }

  function init() {
    if (userChip) {
      userChip.addEventListener('click', () => {
        if (!userObject) {
          showModal();
        } else {
          if (confirm("Do you want to log out?")) {
            logout();
          }
        }
      });
    }

    if (closeBtn) closeBtn.addEventListener('click', hideModal);
    if (tabLoginBtn) tabLoginBtn.addEventListener('click', () => switchTab('login'));
    if (tabRegisterBtn) tabRegisterBtn.addEventListener('click', () => switchTab('register'));

    if (loginForm) {
      loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        loginErrorMsg.textContent = '';
        const email = document.getElementById('loginEmail').value;
        const password = document.getElementById('loginPassword').value;
        
        try {
          const res = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
          });
          const data = await res.json();
          if (res.ok) {
            hideModal();
            await checkStatus();
            Products.refresh(); 
          } else {
            loginErrorMsg.textContent = data.error || 'Login failed';
          }
        } catch (e) {
          loginErrorMsg.textContent = 'Server error. Please try again.';
        }
      });
    }

    if (registerForm) {
      registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        registerErrorMsg.textContent = '';
        const name = document.getElementById('registerName').value;
        const email = document.getElementById('registerEmail').value;
        const password = document.getElementById('registerPassword').value;
        
        try {
          const res = await fetch('/api/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, email, password })
          });
          const data = await res.json();
          if (res.ok) {
            const loginRes = await fetch('/api/auth/login', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ email, password })
            });
            if (loginRes.ok) {
              hideModal();
              await checkStatus();
              Products.refresh();
            } else {
              switchTab('login');
              loginErrorMsg.textContent = 'Account created! Please sign in.';
            }
          } else {
            registerErrorMsg.textContent = data.error || 'Registration failed';
          }
        } catch (e) {
          registerErrorMsg.textContent = 'Server error. Please try again.';
        }
      });
    }
  }

  async function logout() {
    try {
      await fetch('/api/auth/logout', { method: 'POST' });
      await checkStatus();
      Products.refresh();
    } catch (e) {
      console.error(e);
    }
  }

  return { init, checkStatus, isAuthenticated: () => !!userObject, showModal };
})();

const WatchlistModule = (() => {
  const grid = document.getElementById('watchlistGrid');
  const countBadge = document.getElementById('watchlistSidebarCount');
  
  async function load() {
    if (!Auth.isAuthenticated()) return;
    try {
      const res = await fetch('/api/watchlist');
      const data = await res.json();
      
      if (countBadge) countBadge.textContent = data.length;
      
      const trackedCount = document.getElementById('wlTrackedCount');
      if (trackedCount) trackedCount.textContent = `${data.length} Items`;
      
      loadAnalytics();
      render(data);
    } catch (e) {
      console.error("Watchlist loading failed:", e);
    }
  }

  async function loadAnalytics() {
    try {
      const res = await fetch('/api/analytics/dashboard');
      const data = await res.json();
      const savingsEl = document.getElementById('wlPotentialSavings');
      if (savingsEl) {
        savingsEl.textContent = `₹${formatINR(data.potential_savings)}`;
      }
    } catch (e) {
      console.log(e);
    }
  }

  function render(items) {
    if (!grid) return;
    if (items.length === 0) {
      grid.innerHTML = `
        <p style="color: #aaa; padding: 40px; grid-column: 1/-1; text-align: center;">
          Your watchlist is empty. Search for products and click <strong>Watch</strong> to add them here!
        </p>
      `;
      return;
    }

    grid.innerHTML = items.map((item, idx) => {
      const p = item.product;
      const target = item.target_price ? `₹${formatINR(item.target_price)}` : 'Any Price Drop';
      const current = item.current_price ? `₹${formatINR(item.current_price)}` : 'N/A';
      
      let priceDiffHtml = '';
      if (item.current_price && item.target_price && item.current_price > item.target_price) {
        const diff = item.current_price - item.target_price;
        priceDiffHtml = `<div style="font-size: 0.75rem; color: #ffb84d; margin-top: 4px;">₹${formatINR(diff)} above target</div>`;
      } else if (item.current_price && item.target_price && item.current_price <= item.target_price) {
        priceDiffHtml = `<div style="font-size: 0.75rem; color: #00ff9d; margin-top: 4px;">Target reached! 📉</div>`;
      }

      return `
        <div class="product-card" style="animation-delay:${idx * 0.08}s; display: flex; flex-direction: column;">
          <div class="pc-store-name" style="font-size: 1.1rem; line-height: 1.3;">${p.title}</div>
          <div style="font-size: 0.8rem; color: #aaa; margin: 5px 0;">Platform: <strong>${item.website}</strong></div>
          
          <div style="margin-top: auto; display: flex; justify-content: space-between; align-items: flex-end; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 10px;">
            <div>
              <div style="font-size: 0.7rem; color: #aaa;">CURRENT PRICE</div>
              <div style="font-size: 1.25rem; font-weight: 800; color: #00ff9d;">${current}</div>
            </div>
            <div style="text-align: right;">
              <div style="font-size: 0.7rem; color: #aaa;">TARGET PRICE</div>
              <div style="font-size: 1.15rem; font-weight: 700; color: #00d4ff;">${target}</div>
            </div>
          </div>
          ${priceDiffHtml}
          
          <button class="pc-cta" style="margin-top: 15px; background: rgba(255,107,107,0.15); border-color: rgba(255,107,107,0.3); color: #ff6b6b;" onclick="WatchlistModule.remove(${item.id})">Remove From Watchlist</button>
        </div>
      `;
    }).join('');
  }

  async function add(prodId, title, targetVal) {
    if (!Auth.isAuthenticated()) {
      Auth.showModal();
      return;
    }
    const targetPrice = targetVal ? parseInt(targetVal, 10) : null;
    try {
      const res = await fetch('/api/watchlist/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          product_id: prodId,
          product_title: title,
          target_price: targetPrice
        })
      });
      const data = await res.json();
      if (res.ok) {
        alert(data.message);
        load();
      } else {
        alert(data.error || 'Failed to watchlist product');
      }
    } catch (e) {
      console.error(e);
    }
  }

  async function remove(watchlistId) {
    if (!confirm("Are you sure you want to remove this product?")) return;
    try {
      const res = await fetch(`/api/watchlist/remove/${watchlistId}`, {
        method: 'DELETE'
      });
      if (res.ok) {
        load();
      } else {
        alert('Failed to remove item');
      }
    } catch (e) {
      console.error(e);
    }
  }

  return { load, add, remove };
})();

const PersonalizedRecommendations = (() => {
  const grid = document.getElementById('recGrid');
  
  async function load() {
    try {
      const res = await fetch('/api/recommendations');
      const data = await res.json();
      render(data);
    } catch (e) {
      console.error("Failed to load recommendations:", e);
    }
  }

  function render(recs) {
    if (!grid) return;
    if (recs.length === 0) {
      grid.innerHTML = '<p style="color: #aaa; padding: 20px; text-align: center; grid-column: 1/-1;">Analyzing your shopping interests to generate personalized deals...</p>';
      return;
    }
    
    grid.innerHTML = recs.map((r, idx) => {
      return `
        <div class="product-card" style="animation-delay:${idx * 0.08}s; display: flex; flex-direction: column;">
          <div class="pc-top">
            <div style="background: linear-gradient(90deg, #ff007a, #7928ca); color: #fff; padding: 4px 8px; border-radius: 4px; font-size: 0.7rem; font-weight: bold;">
              ${r.badge} (Score: ${r.deal_score})
            </div>
          </div>
          <div class="pc-store-name" style="font-size: 1rem; font-weight: bold; margin-top: 10px;">${r.title}</div>
          <div style="font-size: 0.8rem; color: #aaa; margin: 4px 0;">Category: ${r.category} · Brand: ${r.brand}</div>
          
          <div class="pc-price-row" style="margin-top: auto; padding-top: 10px;">
            <div class="pc-price"><span class="currency">₹</span>${formatINR(r.price)}</div>
            ${r.original_price > r.price ? `<div class="pc-orig-price">₹${formatINR(r.original_price)}</div>` : ''}
          </div>
          
          <button class="pc-cta" onclick="window.open('${r.buy_url}','_blank')" style="margin-top: 12px; background: linear-gradient(135deg, var(--teal), #0090c0); color: #000; font-weight: bold;">Buy on ${r.store.charAt(0).toUpperCase() + r.store.slice(1)}</button>
        </div>
      `;
    }).join('');
  }

  return { load };
})();

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

  /** Build HTML for a single product variant card */
  function buildCard(p, index) {
    // Find absolute cheapest platform
    let absoluteLowest = null;
    let absoluteStore = null;
    let platformsHtml = '';
    let backlogHtml = '';
    
    // Sort platforms by lowest price to find the absolute best
    const sortedPlatforms = Object.entries(p.platforms).sort((a, b) => a[1].lowest_price - b[1].lowest_price);
    
    // Determine absolute lowest using the RecommendationEngine's chosen best_platform if available
    if (p.best_platform && p.platforms[p.best_platform]) {
      absoluteStore = p.best_platform;
      absoluteLowest = p.platforms[p.best_platform];
    } else {
      // Fallback
      if (sortedPlatforms.length > 0) {
        absoluteStore = sortedPlatforms[0][0];
        absoluteLowest = sortedPlatforms[0][1];
      }
    }
    
    if (!absoluteLowest) return ''; // Skip if empty
    
    // Build backlog dropdown
    for (const [store, data] of sortedPlatforms) {
        let storeEmoji = store.toLowerCase() === 'amazon' ? '🛒' : '🏪';
        backlogHtml += `
          <div class="backlog-store-group">
            <h4 style="margin: 10px 0 5px 0; font-size: 0.9rem; color: #fff;">${storeEmoji} ${store.charAt(0).toUpperCase() + store.slice(1)}</h4>
            <ul style="list-style: none; padding: 0; margin: 0; font-size: 0.85rem; color: #ccc;">
        `;
        
        data.all_sellers_backlog.forEach(seller => {
            backlogHtml += `
              <li style="display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px solid rgba(255,255,255,0.1);">
                <span>${seller.seller_name}</span>
                <span>
                  <strong style="color: #00ff9d;">₹${formatINR(seller.price)}</strong>
                  <a href="${seller.link}" target="_blank" style="color: #00d4ff; text-decoration: none; margin-left: 8px;">Buy ↗</a>
                </span>
              </li>
            `;
        });
        
        backlogHtml += `</ul></div>`;
    }

    const ctaText = `Buy on ${absoluteStore.charAt(0).toUpperCase() + absoluteStore.slice(1)} for ₹${formatINR(absoluteLowest.lowest_price)}`;
    const imgHtml = p.base_image_url ? `<img src="${p.base_image_url}" alt="${p.product_title}" style="width: 100%; height: 160px; object-fit: contain; margin-bottom: 10px; border-radius: 8px; background: rgba(0,0,0,0.2);">` : '';

    const recommendation = absoluteLowest.recommendation;
    let badgeHtml = '';
    if (recommendation) {
        let badgeColor = recommendation.deal_score > 85 ? 'linear-gradient(90deg, #ff007a, #7928ca)' : 'rgba(255, 193, 7, 0.2)';
        let textColor = recommendation.deal_score > 85 ? '#fff' : '#ffc107';
        badgeHtml = `<div style="margin-top: 8px; display: inline-block; background: ${badgeColor}; color: ${textColor}; padding: 6px 12px; border-radius: 6px; font-size: 0.8rem; font-weight: bold; border: 1px solid rgba(255,255,255,0.2); box-shadow: 0 0 10px rgba(255,0,122,0.3);">
            ${recommendation.badge} (Score: ${recommendation.deal_score})
            <div style="font-size: 0.7rem; font-weight: normal; margin-top: 4px; opacity: 0.9;">
                ${recommendation.reasons.map(r => `• ${r}`).join('<br>')}
            </div>
        </div>`;
    }

    return `
      <div class="product-card" style="animation-delay:${index * 0.08}s; display: flex; flex-direction: column;">
        <div class="pc-glow"></div>
        ${imgHtml}
        <div class="pc-top">
          <div class="pc-store-info" style="width: 100%;">
            <div class="pc-store-name" style="font-size: 1.1rem; white-space: normal; line-height: 1.3;">${p.product_title}</div>
            ${badgeHtml}
            ${!badgeHtml && p.match_quality === 'strong' && p.match_type !== 'exact' ? `<div style="margin-top: 8px; display: inline-block; background: rgba(0, 255, 157, 0.1); color: #00ff9d; padding: 4px 8px; border-radius: 4px; font-size: 0.75rem; border: 1px solid rgba(0, 255, 157, 0.3);">✨ AI Verified Match (${p.match_confidence}%)</div>` : ''}
            ${!badgeHtml && p.match_quality === 'possible' ? `<div style="margin-top: 8px; display: inline-block; background: rgba(255, 193, 7, 0.1); color: #ffc107; padding: 4px 8px; border-radius: 4px; font-size: 0.75rem; border: 1px solid rgba(255, 193, 7, 0.3);">⚠️ Possible Match (${p.match_confidence}%)</div>` : ''}
          </div>
        </div>
        <div class="pc-price-row" style="margin-top: auto; padding-top: 15px;">
          <div class="pc-price"><span class="currency">₹</span>${formatINR(absoluteLowest.lowest_price)}</div>
        </div>
        
        <button class="pc-cta" onclick="window.open('${absoluteLowest.direct_seller_link}','_blank')" style="margin-top: 15px;">${ctaText}</button>
        
        <div style="margin-top: 10px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 10px;">
          ${Auth.isAuthenticated() 
            ? `
              <div class="wl-target-input-wrap">
                <input type="number" class="wl-target-input" placeholder="Target Price (₹)" id="targetPrice-${index}">
                <button class="wl-save-btn" onclick="WatchlistModule.add(${p.product_id || 'null'}, '${p.product_title.replace(/'/g, "\\'")}', document.getElementById('targetPrice-${index}').value)">Watch</button>
              </div>
            `
            : `<button class="wl-save-btn" style="width: 100%; padding: 8px; background: rgba(255,255,255,0.05); color: #aaa;" onclick="Auth.showModal()">Login to Watch</button>`
          }
        </div>
        
        <details style="margin-top: 10px; cursor: pointer; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 10px;">
          <summary style="font-size: 0.85rem; color: #aaa; outline: none;">View All Sellers (${p.platforms[absoluteStore].all_sellers_backlog.length}+)</summary>
          <div style="margin-top: 10px; padding: 10px; background: rgba(0,0,0,0.3); border-radius: 6px; max-height: 200px; overflow-y: auto;">
             ${backlogHtml}
          </div>
        </details>
      </div>
    `;
  }

  /** Render all product cards, with a proper empty-state message */
  function render(data) {
    /*
     * BUG FIX: Previously, when the API returned an empty results array the
     * grid just went blank — no feedback to the user at all.
     *
     * Two empty cases are handled separately:
     *   1. No query typed yet  → prompt the user to search.
     *   2. Query returned 0 results  → tell the user nothing was found.
     */
    if (!data || data.length === 0) {
      const noQuery = !currentQuery;
      grid.innerHTML = `
        <div style="
          grid-column: 1 / -1;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 60px 20px;
          text-align: center;
          color: #aaa;
        ">
          <div style="font-size: 3rem; margin-bottom: 16px;">${noQuery ? '🔍' : '😕'}</div>
          <h3 style="font-size: 1.3rem; color: #fff; margin-bottom: 8px;">
            ${noQuery ? 'Search for any product' : 'No results found'}
          </h3>
          <p style="font-size: 0.95rem; max-width: 400px; line-height: 1.6;">
            ${noQuery
              ? 'Type a product name in the search bar above — e.g. <em>"wireless earbuds"</em>, <em>"Samsung TV"</em>, or <em>"iPhone 16"</em> — and we\'ll compare prices across Amazon, Flipkart, Croma, and more.'
              : `We couldn't find any matching listings for <strong style="color:#fff;">"${currentQuery}"</strong>. Try a shorter or different search term.`
            }
          </p>
        </div>
      `;
      return;
    }
    grid.innerHTML = data.map((p, i) => buildCard(p, i)).join('');
  }

  /** Sort variants by lowest price */
  function sortProducts(key, data) {
    const sorted = [...data];
    const getLowest = (p) => {
      const prices = Object.values(p.platforms).map(x => x.lowest_price);
      return prices.length ? Math.min(...prices) : 999999999;
    };
    switch (key) {
      case 'price-asc':  return sorted.sort((a, b) => getLowest(a) - getLowest(b));
      case 'price-desc': return sorted.sort((a, b) => getLowest(b) - getLowest(a));
      default:           return sorted;
    }
  }

  // Track the current active query so render() can build appropriate empty-state messages
  let currentQuery = '';

  /** Fetch product data from the server and render the grid */
  async function refresh(query = '') {
    /*
     * BUG FIX: Previously, when no query was supplied, the function still
     * showed skeleton loaders and fired a fetch to /api/products (no ?q=).
     * The server returned mock iPhone data with dead "#" buy links.
     *
     * Fix: skip the fetch entirely when there is no query and show the
     * empty/welcome state immediately.
     */
    currentQuery = query.trim();

    if (!currentQuery) {
      currentProductData = [];
      render([]);
      return;
    }

    // Show skeleton loaders while fetching
    grid.innerHTML = `
      <div class="skeleton-card"><div class="skeleton-shine"></div><div class="sk-block sk-tall"></div><div class="sk-block sk-med"></div><div class="sk-block sk-short"></div></div>
      <div class="skeleton-card"><div class="skeleton-shine"></div><div class="sk-block sk-tall"></div><div class="sk-block sk-med"></div><div class="sk-block sk-short"></div></div>
      <div class="skeleton-card"><div class="skeleton-shine"></div><div class="sk-block sk-tall"></div><div class="sk-block sk-med"></div><div class="sk-block sk-short"></div></div>
    `;

    try {
      const url = `/api/products?q=${encodeURIComponent(currentQuery)}`;
      const res = await fetch(url);
      const data = await res.json();

      // Fetch history / prediction charts in background
      const queryToFetch = data.search_query || currentQuery;
      if (typeof Charts !== 'undefined' && Charts.fetchHistory) {
        Charts.fetchHistory(queryToFetch).then(histData => {
          Charts.renderHistoricalChart(histData);
        });
        if (typeof Prediction !== 'undefined' && Prediction.fetchPrediction) {
          Prediction.fetchPrediction(queryToFetch).then(predData => {
            Prediction.renderPrediction(predData);
            Charts.renderPredictionChart(predData);
          });
        }
      }

      currentProductData = data.results || [];

      // Update the section title
      if (data.search_query) {
        const titleEl = document.getElementById('productTitle');
        if (titleEl) {
          titleEl.innerText = data.search_query.charAt(0).toUpperCase() + data.search_query.slice(1);
        }
      }

      render(sortProducts(sortSelect.value, currentProductData));
    } catch (e) {
      console.error(e);
      grid.innerHTML = '<p style="color: #ff6b6b; padding: 20px;">Error loading products from server. Please try again.</p>';
    }
  }

  function init() {
    // Show empty/welcome state on load — do NOT auto-fetch
    render([]);

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
   6.5. PREDICTION MODULE
---------------------------------------------------------------- */
const Prediction = (() => {
  async function fetchPrediction(query) {
    if (!query) return null;
    try {
      const res = await fetch('/api/predict?q=' + encodeURIComponent(query));
      if (!res.ok) return null;
      return await res.json();
    } catch (e) {
      console.error(e);
      return null;
    }
  }

  function renderPrediction(data) {
    if (!data || !data.predicted_price || data.predicted_price === 0) {
      const recCard = document.getElementById('recCard');
      if (recCard) {
          const action = recCard.querySelector('.verdict-action');
          if (action) action.textContent = 'Need More Data';
      }
      return;
    }

    const recCard = document.getElementById('recCard');
    if (recCard) {
      const conf = recCard.querySelector('.rec-confidence-pill');
      if (conf) conf.textContent = `${data.confidence}% confidence`;

      const action = recCard.querySelector('.verdict-action');
      if (action) action.textContent = data.buy_recommendation;

      const reason = recCard.querySelector('.verdict-reason');
      if (reason) {
          if (data.buy_recommendation === 'WAIT') {
              reason.textContent = `High probability of price drop in ${data.prediction_window_days} days. Trend is ${data.trend}.`;
          } else {
              reason.textContent = `Trend is ${data.trend}. Best time to buy is now.`;
          }
      }

      const values = recCard.querySelectorAll('.rdi-value');
      if (values.length >= 3) {
          const dropAmount = (data.current_price - data.predicted_price);
          values[0].textContent = data.expected_drop_percentage > 0 
              ? `−₹${formatINR(dropAmount)} (~${data.expected_drop_percentage}%)` 
              : 'None expected';
          values[1].textContent = `₹${formatINR(data.predicted_price)}`;
          values[2].textContent = data.prediction_window_days > 0 
              ? `In ~${data.prediction_window_days} Days` 
              : 'Immediately';
      }
    }

    const metricsGrid = document.querySelector('.metrics-grid');
    if (metricsGrid) {
      const values = metricsGrid.querySelectorAll('.mc-value');
      const notes = metricsGrid.querySelectorAll('.mc-note');
      const bars = metricsGrid.querySelectorAll('.mc-fill');

      if (values.length >= 6) {
          values[0].textContent = `${Math.min(100, Math.round(data.expected_drop_percentage * 10))}%`;
          if (bars[0]) bars[0].style.width = `${Math.min(100, Math.round(data.expected_drop_percentage * 10))}%`;

          values[1].textContent = data.trend === 'Falling' ? 'Downward ↓' : (data.trend === 'Rising' ? 'Upward ↑' : 'Stable →');
          
          const volStr = data.confidence > 80 ? 'Low' : (data.confidence > 50 ? 'Medium' : 'High');
          values[2].textContent = volStr;
          if (bars[1]) bars[1].style.width = volStr === 'Low' ? '20%' : (volStr === 'Medium' ? '50%' : '80%');

          values[3].textContent = data.buy_recommendation === 'BUY NOW' ? 'Bullish' : 'Cautious';
          
          values[4].textContent = data.prediction_window_days > 0 
              ? `In ${data.prediction_window_days} days` 
              : 'Today';
              
          const dropAmt = data.current_price - data.predicted_price;
          values[5].textContent = dropAmt > 0 ? `₹${formatINR(dropAmt)}` : '₹0';
      }
    }
  }

  return { fetchPrediction, renderPrediction };
})();

/* ----------------------------------------------------------------
   7. CHARTS MODULE (Canvas-based, no external library)
---------------------------------------------------------------- */
const Charts = (() => {
  let instances = {};
  
  function getThemeColors() {
    return {
      grid: 'rgba(255, 255, 255, 0.1)',
      text: '#aaa',
      teal: '#00d4ff',
      mint: '#00ff9d',
      amber: '#ffb84d',
      purple: '#b54dff',
      coral: '#ff7eb3'
    };
  }

  const C = getThemeColors();

  Chart.defaults.color = C.text;
  Chart.defaults.borderColor = C.grid;

  async function fetchHistory(query) {
    if (!query) return [];
    try {
      const res = await fetch('/api/history?q=' + encodeURIComponent(query));
      if (!res.ok) return [];
      return await res.json();
    } catch (e) {
      console.error(e);
      return [];
    }
  }

  function renderHistoricalChart(data) {
    const ctx = document.getElementById('historicalChart');
    if (!ctx) return;
    
    if (instances['historicalChart']) {
        instances['historicalChart'].destroy();
    }

    if (!data || data.length === 0) {
        return;
    }

    // Group by website
    const websites = [...new Set(data.map(d => d.website))];
    const labels = [...new Set(data.map(d => new Date(d.timestamp).toLocaleDateString()))].sort();
    
    const colors = [C.teal, C.mint, C.amber, C.purple, C.coral];
    
    const datasets = websites.map((web, idx) => {
        const webData = data.filter(d => d.website === web);
        const map = {};
        webData.forEach(d => {
            map[new Date(d.timestamp).toLocaleDateString()] = d.price;
        });
        
        return {
            label: web,
            data: labels.map(l => map[l] || null),
            borderColor: colors[idx % colors.length],
            backgroundColor: colors[idx % colors.length] + '33',
            borderWidth: 2,
            tension: 0.4,
            spanGaps: true
        };
    });

    instances['historicalChart'] = new Chart(ctx, {
        type: 'line',
        data: { labels, datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    grid: { color: C.grid }
                },
                x: {
                    grid: { color: C.grid }
                }
            }
        }
    });
  }

  function renderPredictionChart(data) {
    const ctx = document.getElementById('predictionChart');
    if (!ctx) return;
    
    if (instances['predictionChart']) {
        instances['predictionChart'].destroy();
    }

    if (!data || !data.future_dates || data.future_dates.length === 0) {
        return;
    }

    const labels = [new Date().toLocaleDateString(), ...data.future_dates];
    const prices = [data.current_price, ...data.future_prices];

    instances['predictionChart'] = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Predicted Price',
                data: prices,
                borderColor: C.coral,
                backgroundColor: C.coral + '33',
                borderWidth: 2,
                tension: 0.4,
                borderDash: [5, 5],
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    grid: { color: C.grid }
                },
                x: {
                    grid: { color: C.grid }
                }
            }
        }
    });
  }

  function init() {
    // We will refresh the charts whenever a new search happens via refresh()
  }

  return { init, fetchHistory, renderHistoricalChart, renderPredictionChart };
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
  Auth.init();
  Auth.checkStatus();
  
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

