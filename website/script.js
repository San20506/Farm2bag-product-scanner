/**
 * PriceTrackerPro — Full Dashboard Interactivity
 * Every button, link, and control is wired up.
 */

const API_BASE = 'http://localhost:8001/api/scraper';

/* ── State ── */
let allProducts = [];
let displayedProducts = [];
let currentPage = 1;
const itemsPerPage = 6;
let sortField = null;
let sortAsc = true;
let activeFilters = { instock: false, pricedrop: false };
let currency = 'USD';
let editingSiteKey = null; // null = adding, string = editing

const currencySymbols = { USD: '$', INR: '₹', EUR: '€' };

document.addEventListener('DOMContentLoaded', () => {
    allProducts = getMockData();
    displayedProducts = [...allProducts];
    renderTable(displayedProducts);

    initSearch();
    initSidebarNav();
    initFilters();
    initPagination();
    initExportBtn();
    initNotificationBtn();
    initSettingsBtn();
    initUserMenu();
    initSortableHeaders();
    initModalClose();
    initSourceModal();
});

/* ══════════════════════════════════════════
   SEARCH — live filter by name + specs
   ══════════════════════════════════════════ */
function initSearch() {
    const input = document.getElementById('searchInput');
    input.addEventListener('input', () => {
        applyAllFilters();
    });
}

/* ══════════════════════════════════════════
   SIDEBAR NAV — switch pages / categories
   ══════════════════════════════════════════ */
function initSidebarNav() {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', e => {
            e.preventDefault();
            navItems.forEach(n => n.classList.remove('active'));
            item.classList.add('active');

            const page = item.dataset.page;
            const title = document.getElementById('pageTitle');
            const subtitle = document.getElementById('pageSubtitle');
            const tableCard = document.getElementById('tableCard');
            const filters = document.getElementById('headerFilters');

            // Reset: show table + filters by default
            filters.style.display = 'flex';
            tableCard.style.display = 'flex';

            switch (page) {
                case 'all-products':
                    title.textContent = 'Product Catalog';
                    subtitle.textContent = 'Real-time price aggregation across 42 verified retailers';
                    displayedProducts = [...allProducts];
                    renderTable(displayedProducts);
                    break;
                case 'electronics':
                    title.textContent = 'Electronics';
                    subtitle.textContent = 'Laptops, monitors, keyboards and more';
                    displayedProducts = allProducts.filter(p =>
                        ['Laptop', 'Monitor', 'Keyboard', 'Server'].some(k => p.name.includes(k))
                    );
                    renderTable(displayedProducts);
                    break;
                case 'home-garden':
                    title.textContent = 'Home & Garden';
                    subtitle.textContent = 'Home appliances, garden tools, and décor';
                    displayedProducts = allProducts.filter(p => p.name.includes('Projector'));
                    renderTable(displayedProducts);
                    break;
                case 'fashion':
                    title.textContent = 'Fashion';
                    subtitle.textContent = 'Clothing, accessories, and footwear';
                    displayedProducts = [];
                    renderTable(displayedProducts);
                    break;
                case 'price-alerts':
                    title.textContent = 'Price Alerts';
                    subtitle.textContent = 'Products with significant price changes';
                    filters.style.display = 'none';
                    displayedProducts = allProducts.filter(p => {
                        const v = parseFloat(p.variance);
                        return Math.abs(v) > 5;
                    });
                    renderTable(displayedProducts);
                    break;
                case 'compare-products':
                    title.textContent = 'Compare Products';
                    subtitle.textContent = 'Drop product links below to scrape & compare prices';
                    filters.style.display = 'none';
                    tableCard.style.display = 'none';
                    renderCompareProductsPage();
                    break;
                case 'manage-sources':
                    title.textContent = 'Manage Sources';
                    subtitle.textContent = 'Add, edit, or remove scraping targets';
                    filters.style.display = 'none';
                    tableCard.style.display = 'none';
                    renderManageSourcesPage();
                    break;
            }
            showToast(`Navigated to ${item.textContent.trim()}`);
        });
    });
}

