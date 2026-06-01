function filterLogs() {
    const search = document.getElementById('search-input').value.toLowerCase();
    const action = document.getElementById('action-filter').value;
    document.querySelectorAll('#logs-table tbody tr').forEach(row => {
        if (row.querySelector('.empty-row')) return;
        const rowAction = row.dataset.action || '';
        const rowSearch = row.dataset.search || '';
        const matchA = action === 'All' || rowAction === action;
        const matchS = rowSearch.includes(search);
        row.style.display = (matchA && matchS) ? '' : 'none';
    });
}

window.showDetails = function(btn) {
    const raw = btn.dataset.details;
    const pre = document.getElementById('details-content');
    try {
        const parsed = JSON.parse(raw);
        pre.textContent = JSON.stringify(parsed, null, 2);
    } catch(e) {
        pre.textContent = raw || '—';
    }
    openModal('details-modal');
};