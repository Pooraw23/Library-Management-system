let currentUser = null;

document.addEventListener('DOMContentLoaded', async () => {
  currentUser = await setupNavbar('dashboard');

  if (!currentUser) {
    window.location.href = '/login.html';
    return;
  }

  // Load Dashboard Data
  async function loadDashboard() {
    await Promise.all([
      loadMemberStats(),
      loadIssuedBooks(),
      loadReturnedBooks(),
      loadReservations(),
      loadFines()
    ]);
  }

  // Member Quick Stats
  async function loadMemberStats() {
    try {
      const stats = await API.getStats();
      document.getElementById('member-welcome-name').textContent = currentUser.name;
      document.getElementById('stat-active-issues').textContent = `${stats.active_issues_count} / 3`;
      
      const overdueEl = document.getElementById('stat-overdue-count');
      overdueEl.textContent = stats.overdue_count;
      if (stats.overdue_count > 0) {
        overdueEl.className = 'stat-value text-danger-bold';
      }

      document.getElementById('stat-reservations-count').textContent = stats.active_reservations_count;
      document.getElementById('stat-unpaid-fines').textContent = formatCurrency(stats.unpaid_fines_total);
    } catch (err) {
      console.error('Failed to load user stats:', err);
    }
  }

  // 1. My Issued Books (Active)
  async function loadIssuedBooks() {
    const tbody = document.getElementById('issued-books-tbody');
    try {
      const issues = await API.getIssues();
      const activeIssues = issues.filter(i => !i.return_date);

      if (activeIssues.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:#64748b;padding:2rem;">You currently have no borrowed books.</td></tr>';
        return;
      }

      tbody.innerHTML = activeIssues.map(i => {
        const isOverdue = i.is_overdue;
        const rowClass = isOverdue ? 'row-overdue' : '';

        const statusBadge = isOverdue
          ? `<span class="badge badge-danger">⚠️ OVERDUE (${i.overdue_days} day${i.overdue_days === 1 ? '' : 's'})</span>`
          : `<span class="badge badge-success">Active Loan</span>`;

        return `
          <tr class="${rowClass}">
            <td>
              <a href="/book.html?id=${i.book_id}" style="font-weight:600;color:inherit;text-decoration:none;">
                ${escapeHtml(i.book_title)}
              </a>
            </td>
            <td><code>Copy #${i.copy_id || i.issue_id}</code></td>
            <td>${formatDate(i.issue_date)}</td>
            <td style="${isOverdue ? 'font-weight:700;color:#ef4444;' : ''}">${formatDate(i.due_date)}</td>
            <td>${statusBadge}</td>
            <td>
              <button type="button" class="btn btn-sm btn-primary" style="padding:0.35rem 0.75rem; font-size:0.8rem; font-weight:600; display:inline-flex; align-items:center; gap:0.3rem;" onclick="returnMyBook(${i.issue_id}, '${escapeHtml(i.book_title)}')">
                ↩ Return Book
              </button>
            </td>
          </tr>
        `;
      }).join('');
    } catch (err) {
      tbody.innerHTML = `<tr><td colspan="6" style="color:#ef4444;text-align:center;">Failed to load issued books: ${escapeHtml(err.message)}</td></tr>`;
    }
  }

  // 1b. My Returned Books History
  async function loadReturnedBooks() {
    const tbody = document.getElementById('returned-books-tbody');
    if (!tbody) return;
    try {
      const issues = await API.getIssues();
      const returnedIssues = issues.filter(i => !!i.return_date);

      if (returnedIssues.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:#64748b;padding:2rem;">No returned books on record yet.</td></tr>';
        return;
      }

      tbody.innerHTML = returnedIssues.map(i => {
        const wasOverdue = new Date(i.return_date) > new Date(i.due_date);
        const statusBadge = wasOverdue
          ? '<span class="badge badge-warning">Returned Overdue</span>'
          : '<span class="badge badge-success">Returned On-Time</span>';

        return `
          <tr>
            <td>
              <a href="/book.html?id=${i.book_id}" style="font-weight:600;color:inherit;text-decoration:none;">
                ${escapeHtml(i.book_title)}
              </a>
            </td>
            <td><code>Copy #${i.copy_id || i.issue_id}</code></td>
            <td>${formatDate(i.issue_date)}</td>
            <td>${formatDate(i.due_date)}</td>
            <td style="font-weight:700; color:var(--primary);">${formatDate(i.return_date)}</td>
            <td>${statusBadge}</td>
          </tr>
        `;
      }).join('');
    } catch (err) {
      tbody.innerHTML = `<tr><td colspan="6" style="color:#ef4444;text-align:center;">Failed to load return history: ${escapeHtml(err.message)}</td></tr>`;
    }
  }

  // Global Return Handler for Students
  window.returnMyBook = async (issueId, bookTitle) => {
    if (!confirm(`Are you sure you want to return "${bookTitle}"?`)) return;

    try {
      const res = await API.returnBook(issueId);
      if (res.fine && res.fine.amount > 0) {
        showToast(`Book returned! Late fine of ₹${Number(res.fine.amount).toFixed(2)} applied (₹2.00/day).`, 'warning');
      } else {
        showToast(`Book returned successfully on time! Inventory updated.`, 'success');
      }
      await loadDashboard();
    } catch (err) {
      showToast('Failed to return book: ' + (err.message || err), 'error');
    }
  };

  // 2. My Reservations
  async function loadReservations() {
    const tbody = document.getElementById('reservations-tbody');
    try {
      const reservations = await API.getReservations();

      if (reservations.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:#64748b;padding:2rem;">No reservations on file.</td></tr>';
        return;
      }

      tbody.innerHTML = reservations.map(r => {
        let statusBadge = '';
        if (r.status === 'pending') {
          statusBadge = '<span class="badge badge-warning">Waiting in Queue</span>';
        } else if (r.status === 'fulfilled') {
          statusBadge = '<span class="badge badge-success">Fulfilled</span>';
        } else {
          statusBadge = '<span class="badge badge-secondary">Cancelled</span>';
        }

        const cancelAction = r.status === 'pending'
          ? `<button class="btn btn-outline btn-sm" onclick="cancelReservation(${r.reservation_id})">Cancel</button>`
          : '-';

        return `
          <tr>
            <td>
              <a href="/book.html?id=${r.book_id}" style="font-weight:600;color:inherit;text-decoration:none;">
                ${escapeHtml(r.book_title)}
              </a>
            </td>
            <td><code>${escapeHtml(r.isbn)}</code></td>
            <td>${formatDate(r.reserved_at)}</td>
            <td>${statusBadge}</td>
            <td>${cancelAction}</td>
          </tr>
        `;
      }).join('');
    } catch (err) {
      tbody.innerHTML = `<tr><td colspan="5" style="color:#ef4444;text-align:center;">Failed to load reservations: ${escapeHtml(err.message)}</td></tr>`;
    }
  }

  window.cancelReservation = async function(resId) {
    if (!confirm('Are you sure you want to cancel this reservation?')) return;
    try {
      await API.cancelReservation(resId);
      showToast('Reservation cancelled successfully.', 'success');
      loadReservations();
      loadMemberStats();
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  // 3. My Fines
  async function loadFines() {
    const tbody = document.getElementById('fines-tbody');
    try {
      const fines = await API.getFines();

      if (fines.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:#64748b;padding:2rem;">You have zero library fines. Great job!</td></tr>';
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
          ? `<button class="btn btn-primary btn-sm" onclick="openPaymentModal(${f.fine_id}, ${f.remaining_amount})">Pay Fine</button>`
          : '-';

        return `
          <tr>
            <td><strong>${escapeHtml(f.book_title)}</strong> (Copy #${f.copy_id || f.issue_id})</td>
            <td>${formatDate(f.due_date)} → ${formatDate(f.return_date)}</td>
            <td style="font-weight:700; color:#ef4444;">${formatCurrency(f.fine_amount || f.amount)}</td>
            <td>${statusBadge}</td>
            <td>${payBtn}</td>
          </tr>
        `;
      }).join('');
    } catch (err) {
      tbody.innerHTML = `<tr><td colspan="6" style="color:#ef4444;text-align:center;">Failed to load fines: ${escapeHtml(err.message)}</td></tr>`;
    }
  }

  // Payment Modal Handling
  const paymentModal = document.getElementById('modal-pay-fine');
  const payForm = document.getElementById('form-pay-fine');
  const closePayModalBtn = document.getElementById('btn-close-pay-modal');

  let activeFineId = null;

  window.openPaymentModal = function(fineId, remainingAmount) {
    activeFineId = fineId;
    document.getElementById('pay-fine-amount').value = remainingAmount.toFixed(2);
    document.getElementById('pay-fine-balance').textContent = formatCurrency(remainingAmount);
    paymentModal.classList.add('open');
  };

  if (closePayModalBtn) {
    closePayModalBtn.addEventListener('click', () => {
      paymentModal.classList.remove('open');
    });
  }

  if (payForm) {
    payForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const amount = parseFloat(document.getElementById('pay-fine-amount').value);
      if (!amount || amount <= 0) return;

      try {
        await API.payFine(activeFineId, amount);
        showToast('Fine payment completed successfully!', 'success');
        paymentModal.classList.remove('open');
        loadFines();
        loadMemberStats();
      } catch (err) {
        showToast(err.message, 'error');
      }
    });
  }

  // Initial load
  loadDashboard();
});