function renderPlaceholderPage(page) {
    const tbody = document.getElementById('tableBody');
    let icon, message;
    if (page === 'preferred-sites') {
        icon = '🌐'; message = 'Configure your preferred retailer sites here. Feature coming soon.';
    } else {
        icon = '⎈'; message = 'Manage your scraping sources and endpoints here. Feature coming soon.';
    }
    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding: 48px; color: var(--text-muted);">
        <div style="font-size:36px; margin-bottom:12px;">${icon}</div>
        <div style="font-size:15px;">${message}</div>
    </td></tr>`;
    document.getElementById('paginationInfo').textContent = '';
}

/* ══════════════════════════════════════════
   COMPARE PRODUCTS — Drop Links & Scrape
   ══════════════════════════════════════════ */
function renderCompareProductsPage() {
    const pageContent = document.getElementById('pageContent');

    // Remove any existing containers
    let existing = document.getElementById('sourceContainer');
    if (existing) existing.remove();
    existing = document.getElementById('compareContainer');
    if (existing) existing.remove();

    const container = document.createElement('div');
    container.id = 'compareContainer';
    container.innerHTML = `
        <div class="url-drop-zone">
            <div class="drop-header">
                <span style="font-size:28px;">🔗</span>
                <h3>Drop Product Links</h3>
                <p>Paste one URL per line — we'll scrape product details automatically</p>
            </div>
            <textarea id="urlInput" class="url-textarea" rows="5"
                placeholder="https://www.bigbasket.com/pd/100001/...
https://www.amazon.in/dp/B0...
https://www.flipkart.com/..."></textarea>
            <div class="drop-actions">
                <span class="url-count" id="urlCount">0 URLs</span>
                <button class="btn btn-primary" id="scrapeUrlsBtn" disabled>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="5 3 19 12 5 21 5 3"/></svg>
                    Scrape & Compare
                </button>
            </div>
        </div>
        <div id="comparisonResults"></div>
    `;
    pageContent.appendChild(container);

    const textarea = document.getElementById('urlInput');
    const countEl = document.getElementById('urlCount');
    const btn = document.getElementById('scrapeUrlsBtn');

    textarea.addEventListener('input', () => {
        const urls = textarea.value.trim().split('\n').filter(u => u.trim().startsWith('http'));
        countEl.textContent = `${urls.length} URL${urls.length !== 1 ? 's' : ''}`;
        btn.disabled = urls.length === 0;
    });

    btn.addEventListener('click', async () => {
        const urls = textarea.value.trim().split('\n')
            .map(u => u.trim())
            .filter(u => u.startsWith('http'));

        if (urls.length === 0) return;
        if (urls.length > 10) {
            showToast('Maximum 10 URLs at a time');
            return;
        }

        btn.disabled = true;
        btn.innerHTML = `
            <svg class="spin" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 12a9 9 0 11-6.219-8.56"/></svg>
            Scraping ${urls.length} URL${urls.length > 1 ? 's' : ''}...
        `;
        showToast(`Scraping ${urls.length} product link${urls.length > 1 ? 's' : ''}...`);

        try {
            const res = await fetch(`${API_BASE.replace('/scraper', '')}/scrape-urls`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ urls }),
            });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();

            showToast(`✅ Scraped ${data.successful}/${data.total} products successfully`);
            displayComparisonResults(data.products);
        } catch (err) {
            showToast(`❌ Scrape failed: ${err.message}`);
        } finally {
            btn.disabled = false;
            btn.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="5 3 19 12 5 21 5 3"/></svg>
                Scrape & Compare
            `;
        }
    });
}

