let currentUser = null;

document.addEventListener('DOMContentLoaded', async () => {
  currentUser = await setupNavbar('books');

  const searchInput = document.getElementById('books-search-input');
  const categorySelect = document.getElementById('books-category-select');
  const booksGrid = document.getElementById('books-grid');
  const resultsCount = document.getElementById('books-count');

  // Pre-fill from URL params
  const urlParams = new URLSearchParams(window.location.search);
  const initialQ = urlParams.get('q') || '';
  const initialCat = urlParams.get('category_id') || '';

  if (searchInput) searchInput.value = initialQ;

  // Load Categories into filter dropdown
  try {
    const categories = await API.getCategories();
    categories.forEach(cat => {
      const opt = document.createElement('option');
      opt.value = cat.category_id;
      opt.textContent = `${cat.category_name} (${cat.book_count})`;
      if (initialCat && initialCat == cat.category_id) {
        opt.selected = true;
      }
      categorySelect.appendChild(opt);
    });
  } catch (err) {
    console.error('Could not load categories:', err);
  }

  // Load and Render Books
  async function loadBooks() {
    booksGrid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 2rem; color: #64748b;">Loading books catalog...</div>';

    const q = searchInput ? searchInput.value.trim() : '';
    const category_id = categorySelect ? categorySelect.value : '';

    try {
      const books = await API.getBooks({ q, category_id });
      resultsCount.textContent = `Found ${books.length} book${books.length === 1 ? '' : 's'}`;

      if (books.length === 0) {
        booksGrid.innerHTML = `
          <div style="grid-column: 1/-1; text-align: center; padding: 3rem 1rem; background: white; border-radius: 8px; border: 1px dashed #cbd5e1;">
            <p style="font-size: 1.1rem; color: #475569; font-weight: 500;">No books match your search criteria.</p>
            <p style="color: #94a3b8; font-size: 0.9rem; margin-top: 0.25rem;">Try adjusting your keyword or clearing the category filter.</p>
          </div>
        `;
        return;
      }

      booksGrid.innerHTML = books.map(b => {
        const authorNames = b.authors && b.authors.length 
          ? b.authors.map(a => a.author_name).join(', ') 
          : 'Unknown Author';

        const isAvailable = b.available_copies > 0;
        const availBadge = isAvailable
          ? `<span class="badge badge-success">✓ ${b.available_copies} of ${b.total_copies} Available</span>`
          : `<span class="badge badge-warning">⚠ All Copies Issued (${b.total_copies} total)</span>`;

        let actionHtml = `<a href="/book.html?id=${b.book_id}" class="btn btn-outline btn-sm">View Details</a>`;
        
        // If copies available and user is a member, provide quick borrow button
        if (isAvailable && currentUser && currentUser.role === 'member') {
          actionHtml += ` <button class="btn btn-success btn-sm" onclick="borrowBookQuick(${b.book_id})">Borrow</button>`;
        }
        // If 0 copies available and user is a member, provide quick reservation button
        else if (!isAvailable && currentUser && currentUser.role === 'member') {
          actionHtml += ` <button class="btn btn-primary btn-sm" onclick="reserveBookQuick(${b.book_id})">Reserve</button>`;
        }

        return `
          <div class="card book-card">
            <div>
              <div class="book-card-category">${escapeHtml(b.category_name)}</div>
              <h3 class="book-card-title">
                <a href="/book.html?id=${b.book_id}">${escapeHtml(b.title)}</a>
              </h3>
              <p class="book-card-authors">By ${escapeHtml(authorNames)}</p>
              <div style="font-size: 0.8rem; color: #64748b; margin-bottom: 0.75rem;">
                <span>ISBN: ${escapeHtml(b.isbn)}</span> • 
                <span>${escapeHtml(b.publisher || 'N/A')} (${escapeHtml(b.publication_year || 'N/A')})</span>
              </div>
            </div>
            <div class="book-card-meta">
              ${availBadge}
              <div style="display: flex; gap: 0.4rem;">
                ${actionHtml}
              </div>
            </div>
          </div>
        `;
      }).join('');
    } catch (err) {
      booksGrid.innerHTML = `<div style="grid-column: 1/-1; color: #ef4444; padding: 2rem; text-align: center;">Error loading books: ${escapeHtml(err.message)}</div>`;
    }
  }

  // Quick borrow handler
  window.borrowBookQuick = async function(bookId) {
    try {
      await API.borrowBook(bookId);
      showToast('Book borrowed successfully! Due in 14 days. Check your Dashboard.', 'success');
      loadBooks();
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  // Quick reservation handler
  window.reserveBookQuick = async function(bookId) {
    try {
      await API.reserveBook(bookId);
      showToast('Book reserved successfully! Check your Dashboard.', 'success');
      loadBooks();
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  // Event Listeners for Filters
  let debounceTimeout = null;
  searchInput.addEventListener('input', () => {
    clearTimeout(debounceTimeout);
    debounceTimeout = setTimeout(loadBooks, 300);
  });

  categorySelect.addEventListener('change', loadBooks);

  // Initial load
  loadBooks();
});
