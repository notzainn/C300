document.addEventListener('DOMContentLoaded', () => {
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    const formContent = document.getElementById('formContent');
    const adminLogin = document.getElementById('adminLogin');
    const adminLoginButton = document.getElementById('adminLoginButton');
    const toggleForm = document.getElementById('toggleForm');

    // Ensure elements exist before adding event listeners
    if (sidebarToggle) {
        // Toggle sidebar visibility
        sidebarToggle.addEventListener('click', () => {
            sidebar.classList.toggle('hidden');
            formContent.classList.toggle('full-width');
        });
    }

    if (adminLoginButton) {
        // Show admin login
        adminLoginButton.addEventListener('click', () => {
            formContent.style.display = 'none';
            adminLogin.style.display = 'block';
        });
    }

    if (toggleForm) {
        // Show credit rating form
        toggleForm.addEventListener('click', () => {
            adminLogin.style.display = 'none';
            formContent.style.display = 'block';
        });
    }

    // Example form submission handling
    const creditForm = document.getElementById('creditForm');
    if (creditForm) {
        creditForm.addEventListener('submit', (e) => {
            e.preventDefault();
            alert('Credit Rating Prediction Submitted!');
        });
    }

    const adminForm = document.getElementById('adminForm');
    if (adminForm) {
        adminForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            if (username === 'admin' && password === 'password123') {
                alert('Login Successful!');
                window.location.href = 'admin.html'; // Navigate to admin page
            } else {
                alert('Invalid Login Credentials');
            }
        });
    }
});