function displayComparisonResults(products) {
    const container = document.getElementById('comparisonResults');
    if (!products || products.length === 0) {
        container.innerHTML = `<div style="text-align:center; padding:32px; color:var(--text-muted);">No products could be scraped.</div>`;
        return;
    }

    // Sort by price (lowest first)
    const sorted = [...products].filter(p => p.success).sort((a, b) => (a.price || Infinity) - (b.price || Infinity));
    const lowestPrice = sorted[0]?.price;

    container.innerHTML = `
        <h3 style="margin:24px 0 16px; font-size:16px; font-weight:700;">Comparison Results (${sorted.length} products)</h3>
        <div class="compare-grid">
            ${sorted.map((p, i) => {
        const isBest = p.price === lowestPrice && lowestPrice != null;
        return `
                <div class="compare-card ${isBest ? 'best-deal' : ''}">
                    ${isBest ? '<div class="best-badge">🏆 Best Price</div>' : ''}
                    ${p.image ? `<div class="compare-img"><img src="${p.image}" alt="${p.name}" onerror="this.style.display='none'"></div>` : ''}
                    <div class="compare-info">
                        <div class="compare-site">${p.site}</div>
                        <div class="compare-name">${p.name || 'Unknown Product'}</div>
                        <div class="compare-price">${p.price != null ? '₹' + p.price.toLocaleString() : 'Price N/A'}</div>
                        ${p.description ? `<div class="compare-desc">${p.description.slice(0, 120)}${p.description.length > 120 ? '...' : ''}</div>` : ''}
                        <a href="${p.url}" target="_blank" class="compare-link">View on ${p.site} →</a>
                    </div>
                </div>
                `;
    }).join('')}
        </div>
        ${products.filter(p => !p.success).length > 0 ? `
            <div style="margin-top:16px; padding:12px; background:var(--danger-bg); border-radius:6px; font-size:13px; color:var(--danger-text);">
                ⚠️ Failed to scrape ${products.filter(p => !p.success).length} URL(s):
                ${products.filter(p => !p.success).map(p => `<div style="margin-top:4px;">${p.url} — ${p.error || 'Unknown error'}</div>`).join('')}
            </div>
        ` : ''}
    `;
}

/* ══════════════════════════════════════════
   MANAGE SOURCES PAGE — live from API
   ══════════════════════════════════════════ */
