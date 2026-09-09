/**
 * TeleLearn AI – main.js
 * Global UI helpers: sidebar toggle, alert auto-dismiss, mobile overlay
 */

document.addEventListener('DOMContentLoaded', () => {
  initSidebar();
  initAlerts();
  initTooltips();
});

/* ─── Sidebar Toggle (mobile) ─────────────────── */
function initSidebar() {
  const toggleBtn = document.getElementById('sidebarToggle');
  const sidebar   = document.getElementById('sidebar');
  const mainContent = document.getElementById('mainContent');

  if (!toggleBtn || !sidebar) return;

  toggleBtn.addEventListener('click', () => {
    sidebar.classList.toggle('open');
    toggleBtn.innerHTML = sidebar.classList.contains('open')
      ? '<i class="fas fa-times"></i>'
      : '<i class="fas fa-bars"></i>';
  });

  // Close when clicking outside on mobile
  document.addEventListener('click', (e) => {
    if (window.innerWidth > 992) return;
    if (sidebar.classList.contains('open') &&
        !sidebar.contains(e.target) &&
        !toggleBtn.contains(e.target)) {
      sidebar.classList.remove('open');
      toggleBtn.innerHTML = '<i class="fas fa-bars"></i>';
    }
  });
}

/* ─── Auto-dismiss alerts ─────────────────────── */
function initAlerts() {
  document.querySelectorAll('.alert.alert-success, .alert.alert-info').forEach(alert => {
    setTimeout(() => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      if (bsAlert) bsAlert.close();
    }, 4000);
  });
}

/* ─── Bootstrap tooltips ──────────────────────── */
function initTooltips() {
  document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
    new bootstrap.Tooltip(el);
  });
}

/* ─── Number animation for dashboard stats ─────── */
function animateNumber(el, target, duration = 800) {
  const start = 0;
  const startTime = performance.now();
  const update = (currentTime) => {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    el.textContent = Math.round(start + (target - start) * eased);
    if (progress < 1) requestAnimationFrame(update);
  };
  requestAnimationFrame(update);
}

/* ─── Expose helpers globally ─────────────────── */
window.TeleLearnUtils = {
  animateNumber,

  showToast(message, type = 'info') {
    const container = document.querySelector('.flash-container') || (() => {
      const c = document.createElement('div');
      c.className = 'flash-container';
      document.querySelector('.main-content')?.prepend(c);
      return c;
    })();

    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.innerHTML = `${message}<button type="button" class="btn-close" data-bs-dismiss="alert"></button>`;
    container.appendChild(alert);

    setTimeout(() => {
      if (alert.parentNode) {
        const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
        if (bsAlert) bsAlert.close();
      }
    }, 4000);
  },

  formatDate(dateStr) {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', { year:'numeric', month:'short', day:'numeric' });
  },

  debounce(fn, wait) {
    let timer;
    return (...args) => { clearTimeout(timer); timer = setTimeout(() => fn(...args), wait); };
  }
};
