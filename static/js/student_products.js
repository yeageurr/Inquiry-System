let currentProductId = null;

function setFilter(value) {
	const url = new URL(window.location.href);
	url.searchParams.set('status', value);
	window.location.href = url.toString();
}

function filterProducts() {
	const search = document.getElementById('search-input').value.toLowerCase();
	document.querySelectorAll('.product-card').forEach(card => {
			const name = card.dataset.name || '';
			card.style.display = name.includes(search) ? '' : 'none';
	});
}

window.openInquireModal = function(btn) {
	currentProductId = btn.dataset.id;
	document.getElementById('inquire-product-name').textContent = btn.dataset.name;
	document.getElementById('inquire-message').value = '';
	openModal('inquire-modal');
};

async function submitInquiry() {
	const message = document.getElementById('inquire-message').value.trim();
	if (!message) {
			showToast('Please enter a message.', 'error'); return;
	}

	const formData = new FormData();
	formData.append('product_id', currentProductId);
	formData.append('message',    message);

	try {
			const res  = await fetch('/student/inquiries/submit',
					{ method: 'POST', body: formData });
			const data = await res.json();
			if (data.success) {
					showToast(data.message, 'success');
					closeModal('inquire-modal');
			} else {
					showToast(data.error || 'Something went wrong.', 'error');
			}
	} catch(e) {
			showToast('Something went wrong. Please try again.', 'error');
	}
}