async function renderManageSourcesPage() {
    const pageContent = document.getElementById('pageContent');

    // Remove any existing source container
    let existing = document.getElementById('sourceContainer');
    if (existing) existing.remove();

    // Create sources container
    const container = document.createElement('div');
    container.id = 'sourceContainer';
    container.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
            <span style="font-size:14px; color:var(--text-muted);">Loading sources...</span>
            <button class="btn btn-primary" id="addSourceBtn">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                Add Source
            </button>
        </div>
        <div class="source-grid" id="sourceGrid"></div>
    `;
    pageContent.appendChild(container);

    // Wire Add Source button
    document.getElementById('addSourceBtn').addEventListener('click', () => openSourceModal());

    // Fetch sites from API
    try {
        const res = await fetch(`${API_BASE}/sites`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const sites = await res.json();
        renderSourceCards(sites);
    } catch (err) {
        document.getElementById('sourceGrid').innerHTML = `
            <div style="grid-column: 1/-1; text-align:center; padding:32px; color:var(--text-muted);">
                <div style="font-size:24px; margin-bottom:8px;">⚠️</div>
                <div>Could not load sources from API.<br><span style="font-size:12px;">${err.message}</span></div>
                <div style="margin-top:12px; font-size:13px;">Make sure the backend is running on port 8001.</div>
            </div>
        `;
    }
}

function renderSourceCards(sites) {
    const grid = document.getElementById('sourceGrid');
    if (!sites || sites.length === 0) {
        grid.innerHTML = `<div style="grid-column:1/-1; text-align:center; padding:48px; color:var(--text-muted);">
            <div style="font-size:32px; margin-bottom:8px;">📡</div>
            No sources configured. Click "Add Source" to get started.
        </div>`;
        return;
    }

    grid.innerHTML = sites.map(site => `
        <div class="source-card" data-key="${site.key}">
            <div class="source-card-header">
                <div>
                    <div class="source-card-title">${site.name}</div>
                    <div class="source-card-url">${site.base_url}</div>
                </div>
                <span class="source-badge ${site.enabled ? 'enabled' : 'disabled'}">
                    ${site.enabled ? 'Active' : 'Disabled'}
                </span>
            </div>
            <div class="source-meta">
                <span>⏱ ${site.rate_limit}s delay</span>
                <span>${site.use_playwright ? '🎭 Playwright' : '📄 Static'}</span>
                <span>📂 ${(site.categories || []).length} categories</span>
            </div>
            <div class="source-actions">
                <button class="btn btn-primary scrape-btn" data-key="${site.key}" data-name="${site.name}">▶ Scrape</button>
                <button class="btn btn-outline edit-btn" data-key="${site.key}">Edit</button>
                <button class="btn btn-outline delete-btn" data-key="${site.key}" data-name="${site.name}" style="color:var(--danger-text);">Delete</button>
            </div>
        </div>
    `).join('');

    // Wire buttons
    grid.querySelectorAll('.scrape-btn').forEach(btn => {
        btn.addEventListener('click', () => triggerScrape(btn.dataset.key, btn.dataset.name));
    });
    grid.querySelectorAll('.edit-btn').forEach(btn => {
        btn.addEventListener('click', () => editSource(btn.dataset.key));
    });
    grid.querySelectorAll('.delete-btn').forEach(btn => {
        btn.addEventListener('click', () => deleteSource(btn.dataset.key, btn.dataset.name));
    });
}

/* ── Trigger Scrape ── */
async function triggerScrape(siteKey, siteName) {
    showToast(`Starting scrape for ${siteName}...`);
    try {
        const res = await fetch(`${API_BASE}/scrape`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-API-Key': 'dev-key' },
            body: JSON.stringify({ sites: [siteKey], generate_report: false, store_data: true })
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || `HTTP ${res.status}`);
        }
        const data = await res.json();
        showToast(`✅ Scrape queued — Task ID: ${data.task_id.slice(0, 8)}...`);
    } catch (err) {
        showToast(`❌ Scrape failed: ${err.message}`);
    }
}

/* ── Delete Source ── */
async function deleteSource(siteKey, siteName) {
    if (!confirm(`Delete source "${siteName}"? This cannot be undone.`)) return;
    try {
        const res = await fetch(`${API_BASE}/sites/${siteKey}`, { method: 'DELETE' });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        showToast(`🗑️ Deleted ${siteName}`);
        renderManageSourcesPage();
    } catch (err) {
        showToast(`❌ Delete failed: ${err.message}`);
    }
}

/* ── Edit Source (loads into modal) ── */
async function editSource(siteKey) {
    try {
        const res = await fetch(`${API_BASE}/sites`);
        const sites = await res.json();
        const site = sites.find(s => s.key === siteKey);
        if (!site) { showToast('Site not found'); return; }
        openSourceModal(site);
    } catch (err) {
        showToast(`Failed to load site: ${err.message}`);
    }
}

/* ══════════════════════════════════════════
   SOURCE MODAL — Add / Edit
   ══════════════════════════════════════════ */
function initSourceModal() {
    const modal = document.getElementById('sourceModal');
    const closeBtn = document.getElementById('sourceModalClose');
    const form = document.getElementById('sourceForm');

    closeBtn.addEventListener('click', () => modal.classList.remove('open'));
    modal.addEventListener('click', e => { if (e.target === modal) modal.classList.remove('open'); });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const payload = {
            key: document.getElementById('srcKey').value.trim().toLowerCase().replace(/\s+/g, '_'),
            name: document.getElementById('srcName').value.trim(),
            base_url: document.getElementById('srcUrl').value.trim(),
            rate_limit: parseFloat(document.getElementById('srcRate').value) || 2.0,
            use_playwright: document.getElementById('srcPlaywright').value === 'true',
            enabled: true,
            selectors: {
                product_container: document.getElementById('selContainer').value.trim() || '.product',
                name: document.getElementById('selName').value.trim() || '.product-name',
                price: document.getElementById('selPrice').value.trim() || '.price',
                unit: document.getElementById('selUnit').value.trim() || '.unit',
            },
            categories: []
        };

        try {
            let res;
            if (editingSiteKey) {
                // Update existing
                res = await fetch(`${API_BASE}/sites/${editingSiteKey}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
            } else {
                // Create new
                res = await fetch(`${API_BASE}/sites`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
            }

            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || `HTTP ${res.status}`);
            }

            showToast(editingSiteKey ? `✅ Updated ${payload.name}` : `✅ Added ${payload.name}`);
            modal.classList.remove('open');
            form.reset();
            editingSiteKey = null;
            renderManageSourcesPage();
        } catch (err) {
            showToast(`❌ Error: ${err.message}`);
        }
    });
}

