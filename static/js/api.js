/**
 * Smart Library Management System - API Client & Core Utilities
 * Centralized AJAX fetch handlers, session management, and UI notifications
 */

const API = {
  // Base request handler
  async request(endpoint, options = {}) {
    const config = {
      method: options.method || 'GET',
      headers: {
        'Accept': 'application/json',
        ...(options.headers || {})
      },
      credentials: 'same-origin', // Sends session cookies with every request
      ...options
    };

    if (config.body && typeof config.body === 'object' && !(config.body instanceof FormData)) {
      config.headers['Content-Type'] = 'application/json';
      config.body = JSON.stringify(config.body);
    }

    try {
      const response = await fetch(endpoint, config);
      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        const errorMsg = data.error || data.message || `Request failed with status ${response.status}`;
        throw new Error(errorMsg);
      }

      return data;
    } catch (err) {
      console.error(`API Error on [${config.method} ${endpoint}]:`, err);
      throw err;
    }
  },

  // Auth Endpoints
  async register(formData) {
    return this.request('/api/auth/register', { method: 'POST', body: formData });
  },

  async login(email, password) {
    return this.request('/api/auth/login', { method: 'POST', body: { email, password } });
  },

  async logout() {
    try {
      await this.request('/api/auth/logout', { method: 'POST' });
    } finally {
      localStorage.removeItem('smartlib_user');
      window.location.href = '/login.html';
    }
  },

  async getMe() {
    return this.request('/api/me');
  },

  // Books
  async getBooks(params = {}) {
    const query = new URLSearchParams();
    if (params.q) query.append('q', params.q);
    if (params.category_id) query.append('category_id', params.category_id);
    const qs = query.toString();
    return this.request(`/api/books${qs ? '?' + qs : ''}`);
  },

  async getBook(id) {
    return this.request(`/api/books/${id}`);
  },

  async createBook(bookData) {
    return this.request('/api/books', { method: 'POST', body: bookData });
  },

  async updateBook(id, bookData) {
    return this.request(`/api/books/${id}`, { method: 'PUT', body: bookData });
  },

  async deleteBook(id) {
    return this.request(`/api/books/${id}`, { method: 'DELETE' });
  },

  // Categories & Authors
  async getCategories() {
    return this.request('/api/categories');
  },

  async createCategory(category_name) {
    return this.request('/api/categories', { method: 'POST', body: { category_name } });
  },

  async getAuthors() {
    return this.request('/api/authors');
  },

  async createAuthor(author_name) {
    return this.request('/api/authors', { method: 'POST', body: { author_name } });
  },

  // Book Copies
  async getCopies(book_id = null) {
    return this.request(`/api/copies${book_id ? '?book_id=' + book_id : ''}`);
  },

  async createCopy(book_id) {
    return this.request(`/api/books/${book_id}/copies`, { method: 'POST', body: {} });
  },

  // Circulation (Issue / Return / Borrow)
  async issueBook(issueData) {
    return this.request('/api/issue', { method: 'POST', body: issueData });
  },

  async borrowBook(book_id, copy_id = null) {
    return this.request('/api/issue', { method: 'POST', body: { book_id, copy_id } });
  },

  async returnBook(issue_id, return_date = null) {
    return this.request(`/api/return/${issue_id}`, { method: 'POST', body: { return_date } });
  },

  async getIssues(member_id = null) {
    return this.request(`/api/issues${member_id ? '?member_id=' + member_id : ''}`);
  },

  // Reservations
  async reserveBook(book_id, member_id = null) {
    return this.request('/api/reservations', { method: 'POST', body: { book_id, member_id } });
  },

  async getReservations(member_id = null) {
    return this.request(`/api/reservations${member_id ? '?member_id=' + member_id : ''}`);
  },

  async cancelReservation(id) {
    return this.request(`/api/reservations/${id}`, { method: 'DELETE' });
  },

  // Fines
  async getFines(member_id = null) {
    return this.request(`/api/fines${member_id ? '?member_id=' + member_id : ''}`);
  },

  async payFine(fine_id, amount = null) {
    return this.request(`/api/fines/${fine_id}/pay`, { method: 'POST', body: { amount } });
  },

  // Members & Stats
  async getMembers() {
    return this.request('/api/members');
  },

  async getStats() {
    return this.request('/api/stats');
  }
};

// -------------------------------------------------------------------------
// Global UI & Session Helpers
// -------------------------------------------------------------------------

function showToast(message, type = 'info') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <span>${escapeHtml(message)}</span>
    <button style="background:none;border:none;cursor:pointer;color:#94a3b8;font-size:1.1rem;" onclick="this.parentElement.remove()">&times;</button>
  `;

  container.appendChild(toast);
  setTimeout(() => {
    if (toast.parentElement) toast.remove();
  }, 4500);
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function formatCurrency(num) {
  const n = parseFloat(num) || 0;
  return '₹' + n.toFixed(2);
}

function formatDate(dateStr) {
  if (!dateStr) return 'N/A';
  const d = new Date(dateStr);
  return isNaN(d.getTime()) ? dateStr : d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
}

// -------------------------------------------------------------------------
// Unified Navbar Manager
// -------------------------------------------------------------------------

async function setupNavbar(activePage = '') {
  let user = null;
  try {
    const res = await API.getMe();
    user = res.user;
    localStorage.setItem('smartlib_user', JSON.stringify(user));
  } catch (e) {
    localStorage.removeItem('smartlib_user');
  }

  const navContainer = document.querySelector('.nav-container');
  if (!navContainer) return;

  const isAdminOrLibrarian = user && (user.role === 'admin' || user.role === 'librarian');

  let navLinksHtml = `
    <li><a href="/index.html" class="nav-link ${activePage === 'home' ? 'active' : ''}">Home</a></li>
    <li><a href="/books.html" class="nav-link ${activePage === 'books' ? 'active' : ''}">Catalogue</a></li>
  `;

  if (user) {
    if (user.role === 'member') {
      navLinksHtml += `<li><a href="/dashboard.html" class="nav-link ${activePage === 'dashboard' ? 'active' : ''}">My Dashboard</a></li>`;
    }
    if (isAdminOrLibrarian) {
      navLinksHtml += `<li><a href="/admin.html" class="nav-link ${activePage === 'admin' ? 'active' : ''}">Admin Panel</a></li>`;
    }
  }

  let userSectionHtml = '';
  if (user) {
    userSectionHtml = `
      <div class="nav-user">
        <div class="user-badge">
          <span class="user-name">${escapeHtml(user.name)}</span>
          <span class="user-role">${escapeHtml(user.role)} • ${escapeHtml(user.department || 'General')}</span>
        </div>
        <button id="nav-logout-btn" class="btn btn-outline btn-sm">Sign Out</button>
      </div>
    `;
  } else {
    userSectionHtml = `
      <div style="display:flex;gap:0.5rem;">
        <a href="/login.html" class="btn btn-outline btn-sm">Sign In</a>
        <a href="/register.html" class="btn btn-primary btn-sm">Register</a>
      </div>
    `;
  }

  navContainer.innerHTML = `
    <a href="/index.html" class="nav-brand">
      📚 SmartLib <span class="badge-pill">DBMS</span>
    </a>
    <ul class="nav-links">
      ${navLinksHtml}
    </ul>
    ${userSectionHtml}
  `;

  const logoutBtn = document.getElementById('nav-logout-btn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', () => API.logout());
  }

  return user;
}
