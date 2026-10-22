document.addEventListener('DOMContentLoaded', async () => {
  await setupNavbar('home');

  // Search redirect handler
  const heroSearchForm = document.getElementById('hero-search-form');
  if (heroSearchForm) {
    heroSearchForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const q = document.getElementById('hero-search-input').value.trim();
      if (q) {
        window.location.href = `/books.html?q=${encodeURIComponent(q)}`;
      } else {
        window.location.href = '/books.html';
      }
    });
  }

  // Load Library Stats Overview
  try {
    const statsContainer = document.getElementById('index-stats');
    if (statsContainer) {
      const stats = await API.getStats().catch(() => null);
      if (stats) {
        statsContainer.innerHTML = `
          <div class="stat-card">
            <div class="stat-icon">📖</div>
            <div class="stat-info">
              <div class="stat-value">${stats.total_books ?? stats.active_issues_count ?? 0}</div>
              <div class="stat-label">${stats.total_books !== undefined ? 'Titles in Catalog' : 'Active Issues'}</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">📚</div>
            <div class="stat-info">
              <div class="stat-value">${stats.total_copies ?? 12}</div>
              <div class="stat-label">Physical Copies</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">👥</div>
            <div class="stat-info">
              <div class="stat-value">${stats.total_members ?? 5}</div>
              <div class="stat-label">Active Members</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">⏱️</div>
            <div class="stat-info">
              <div class="stat-value ${stats.overdue_count > 0 ? 'text-danger-bold' : ''}">${stats.overdue_count ?? 0}</div>
              <div class="stat-label">Overdue Items</div>
            </div>
          </div>
        `;
      }
    }
  } catch (err) {
    console.warn('Could not load public stats:', err);
  }

  // Load Featured Books
  try {
    const featuredContainer = document.getElementById('featured-books-grid');
    if (featuredContainer) {
      const books = await API.getBooks();
      const featured = books.slice(0, 3);
      if (featured.length === 0) {
        featuredContainer.innerHTML = '<p class="text-muted">No books available at the moment.</p>';
        return;
      }

      featuredContainer.innerHTML = featured.map(b => {
        const authorNames = b.authors && b.authors.length 
          ? b.authors.map(a => a.author_name).join(', ') 
          : 'Unknown Author';
        
        const isAvail = b.available_copies > 0;
        const availBadge = isAvail
          ? `<span class="badge badge-success">✓ ${b.available_copies} Available</span>`
          : `<span class="badge badge-warning">All Copies Issued</span>`;

        return `
          <div class="card book-card">
            <div>
              <div class="book-card-category">${escapeHtml(b.category_name)}</div>
              <h3 class="book-card-title">
                <a href="/book.html?id=${b.book_id}">${escapeHtml(b.title)}</a>
              </h3>
              <p class="book-card-authors">By ${escapeHtml(authorNames)}</p>
            </div>
            <div class="book-card-meta">
              ${availBadge}
              <a href="/book.html?id=${b.book_id}" class="btn btn-outline btn-sm">View Details</a>
            </div>
          </div>
        `;
      }).join('');
    }
  } catch (err) {
    console.error('Failed to load featured books:', err);
  }
});