function openSourceModal(site = null) {
    editingSiteKey = site ? site.key : null;
    const modal = document.getElementById('sourceModal');
    document.getElementById('sourceModalTitle').textContent = site ? 'Edit Source' : 'Add Source';
    document.getElementById('sourceSubmitBtn').textContent = site ? 'Save Changes' : 'Add Source';

    // Pre-fill if editing
    document.getElementById('srcName').value = site ? site.name : '';
    document.getElementById('srcKey').value = site ? site.key : '';
    document.getElementById('srcKey').disabled = !!site; // Can't change key when editing
    document.getElementById('srcUrl').value = site ? site.base_url : '';
    document.getElementById('srcRate').value = site ? site.rate_limit : 2.0;
    document.getElementById('srcPlaywright').value = site?.use_playwright ? 'true' : 'false';

    const sel = site?.selectors || {};
    document.getElementById('selContainer').value = sel.product_container || '';
    document.getElementById('selName').value = sel.name || '';
    document.getElementById('selPrice').value = sel.price || '';
    document.getElementById('selUnit').value = sel.unit || '';

    modal.classList.add('open');
}

/* ══════════════════════════════════════════
   FILTERS — In Stock Only / Price Drop >10%
   ══════════════════════════════════════════ */
function initFilters() {
    document.getElementById('filterInStock').addEventListener('click', () => {
        activeFilters.instock = !activeFilters.instock;
        document.getElementById('filterInStock').classList.toggle('active-filter', activeFilters.instock);
        applyAllFilters();
        showToast(activeFilters.instock ? 'Filter: In Stock Only — ON' : 'Filter: In Stock Only — OFF');
    });

    document.getElementById('filterPriceDrop').addEventListener('click', () => {
        activeFilters.pricedrop = !activeFilters.pricedrop;
        document.getElementById('filterPriceDrop').classList.toggle('active-filter', activeFilters.pricedrop);
        applyAllFilters();
        showToast(activeFilters.pricedrop ? 'Filter: Price Drop >10% — ON' : 'Filter: Price Drop >10% — OFF');
    });
}

function applyAllFilters() {
    const query = document.getElementById('searchInput').value.toLowerCase();
    let filtered = [...allProducts];

    if (query) {
        filtered = filtered.filter(p =>
            p.name.toLowerCase().includes(query) || p.specs.toLowerCase().includes(query)
        );
    }
    if (activeFilters.instock) {
        filtered = filtered.filter(p => p.inStock !== false);
    }
    if (activeFilters.pricedrop) {
        filtered = filtered.filter(p => parseFloat(p.variance) < -10);
    }

    displayedProducts = filtered;
    currentPage = 1;
    renderTable(displayedProducts);
}

/* ══════════════════════════════════════════
   SORTABLE TABLE HEADERS
   ══════════════════════════════════════════ */
function initSortableHeaders() {
    document.querySelectorAll('th.sortable').forEach(th => {
        th.addEventListener('click', () => {
            const field = th.dataset.sort;
            if (sortField === field) { sortAsc = !sortAsc; } else { sortField = field; sortAsc = true; }
            sortProducts();
            renderTable(displayedProducts);
            showToast(`Sorted by ${th.textContent.replace('⇅', '').trim()} ${sortAsc ? '↑' : '↓'}`);
        });
    });
}

