let currentInquiryId = null;

// ── Filter ────────────────────────────────────────────────────────────────
function filterInquiries() {
    const search = document.getElementById('search-input').value.toLowerCase();
    const status = document.getElementById('status-filter').value;
    document.querySelectorAll('#inquiries-table tbody tr').forEach(row => {
        if (row.querySelector('.empty-row')) return;
        const rowSearch = row.dataset.search || '';
        const rowStatus = row.dataset.status || '';
        const matchS = rowSearch.includes(search);
        const matchF = status === 'All' || rowStatus === status;
        row.style.display = (matchS && matchF) ? '' : 'none';
    });
}

// ── Respond modal ─────────────────────────────────────────────────────────
window.openRespondModal = function(btn) {
    currentInquiryId = btn.dataset.id;
    document.getElementById('modal-student').textContent = btn.dataset.student;
    document.getElementById('modal-product').textContent = btn.dataset.product;
    document.getElementById('modal-message').textContent = btn.dataset.message;
    document.getElementById('response-text').value = '';
    document.getElementById('char-count').textContent = '0';
    openModal('respond-modal');
};

function updateCharCount() {
    const len = document.getElementById('response-text').value.length;
    document.getElementById('char-count').textContent = len;
}

async function submitResponse() {
    const message = document.getElementById('response-text').value.trim();
    if (!message) {
        showToast('Response cannot be empty.', 'error'); return;
    }
    if (message.length < 10) {
        showToast('Response must be at least 10 characters.', 'error'); return;
    }

    const formData = new FormData();
    formData.append('response_message', message);

    try {
        const res = await fetch(
            `/admin/inquiries/respond/${currentInquiryId}`,
            { method: 'POST', body: formData }
        );
        const data = await res.json();
        if (data.success) {
            showToast(data.message, 'success');
            closeModal('respond-modal');
            setTimeout(() => location.reload(), 1500);
        } else {
            showToast(data.error || 'Something went wrong.', 'error');
        }
    } catch(e) {
        showToast('Something went wrong. Please try again.', 'error');
    }
}