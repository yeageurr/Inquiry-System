// ── Filter ────────────────────────────────────────────────────────────────
function filterProducts() {
    const search = document.getElementById('search-input').value.toLowerCase();
    const status = document.getElementById('status-filter').value;
    document.querySelectorAll('#products-table tbody tr').forEach(row => {
        if (row.querySelector('.empty-row')) return;
        const name   = row.dataset.name   || '';
        const rowSt  = row.dataset.status || '';
        const matchS = name.includes(search);
        const matchF = status === 'All' || rowSt === status;
        row.style.display = (matchS && matchF) ? '' : 'none';
    });
}

// ── Add modal ─────────────────────────────────────────────────────────────
function openAddModal() { openModal('add-modal'); }

// ── Edit modal ────────────────────────────────────────────────────────────
window.openEditModal = function(btn) {
    const id     = btn.dataset.id;
    const name   = btn.dataset.name;
    const desc   = btn.dataset.desc;
    const price  = btn.dataset.price;
    const status = btn.dataset.status;

    document.getElementById('edit-name').value   = name;
    document.getElementById('edit-desc').value   = desc;
    document.getElementById('edit-price').value  = price;
    document.getElementById('edit-status').value = status;
    document.getElementById('edit-form').action  = `/admin/products/edit/${id}`;
    openModal('edit-modal');
};

// ── Delete modal ──────────────────────────────────────────────────────────
window.openDeleteModal = function(btn) {
    const id   = btn.dataset.id;
    const name = btn.dataset.name;

    document.getElementById('delete-name').textContent = name;
    document.getElementById('delete-form').action = `/admin/products/delete/${id}`;
    openModal('delete-modal');
};