function sortProducts() {
    displayedProducts.sort((a, b) => {
        let valA, valB;
        switch (sortField) {
            case 'name': valA = a.name; valB = b.name; break;
            case 'retailerA': valA = a.retailers.A; valB = b.retailers.A; break;
            case 'retailerB': valA = a.retailers.B; valB = b.retailers.B; break;
            case 'retailerC': valA = a.retailers.C; valB = b.retailers.C; break;
            case 'variance': valA = parseFloat(a.variance); valB = parseFloat(b.variance); break;
            default: return 0;
        }
        if (typeof valA === 'string') return sortAsc ? valA.localeCompare(valB) : valB.localeCompare(valA);
        return sortAsc ? valA - valB : valB - valA;
    });
}

/* ══════════════════════════════════════════
   PAGINATION
   ══════════════════════════════════════════ */
function initPagination() {
    document.getElementById('paginationControls').addEventListener('click', e => {
        const btn = e.target.closest('.page-btn');
        if (!btn) return;
        const totalPages = 3;
        if (btn.dataset.action === 'prev') { if (currentPage > 1) currentPage--; }
        else if (btn.dataset.action === 'next') { if (currentPage < totalPages) currentPage++; }
        else if (btn.dataset.page) { currentPage = parseInt(btn.dataset.page); }

        document.querySelectorAll('.page-btn[data-page]').forEach(b => b.classList.remove('active'));
        const activeBtn = document.querySelector(`.page-btn[data-page="${currentPage}"]`);
        if (activeBtn) activeBtn.classList.add('active');
        document.querySelector('.page-btn[data-action="prev"]').disabled = currentPage === 1;
        document.querySelector('.page-btn[data-action="next"]').disabled = currentPage === totalPages;
        renderTable(displayedProducts);
    });
}

/* ══════════════════════════════════════════
   EXPORT DATA — generate and download CSV
   ══════════════════════════════════════════ */
function initExportBtn() {
    document.getElementById('exportBtn').addEventListener('click', () => {
        if (displayedProducts.length === 0) { showToast('No data to export'); return; }
        const headers = ['Product Name', 'Specs', 'Retailer A', 'Retailer B', 'Retailer C', 'Variance'];
        const rows = displayedProducts.map(p => [
            `"${p.name}"`, `"${p.specs}"`, p.retailers.A, p.retailers.B, p.retailers.C, p.variance
        ]);
        const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `pricetrackerPro_export_${new Date().toISOString().slice(0, 10)}.csv`;
        a.click();
        URL.revokeObjectURL(url);
        showToast(`Exported ${displayedProducts.length} products to CSV`);
    });
}

/* ══════════════════════════════════════════
   NOTIFICATION BELL
   ══════════════════════════════════════════ */
function initNotificationBtn() {
    const btn = document.getElementById('notificationBtn');
    const panel = document.getElementById('notificationPanel');
    const closeBtn = document.getElementById('notifClose');
    const dot = document.getElementById('notifDot');

    btn.addEventListener('click', () => {
        document.getElementById('settingsPanel').classList.remove('open');
        panel.classList.toggle('open');
        if (panel.classList.contains('open')) {
            dot.classList.add('hidden');
            document.querySelectorAll('.notif-item.unread').forEach(i => i.classList.remove('unread'));
        }
    });
    closeBtn.addEventListener('click', () => panel.classList.remove('open'));
    document.querySelectorAll('.notif-item').forEach(item => {
        item.addEventListener('click', () => {
            showToast(`Opened: ${item.querySelector('.notif-title').textContent}`);
            panel.classList.remove('open');
        });
    });
}

/* ══════════════════════════════════════════
   SETTINGS GEAR
   ══════════════════════════════════════════ */
