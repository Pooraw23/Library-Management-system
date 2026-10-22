let currentUser = null;
let allMembers = [];
let allBooks = [];
let allCopies = [];
let allAuthors = [];
let allCategories = [];

document.addEventListener('DOMContentLoaded', async () => {
  currentUser = await setupNavbar('admin');

  if (!currentUser || (currentUser.role !== 'admin' && currentUser.role !== 'librarian')) {
    alert('Access restricted: Librarian or Administrator credentials required.');
    window.location.href = '/login.html';
    return;
  }

  // Setup Tabs
  const tabBtns = document.querySelectorAll('.tab-btn');
  const tabPanes = document.querySelectorAll('.tab-content');

  function switchTab(tabId) {
    tabBtns.forEach(btn => btn.classList.toggle('active', btn.dataset.tab === tabId));
    tabPanes.forEach(pane => pane.classList.toggle('active', pane.id === `tab-${tabId}`));
  }

  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => switchTab(btn.dataset.tab));
  });

  // Check URL params for pre-selected copy or tab
  const urlParams = new URLSearchParams(window.location.search);
  const preselectedCopyId = urlParams.get('issue_copy');
  const initialTab = urlParams.get('tab') || 'circulation';
  switchTab(initialTab);

  // Initialize and load all datasets
  await loadAdminData();

  if (preselectedCopyId) {
    const copySelect = document.getElementById('issue-copy-select');
    if (copySelect) copySelect.value = preselectedCopyId;
  }

  async function loadAdminData() {
    await Promise.all([
      loadStats(),
      loadMembers(),
      loadCategoriesAndAuthors(),
      loadBooksAndCopies(),
      loadActiveIssues(),
      loadAllIssues(),
      loadFines()
    ]);
  }

  // 1. Stats Bar
  async function loadStats() {
    try {
      const stats = await API.getStats();
      document.getElementById('stat-admin-books').textContent = stats.total_books;
      document.getElementById('stat-admin-copies').textContent = stats.total_copies;
      document.getElementById('stat-admin-members').textContent = stats.total_members;
      document.getElementById('stat-admin-issues').textContent = stats.active_issues_count;
      
      const odEl = document.getElementById('stat-admin-overdue');
      odEl.textContent = stats.overdue_count;
      if (stats.overdue_count > 0) odEl.className = 'stat-value text-danger-bold';

      document.getElementById('stat-admin-fines').textContent = formatCurrency(stats.unpaid_fines_total);
    } catch (err) {
      console.error('Failed to load admin stats:', err);
    }
  }

  // 2. Members List & Dropdowns
  async function loadMembers() {
    try {
      allMembers = await API.getMembers();
      
      // Populate issue form member dropdown
      const issueMemberSelect = document.getElementById('issue-member-select');
      issueMemberSelect.innerHTML = '<option value="">-- Choose Member --</option>' + 
        allMembers.map(m => `<option value="${m.member_id}">${escapeHtml(m.name)} (${escapeHtml(m.email)}) - ${m.active_issues}/3 active</option>`).join('');

      // Populate Members Directory Table
      const membersTbody = document.getElementById('admin-members-tbody');
      membersTbody.innerHTML = allMembers.map(m => `
        <tr>
          <td><strong>#${m.member_id}</strong></td>
          <td><strong>${escapeHtml(m.name)}</strong></td>
          <td>${escapeHtml(m.email)}</td>
          <td><span class="badge ${m.role === 'admin' ? 'badge-danger' : m.role === 'librarian' ? 'badge-primary' : 'badge-secondary'}">${escapeHtml(m.role)}</span></td>
          <td>${escapeHtml(m.department || 'N/A')}</td>
          <td>${formatDate(m.joined_on)}</td>
          <td><span class="badge ${m.active_issues >= 3 ? 'badge-danger' : 'badge-success'}">${m.active_issues} / 3</span></td>
          <td style="${m.total_unpaid_fines > 0 ? 'color:#ef4444;font-weight:700;' : ''}">${formatCurrency(m.total_unpaid_fines)}</td>
        </tr>
      `).join('');
    } catch (err) {
      console.error('Failed to load members:', err);
    }
  }

  // 3. Categories and Authors Dropdowns
  async function loadCategoriesAndAuthors() {
    try {
      [allCategories, allAuthors] = await Promise.all([
        API.getCategories(),
        API.getAuthors()
      ]);

      const catSelect = document.getElementById('new-book-category');
      catSelect.innerHTML = '<option value="">-- Select Category --</option>' + 
        allCategories.map(c => `<option value="${c.category_id}">${escapeHtml(c.category_name)}</option>`).join('');

      const authorsContainer = document.getElementById('new-book-authors-list');
      authorsContainer.innerHTML = allAuthors.map(a => `
        <label style="display:inline-flex;align-items:center;gap:0.35rem;margin-right:1rem;margin-bottom:0.5rem;font-size:0.875rem;">
          <input type="checkbox" name="author_id" value="${a.author_id}">
          ${escapeHtml(a.author_name)}
        </label>
      `).join('');
    } catch (err) {
      console.error('Failed to load categories/authors:', err);
    }
  }

  // 4. Books and Copies
  async function loadBooksAndCopies() {
    try {
      [allBooks, allCopies] = await Promise.all([
        API.getBooks(),
        API.getCopies()
      ]);

      // Populate Copy creation book dropdown
      const copyBookSelect = document.getElementById('copy-book-select');
      copyBookSelect.innerHTML = '<option value="">-- Select Book Title --</option>' + 
        allBooks.map(b => `<option value="${b.book_id}">${escapeHtml(b.title)} (ISBN: ${b.isbn})</option>`).join('');

      // Populate Issue form copy dropdown (only available copies)
      const issueCopySelect = document.getElementById('issue-copy-select');
      const availableCopies = allCopies.filter(c => c.status === 'available');
      issueCopySelect.innerHTML = '<option value="">-- Select Available Copy --</option>' + 
        availableCopies.map(c => `<option value="${c.copy_id}">[Copy #${c.copy_id}] ${escapeHtml(c.title)}</option>`).join('');

      // Populate Book Management Table
      const booksTbody = document.getElementById('admin-books-tbody');
      booksTbody.innerHTML = allBooks.map(b => {
        const authorNames = b.authors && b.authors.length ? b.authors.map(a => a.author_name).join(', ') : 'Unknown';
        return `
          <tr>
            <td><strong>#${b.book_id}</strong></td>
            <td><a href="/book.html?id=${b.book_id}" style="font-weight:600;color:inherit;text-decoration:none;">${escapeHtml(b.title)}</a></td>
            <td><code>${escapeHtml(b.isbn)}</code></td>
            <td><span class="badge badge-secondary">${escapeHtml(b.category_name)}</span></td>
            <td>${escapeHtml(authorNames)}</td>
            <td>${b.available_copies} / ${b.total_copies} available</td>
            <td>
              <button class="btn btn-outline btn-sm" onclick="openAddCopyModalForBook(${b.book_id}, '${escapeHtml(b.title)}')">+ Copy</button>
              ${currentUser.role === 'admin' ? `<button class="btn btn-danger btn-sm" onclick="deleteBook(${b.book_id})">Delete</button>` : ''}
            </td>
          </tr>
        `;
      }).join('');
    } catch (err) {
      console.error('Failed to load books and copies:', err);
    }
  }

  // Delete Book
  window.deleteBook = async function(bookId) {
    if (!confirm('Are you sure you want to permanently delete this book and its copies?')) return;
    try {
      await API.deleteBook(bookId);
      showToast('Book deleted successfully.', 'success');
      loadAdminData();
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  // Open add copy modal shortcut
  window.openAddCopyModalForBook = function(bookId, title) {
    document.getElementById('copy-book-select').value = bookId;
    switchTab('catalog');
    document.getElementById('new-copy-code').focus();
  };

  // 5. Active Issues (Circulation Desk)
  async function loadActiveIssues() {
    const tbody = document.getElementById('active-issues-tbody');
    try {
      const issues = await API.getIssues();
      const active = issues.filter(i => !i.return_date);

      if (active.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:#64748b;padding:2rem;">No active unreturned loans at this time.</td></tr>';
        return;
      }

      tbody.innerHTML = active.map(i => {
        const isOverdue = i.is_overdue;
        const rowClass = isOverdue ? 'row-overdue' : '';

        const statusBadge = isOverdue
          ? `<span class="badge badge-danger">⚠️ OVERDUE (${i.overdue_days}d)</span>`
          : `<span class="badge badge-success">On Loan</span>`;

        return `
          <tr class="${rowClass}">
            <td><strong>#${i.issue_id}</strong></td>
            <td><strong>${escapeHtml(i.member_name)}</strong><br><small style="color:#64748b;">${escapeHtml(i.member_email)}</small></td>
            <td>${escapeHtml(i.book_title)}<br><small style="color:#64748b;">Copy #${i.copy_id || i.issue_id}</small></td>
            <td>${formatDate(i.issue_date)}</td>
            <td style="${isOverdue ? 'font-weight:700;color:#ef4444;' : ''}">${formatDate(i.due_date)}</td>
            <td>${statusBadge}</td>
            <td>
              <button class="btn btn-primary btn-sm" onclick="returnBook(${i.issue_id}, ${isOverdue}, ${i.overdue_days})">Process Return</button>
            </td>
          </tr>
        `;
      }).join('');
    } catch (err) {
      tbody.innerHTML = `<tr><td colspan="7" style="color:#ef4444;text-align:center;">Failed to load active loans: ${escapeHtml(err.message)}</td></tr>`;
    }
  }

  // Process Return Handler
  window.returnBook = async function(issueId, isOverdue, overdueDays) {
    let confirmMsg = `Process return for Issue #${issueId}?`;
    if (isOverdue) {
      const fineAmount = (overdueDays * 2).toFixed(2);
      confirmMsg += `\n\nNotice: This book is overdue by ${overdueDays} day(s). A fine of ₹${fineAmount} (₹2/day) will be generated!`;
    }

    if (!confirm(confirmMsg)) return;

    try {
      const result = await API.returnBook(issueId);
      if (result.fine) {
        showToast(`Book returned! An overdue fine of ₹${result.fine.amount.toFixed(2)} was registered.`, 'warning');
      } else {
        showToast('Book returned successfully! Copy is now available.', 'success');
      }
      loadAdminData();
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  // 6. Circulation History (All Issues)
  async function loadAllIssues() {
    const tbody = document.getElementById('all-issues-tbody');
    try {
      const issues = await API.getIssues();
      tbody.innerHTML = issues.map(i => {
        const isReturned = !!i.return_date;
        const badge = isReturned
          ? `<span class="badge badge-secondary">Returned (${formatDate(i.return_date)})</span>`
          : i.is_overdue
            ? `<span class="badge badge-danger">Overdue (${i.overdue_days}d)</span>`
            : `<span class="badge badge-success">Active Loan</span>`;

        return `
          <tr class="${i.is_overdue && !isReturned ? 'row-overdue' : ''}">
            <td><strong>#${i.issue_id}</strong></td>
            <td>${escapeHtml(i.member_name)}</td>
            <td>${escapeHtml(i.book_title)} (Copy #${i.copy_id || i.issue_id})</td>
            <td>${formatDate(i.issue_date)}</td>
            <td>${formatDate(i.due_date)}</td>
            <td>${formatDate(i.return_date)}</td>
            <td>${badge}</td>
          </tr>
        `;
      }).join('');
    } catch (err) {
      console.error('Failed to load issue history:', err);
    }
  }

  // 7. Fines Management
  async function loadFines() {
    const tbody = document.getElementById('admin-fines-tbody');
    try {
      const fines = await API.getFines();
      if (fines.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;color:#64748b;padding:2rem;">No fines recorded on file.</td></tr>';
        return;
      }

      tbody.innerHTML = fines.map(f => {
        let statusBadge = '';
        if (f.payment_status === 'paid') {
          statusBadge = '<span class="badge badge-success">Paid</span>';
        } else if (f.payment_status === 'partially_paid') {
          statusBadge = '<span class="badge badge-warning">Partially Paid</span>';
        } else {
          statusBadge = '<span class="badge badge-danger">Unpaid</span>';
        }

        const payBtn = f.remaining_amount > 0
          ? `<button class="btn btn-primary btn-sm" onclick="openRecordPaymentModal(${f.fine_id}, ${f.remaining_amount}, '${escapeHtml(f.member_name)}')">Record Payment</button>`
          : '-';

        return `
          <tr>
            <td><strong>#${f.fine_id}</strong></td>
            <td><strong>${escapeHtml(f.member_name)}</strong><br><small style="color:#64748b;">${escapeHtml(f.member_email)}</small></td>
            <td>${escapeHtml(f.book_title)} (Copy #${f.copy_id || f.issue_id})</td>
            <td>${formatDate(f.due_date)} → ${formatDate(f.return_date)}</td>
            <td>${formatCurrency(f.fine_amount || f.amount)}</td>
            <td>${formatCurrency(f.amount_paid)}</td>
            <td style="font-weight:700;${f.remaining_amount > 0 ? 'color:#ef4444;' : 'color:#10b981;'}">${formatCurrency(f.remaining_amount)}</td>
            <td>${statusBadge} ${payBtn}</td>
          </tr>
        `;
      }).join('');
    } catch (err) {
      console.error('Failed to load fines:', err);
    }
  }

  // Record Payment Modal
  const fineModal = document.getElementById('modal-admin-pay-fine');
  const fineForm = document.getElementById('form-admin-pay-fine');
  let currentFineId = null;

  window.openRecordPaymentModal = function(fineId, balance, memberName) {
    currentFineId = fineId;
    document.getElementById('admin-pay-member-name').textContent = memberName;
    document.getElementById('admin-pay-amount').value = balance.toFixed(2);
    document.getElementById('admin-pay-balance').textContent = formatCurrency(balance);
    fineModal.classList.add('open');
  };

  document.getElementById('btn-close-admin-pay-modal').addEventListener('click', () => {
    fineModal.classList.remove('open');
  });

  fineForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const amount = parseFloat(document.getElementById('admin-pay-amount').value);
    if (!amount || amount <= 0) return;

    try {
      await API.payFine(currentFineId, amount);
      showToast('Payment recorded successfully!', 'success');
      fineModal.classList.remove('open');
      loadAdminData();
    } catch (err) {
      showToast(err.message, 'error');
    }
  });

  // -----------------------------------------------------------------------
  // Form Event Handlers
  // -----------------------------------------------------------------------

  // Issue Book Form
  const formIssue = document.getElementById('form-issue-book');
  formIssue.addEventListener('submit', async (e) => {
    e.preventDefault();
    const memberId = document.getElementById('issue-member-select').value;
    const copyId = document.getElementById('issue-copy-select').value;
    const issueDate = document.getElementById('issue-date').value || null;
    const dueDate = document.getElementById('issue-due-date').value || null;

    if (!memberId || !copyId) {
      showToast('Please select both a Member and an Available Copy.', 'error');
      return;
    }

    try {
      await API.issueBook({
        member_id: memberId,
        copy_id: copyId,
        issue_date: issueDate,
        due_date: dueDate
      });
      showToast('Book issued successfully!', 'success');
      formIssue.reset();
      loadAdminData();
    } catch (err) {
      showToast(err.message, 'error');
    }
  });

  // Add Book Form
  const formAddBook = document.getElementById('form-add-book');
  formAddBook.addEventListener('submit', async (e) => {
    e.preventDefault();
    const title = document.getElementById('new-book-title').value.trim();
    const isbn = document.getElementById('new-book-isbn').value.trim();
    const category_id = document.getElementById('new-book-category').value;
    const publisher = document.getElementById('new-book-publisher').value.trim();
    const publication_year = document.getElementById('new-book-year').value;

    const selectedAuthors = Array.from(document.querySelectorAll('#new-book-authors-list input[type="checkbox"]:checked')).map(cb => cb.value);

    try {
      await API.createBook({
        title,
        isbn,
        category_id,
        publisher,
        publication_year,
        author_ids: selectedAuthors
      });
      showToast('New title registered into catalog with 1 available copy!', 'success');
      formAddBook.reset();
      loadAdminData();
    } catch (err) {
      showToast(err.message, 'error');
    }
  });

  // Add Copy Form
  const formAddCopy = document.getElementById('form-add-copy-admin');
  formAddCopy.addEventListener('submit', async (e) => {
    e.preventDefault();
    const book_id = document.getElementById('copy-book-select').value;

    if (!book_id) {
      showToast('Please select a book to add a copy.', 'error');
      return;
    }

    try {
      await API.createCopy(book_id);
      showToast('Book copy added successfully to inventory!', 'success');
      formAddCopy.reset();
      loadAdminData();
    } catch (err) {
      showToast(err.message, 'error');
    }
  });

  // Quick Add Category Modal
  const modalCat = document.getElementById('modal-add-category');
  document.getElementById('btn-open-category-modal').addEventListener('click', () => modalCat.classList.add('open'));
  document.getElementById('btn-close-cat-modal').addEventListener('click', () => modalCat.classList.remove('open'));
  document.getElementById('form-add-category').addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = document.getElementById('new-category-name').value.trim();
    if (!name) return;
    try {
      await API.createCategory(name);
      showToast(`Category "${name}" created!`, 'success');
      modalCat.classList.remove('open');
      document.getElementById('new-category-name').value = '';
      loadCategoriesAndAuthors();
    } catch (err) {
      showToast(err.message, 'error');
    }
  });

  // Quick Add Author Modal
  const modalAuth = document.getElementById('modal-add-author');
  document.getElementById('btn-open-author-modal').addEventListener('click', () => modalAuth.classList.add('open'));
  document.getElementById('btn-close-auth-modal').addEventListener('click', () => modalAuth.classList.remove('open'));
  document.getElementById('form-add-author').addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = document.getElementById('new-author-name').value.trim();
    if (!name) return;
    try {
      await API.createAuthor(name);
      showToast(`Author "${name}" added!`, 'success');
      modalAuth.classList.remove('open');
      document.getElementById('new-author-name').value = '';
      loadCategoriesAndAuthors();
    } catch (err) {
      showToast(err.message, 'error');
    }
  });
});
