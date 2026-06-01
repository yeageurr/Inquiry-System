function togglePassword() {
    const input   = document.getElementById('password');
    const icon    = document.getElementById('eye-icon');
    const isText  = input.type === 'text';
    input.type    = isText ? 'password' : 'text';
    icon.className = isText ? 'ti ti-eye' : 'ti ti-eye-off';
}