function initSettingsBtn() {
    const btn = document.getElementById('settingsBtn');
    const panel = document.getElementById('settingsPanel');
    const closeBtn = document.getElementById('settingsClose');
    const saveBtn = document.getElementById('saveSettingsBtn');

    btn.addEventListener('click', () => {
        document.getElementById('notificationPanel').classList.remove('open');
        panel.classList.toggle('open');
    });
    closeBtn.addEventListener('click', () => panel.classList.remove('open'));
    saveBtn.addEventListener('click', () => {
        currency = document.getElementById('currencySelect').value;
        const interval = document.getElementById('scrapeIntervalSelect').value;
        const darkMode = document.getElementById('darkModeToggle').checked;
        if (darkMode) { document.body.style.background = '#111827'; document.body.style.color = '#f9fafb'; }
        else { document.body.style.background = ''; document.body.style.color = ''; }
        panel.classList.remove('open');
        renderTable(displayedProducts);
        showToast(`Settings saved — Currency: ${currency}, Interval: ${interval}h, Dark: ${darkMode ? 'ON' : 'OFF'}`);
    });
}

/* ══════════════════════════════════════════
   USER PROFILE MENU
   ══════════════════════════════════════════ */
function initUserMenu() {
    const menuBtn = document.getElementById('userMenuBtn');
    const profileBtn = document.getElementById('userProfileBtn');
    const dropdown = document.getElementById('userDropdown');

    const toggle = (e) => { e.stopPropagation(); dropdown.classList.toggle('open'); };
    menuBtn.addEventListener('click', toggle);
    profileBtn.addEventListener('click', toggle);
    document.addEventListener('click', () => dropdown.classList.remove('open'));
    dropdown.addEventListener('click', e => e.stopPropagation());

    document.getElementById('editProfileBtn').addEventListener('click', e => {
        e.preventDefault(); dropdown.classList.remove('open');
        showToast('Edit Profile — Feature coming soon');
    });
    document.getElementById('accountSettingsBtn').addEventListener('click', e => {
        e.preventDefault(); dropdown.classList.remove('open');
        document.getElementById('settingsPanel').classList.add('open');
        showToast('Opening Account Settings...');
    });
    document.getElementById('logoutBtn').addEventListener('click', e => {
        e.preventDefault(); dropdown.classList.remove('open');
        if (confirm('Are you sure you want to log out?')) showToast('Logged out successfully');
    });
}

/* ══════════════════════════════════════════
   MODAL — product detail view
   ══════════════════════════════════════════ */
function initModalClose() {
    const modal = document.getElementById('detailModal');
    document.getElementById('modalClose').addEventListener('click', () => modal.classList.remove('open'));
    modal.addEventListener('click', e => { if (e.target === modal) modal.classList.remove('open'); });
}

function openProductDetail(product) {
    const modal = document.getElementById('detailModal');
    document.getElementById('modalTitle').textContent = product.name;
    const lo = Math.min(product.retailers.A, product.retailers.B, product.retailers.C);
    const hi = Math.max(product.retailers.A, product.retailers.B, product.retailers.C);
    document.getElementById('modalBody').innerHTML = `
        <div class="detail-row"><span class="detail-label">Specs</span><span class="detail-value">${product.specs}</span></div>
        <div class="detail-row"><span class="detail-label">Retailer A</span><span class="detail-value">${formatPrice(product.retailers.A)}</span></div>
        <div class="detail-row"><span class="detail-label">Retailer B</span><span class="detail-value">${formatPrice(product.retailers.B)}</span></div>
        <div class="detail-row"><span class="detail-label">Retailer C</span><span class="detail-value">${formatPrice(product.retailers.C)}</span></div>
        <div class="detail-row"><span class="detail-label">Lowest Price</span><span class="detail-value" style="color:var(--success-text)">${formatPrice(lo)}</span></div>
        <div class="detail-row"><span class="detail-label">Potential Savings</span><span class="detail-value" style="color:var(--primary)">${formatPrice(hi - lo)}</span></div>
        <div class="detail-row"><span class="detail-label">Price Variance</span><span class="detail-value">${product.variance}</span></div>
    `;
    modal.classList.add('open');
}

