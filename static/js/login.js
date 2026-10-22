document.addEventListener('DOMContentLoaded', async () => {
  const user = await setupNavbar('login');
  if (user) {
    // Already logged in, redirect to appropriate page
    window.location.href = (user.role === 'admin' || user.role === 'librarian') ? '/admin.html' : '/dashboard.html';
    return;
  }

  const form = document.getElementById('login-form');
  const errorAlert = document.getElementById('login-error');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    errorAlert.style.display = 'none';

    const email = document.getElementById('login-email').value.trim();
    const password = document.getElementById('login-password').value;
    const submitBtn = document.getElementById('login-submit-btn');

    try {
      submitBtn.disabled = true;
      submitBtn.textContent = 'Signing in...';

      const res = await API.login(email, password);
      showToast('Login successful! Redirecting...', 'success');

      localStorage.setItem('smartlib_user', JSON.stringify(res.user));

      setTimeout(() => {
        if (res.user.role === 'admin' || res.user.role === 'librarian') {
          window.location.href = '/admin.html';
        } else {
          window.location.href = '/dashboard.html';
        }
      }, 700);
    } catch (err) {
      errorAlert.textContent = err.message || 'Login failed. Please verify your credentials.';
      errorAlert.style.display = 'block';
      showToast(err.message, 'error');
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = 'Sign In';
    }
  });

  // Demo user quick login buttons helper
  window.fillCredentials = function(email, password) {
    document.getElementById('login-email').value = email;
    document.getElementById('login-password').value = password;
  };
});
