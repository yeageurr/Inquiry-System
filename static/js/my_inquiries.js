function setFilter(value) {
    const url = new URL(window.location.href);
    url.searchParams.set('status', value);
    window.location.href = url.toString();
}