/* ══════════════════════════════════════════
   TABLE RENDERER
   ══════════════════════════════════════════ */
function renderTable(products) {
    const tableBody = document.getElementById('tableBody');
    tableBody.innerHTML = '';
    if (!products || products.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding:48px; color:var(--text-muted);">
            <div style="font-size:32px; margin-bottom:8px;">📭</div>No products found matching your criteria.</td></tr>`;
        document.getElementById('paginationInfo').textContent = 'Showing 0 products';
        return;
    }
    products.forEach((product, idx) => {
        const tr = document.createElement('tr');
        let pillClass = 'pill-neutral';
        if (product.variance.startsWith('-')) pillClass = 'pill-success';
        else if (product.variance.startsWith('+')) pillClass = 'pill-danger';
        tr.innerHTML = `
            <td><div class="product-cell"><span class="product-name">${product.name}</span><span class="product-spec">${product.specs}</span></div></td>
            <td class="retailer-price">${formatPrice(product.retailers.A)}</td>
            <td class="retailer-price">${formatPrice(product.retailers.B)}</td>
            <td class="retailer-price">${formatPrice(product.retailers.C)}</td>
            <td style="text-align:center;"><div class="pill-container"><span class="pill ${pillClass}">${product.variance}</span></div></td>
            <td><button class="action-link" data-idx="${idx}">View\nDetails</button></td>
        `;
        tr.querySelector('.action-link').addEventListener('click', e => { e.preventDefault(); openProductDetail(product); });
        tableBody.appendChild(tr);
    });
    document.getElementById('paginationInfo').textContent = `Showing 1 to ${products.length} of ${products.length} products`;
}

/* ══════════════════════════════════════════
   TOAST NOTIFICATIONS
   ══════════════════════════════════════════ */
function showToast(message) {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    container.appendChild(toast);
    requestAnimationFrame(() => toast.classList.add('visible'));
    setTimeout(() => { toast.classList.remove('visible'); setTimeout(() => toast.remove(), 300); }, 2500);
}

/* ══════════════════════════════════════════
   UTILITY
   ══════════════════════════════════════════ */
function formatPrice(price) {
    if (price == null) return '-';
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: currency }).format(price);
}

/* ══════════════════════════════════════════
   MOCK DATA
   ══════════════════════════════════════════ */
function getMockData() {
    return [
        { name: 'Enterprise Server R740', specs: '64GB RAM, 2TB SSD, Dual Gold 6130', retailers: { A: 2499.00, B: 2550.00, C: 2485.00 }, variance: '-2.4%', inStock: true },
        { name: 'Pro Laptop 16" - Space Gray', specs: 'M2 Max, 32GB Unified Memory, 1TB', retailers: { A: 3199.00, B: 3199.00, C: 3249.00 }, variance: '+1.5%', inStock: true },
        { name: 'Wireless Noise Cancelling Gen 5', specs: 'Carbon Black, 30hr Battery Life', retailers: { A: 348.00, B: 349.99, C: 330.00 }, variance: '-5.7%', inStock: true },
        { name: '4K Ultra HD Smart Projector', specs: '3000 Lumens, HDR10, Android TV', retailers: { A: 1899.00, B: 1950.00, C: 1899.00 }, variance: '0.0%', inStock: true },
        { name: 'Mechanical Keyboard RGB Pro', specs: 'Blue Switches, Hot-swappable PCB', retailers: { A: 129.00, B: 145.00, C: 125.00 }, variance: '-13.8%', inStock: true },
        { name: 'Ultrawide Curved Monitor 38"', specs: '144Hz, 1ms, IPS Panel, Thunderbolt 4', retailers: { A: 1199.00, B: 1149.00, C: 1210.00 }, variance: '+5.2%', inStock: false },
    ];
}
