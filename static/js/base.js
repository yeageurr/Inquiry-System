// Date display
const dateEl = document.getElementById('page-date');
if (dateEl) {
    const now = new Date();
    dateEl.textContent = now.toLocaleDateString('en-US', {
        weekday: 'long', year: 'numeric',
        month: 'long', day: 'numeric'
    });
}

// Toast
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    if (!toast) return;
    toast.textContent = message;
    toast.className = `toast show ${type}`;
    setTimeout(() => { toast.className = 'toast'; }, 3500);
}

// Modal helpers
function openModal(id)  {
    document.getElementById(id).classList.add('open');
}
function closeModal(id) {
    document.getElementById(id).classList.remove('open');
}

// Close modal on overlay click
document.querySelectorAll('.modal-overlay').forEach(overlay => {
    overlay.addEventListener('click', function(e) {
        if (e.target === this) this.classList.remove('open');
    });
});

// Close modal on Escape key
document.addEventListener('keydown', e => {
    if (e.key === 'Escape') {
        document.querySelectorAll('.modal-overlay.open')
            .forEach(m => m.classList.remove('open'));
    }
});

// ── Sidebar toggle for mobile ─────────────────────────────────────────────
window.toggleSidebar = function() {
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    sidebar.classList.toggle('open');
    overlay.classList.toggle('open');
};

window.closeSidebar = function() {
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    sidebar.classList.remove('open');
    overlay.classList.remove('open');
};

// Close sidebar on nav item click (mobile)
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', () => {
            if (window.innerWidth <= 768) closeSidebar();
        });
    });
});