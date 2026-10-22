document.addEventListener('DOMContentLoaded', async () => {
  const user = await setupNavbar('register');
  if (user) {
    window.location.href = (user.role === 'admin' || user.role === 'librarian') ? '/admin.html' : '/dashboard.html';
    return;
  }

  const form = document.getElementById('register-form');
  const errorAlert = document.getElementById('register-error');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    errorAlert.style.display = 'none';

    const name = document.getElementById('reg-name').value.trim();
    const email = document.getElementById('reg-email').value.trim();
    const password = document.getElementById('reg-password').value;
    const confirmPassword = document.getElementById('reg-confirm-password').value;
    const department = document.getElementById('reg-department').value.trim();
    const submitBtn = document.getElementById('register-submit-btn');

    if (password !== confirmPassword) {
      errorAlert.textContent = 'Passwords do not match.';
      errorAlert.style.display = 'block';
      return;
    }

    try {
      submitBtn.disabled = true;
      submitBtn.textContent = 'Creating account...';

      const res = await API.register({
        name,
        email,
        password,
        department,
        role: 'member'
      });

      showToast('Registration complete! Welcome to SmartLib.', 'success');
      localStorage.setItem('smartlib_user', JSON.stringify(res.user));

      setTimeout(() => {
        window.location.href = '/dashboard.html';
      }, 800);
    } catch (err) {
      errorAlert.textContent = err.message || 'Registration failed. Please check inputs.';
      errorAlert.style.display = 'block';
      showToast(err.message, 'error');
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = 'Create Account';
    }
  });
});
