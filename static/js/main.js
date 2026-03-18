/**
 * main.js - DigiLib Frontend Scripts
 */
document.addEventListener('DOMContentLoaded', function () {

  // Auto-dismiss flash alerts after 5 seconds
  document.querySelectorAll('.lib-alert').forEach(alert => {
    setTimeout(() => {
      try { new bootstrap.Alert(alert).close(); } catch(e) {}
    }, 5000);
  });

  // Mobile number — digits only
  document.querySelectorAll('input[name="mobile"]').forEach(el => {
    el.addEventListener('input', function () {
      this.value = this.value.replace(/\D/g, '').slice(0, 10);
    });
  });

  // Active nav highlight
  const path = window.location.pathname;
  document.querySelectorAll('.nav-link').forEach(link => {
    if (link.getAttribute('href') === path) link.classList.add('active');
  });

});
