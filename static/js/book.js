let currentUser = null;
let currentBook = null;

document.addEventListener('DOMContentLoaded', async () => {
  currentUser = await setupNavbar('books');

  const urlParams = new URLSearchParams(window.location.search);
  const bookId = urlParams.get('id');

  if (!bookId) {
    document.getElementById('book-details-card').innerHTML = '<p class="text-danger-bold">Error: No book ID specified in URL.</p>';
    return;
  }

  // Load Book Details
  async function loadBookDetails() {
    try {
      currentBook = await API.getBook(bookId);
      renderBook(currentBook);
    } catch (err) {
      document.getElementById('book-details-card').innerHTML = `<p style="color:#ef4444;">Failed to load book: ${escapeHtml(err.message)}</p>`;
    }
  }

  function renderBook(book) {
    document.title = `${book.title} - SmartLib`;

    const authorNames = book.authors && book.authors.length 
      ? book.authors.map(a => a.author_name).join(', ') 
      : 'Unknown';

    const isAvailable = book.available_copies > 0;

    // Render basic info
    document.getElementById('book-category-tag').textContent = book.category_name;
    document.getElementById('book-title').textContent = book.title;
    document.getElementById('book-authors').textContent = `By ${authorNames}`;
    document.getElementById('book-isbn').textContent = book.isbn;
    document.getElementById('book-publisher').textContent = book.publisher || 'Not Specified';
    document.getElementById('book-year').textContent = book.publication_year || 'Not Specified';

    // Availability summary badge
    const availContainer = document.getElementById('book-avail-summary');
    if (isAvailable) {
      availContainer.innerHTML = `<span class="badge badge-success" style="font-size:0.95rem;padding:0.4rem 0.8rem;">✓ ${book.available_copies} of ${book.total_copies} Copies Available</span>`;
    } else {
      availContainer.innerHTML = `<span class="badge badge-warning" style="font-size:0.95rem;padding:0.4rem 0.8rem;">⚠ All Copies Issued (${book.total_copies} total)</span>`;
    }

    // Reservation / Borrow Action Box
    const reserveBox = document.getElementById('reservation-action-box');
    if (!currentUser) {
      reserveBox.innerHTML = `
        <div style="background:#f1f5f9;padding:1.25rem;border-radius:6px;border:1px solid #cbd5e1;">
          <h4 style="font-weight:700;margin-bottom:0.35rem;">Sign In to Borrow</h4>
          <p style="font-size:0.875rem;color:#475569;margin-bottom:0.75rem;">Sign in to your member account to borrow available copies or place reservation holds.</p>
          <a href="/login.html" class="btn btn-primary btn-sm">Sign In to Borrow / Reserve</a>
        </div>
      `;
    } else if (currentUser.role === 'member') {
      if (isAvailable) {
        reserveBox.innerHTML = `
          <div style="background:#ecfdf5;border:1px solid #a7f3d0;padding:1.25rem;border-radius:6px;">
            <h4 style="font-size:1.05rem;font-weight:700;color:#065f46;margin-bottom:0.35rem;">📖 Ready to Borrow</h4>
            <p style="font-size:0.875rem;color:#047857;margin-bottom:0.85rem;">
              <strong>${book.available_copies}</strong> physical copy(ies) are currently available in the library. Standard loan period is 14 days.
            </p>
            <button id="btn-borrow-book" class="btn btn-success" style="width:100%;font-size:1rem;padding:0.75rem;">
              ✓ Borrow This Book Now
            </button>
          </div>
        `;
        document.getElementById('btn-borrow-book').addEventListener('click', () => handleBorrow(book.book_id));
      } else {
        reserveBox.innerHTML = `
          <div style="background:#fffbeb;border:1px solid #fde68a;padding:1.25rem;border-radius:6px;">
            <h4 style="font-size:1.05rem;font-weight:700;color:#92400e;margin-bottom:0.25rem;">Place a Reservation Hold</h4>
            <p style="font-size:0.875rem;color:#78350f;margin-bottom:0.85rem;">
              All copies are currently issued to other members. Place a reservation now to hold your place in line for the next returned copy.
            </p>
            <button id="btn-reserve-book" class="btn btn-primary" style="width:100%;">Reserve This Book</button>
          </div>
        `;
        document.getElementById('btn-reserve-book').addEventListener('click', handleReservation);
      }
    } else {
      // Admin or Librarian view
      reserveBox.innerHTML = `
        <div style="background:#eff6ff;padding:1rem;border-radius:6px;border:1px solid #bfdbfe;display:flex;flex-direction:column;gap:0.75rem;">
          <div>
            <strong>Staff Controls:</strong> Logged in as ${escapeHtml(currentUser.role)}.
          </div>
          <div style="display:flex;gap:0.5rem;flex-wrap:wrap;">
            <button id="btn-open-add-copy" class="btn btn-primary btn-sm">+ Add Physical Copy</button>
            <a href="/admin.html" class="btn btn-outline btn-sm">Circulation Desk</a>
          </div>
        </div>
      `;
      const addCopyBtn = document.getElementById('btn-open-add-copy');
      if (addCopyBtn) {
        addCopyBtn.addEventListener('click', () => {
          document.getElementById('modal-add-copy').classList.add('open');
        });
      }
    }

    // Render Copies Inventory Table
    const copiesTbody = document.getElementById('copies-table-body');
    if (!book.copies || book.copies.length === 0) {
      copiesTbody.innerHTML = '<tr><td colspan="4" style="text-align:center;color:#64748b;padding:1.5rem;">No copies registered in the catalog yet.</td></tr>';
      return;
    }

    copiesTbody.innerHTML = book.copies.map((c, index) => {
      let statusBadge = '';
      if (c.status === 'available') {
        statusBadge = '<span class="badge badge-success">Available</span>';
      } else if (c.status === 'issued') {
        statusBadge = '<span class="badge badge-warning">Issued</span>';
      } else {
        statusBadge = '<span class="badge badge-danger">Lost / Unavailable</span>';
      }

      let actionBtn = '-';
      if (c.status === 'available') {
        if (currentUser && currentUser.role === 'member') {
          actionBtn = `<button class="btn btn-success btn-sm" onclick="handleBorrow(${book.book_id}, ${c.copy_id})" style="padding:0.25rem 0.6rem;font-size:0.8rem;">Borrow Copy</button>`;
        } else if (currentUser && (currentUser.role === 'admin' || currentUser.role === 'librarian')) {
          actionBtn = `<a href="/admin.html?issue_copy=${c.copy_id}" class="btn btn-primary btn-sm" style="padding:0.25rem 0.6rem;font-size:0.8rem;">Issue</a>`;
        }
      }

      return `
        <tr>
          <td><strong>Copy #${c.copy_id}</strong></td>
          <td>${statusBadge}</td>
          <td>${actionBtn}</td>
        </tr>
      `;
    }).join('');
  }

  // Handle Borrow
  window.handleBorrow = async function(bId, cId = null) {
    try {
      const borrowBtn = document.getElementById('btn-borrow-book');
      if (borrowBtn) {
        borrowBtn.disabled = true;
        borrowBtn.textContent = 'Borrowing...';
      }
      await API.borrowBook(bId, cId);
      showToast('Book borrowed successfully! Due in 14 days. Check My Dashboard.', 'success');
      setTimeout(() => {
        loadBookDetails();
      }, 500);
    } catch (err) {
      showToast(err.message, 'error');
      const borrowBtn = document.getElementById('btn-borrow-book');
      if (borrowBtn) {
        borrowBtn.disabled = false;
        borrowBtn.textContent = '✓ Borrow This Book Now';
      }
    }
  };

  // Handle Reservation
  async function handleReservation() {
    const btn = document.getElementById('btn-reserve-book');
    try {
      if (btn) btn.disabled = true;
      await API.reserveBook(bookId);
      showToast('Reservation successful! You can view it in your dashboard.', 'success');
      loadBookDetails();
    } catch (err) {
      showToast(err.message, 'error');
      if (btn) btn.disabled = false;
    }
  }

  // Add Copy Modal Logic
  const modalAddCopy = document.getElementById('modal-add-copy');
  const closeCopyModalBtn = document.getElementById('btn-close-copy-modal');
  const addCopyForm = document.getElementById('form-add-copy');

  if (closeCopyModalBtn) {
    closeCopyModalBtn.addEventListener('click', () => {
      modalAddCopy.classList.remove('open');
    });
  }

  if (addCopyForm) {
    addCopyForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      try {
        await API.createCopy(bookId);
        showToast('New copy added successfully to inventory!', 'success');
        modalAddCopy.classList.remove('open');
        loadBookDetails();
      } catch (err) {
        showToast(err.message, 'error');
      }
    });
  }

  // Initial load
  loadBookDetails();
});
