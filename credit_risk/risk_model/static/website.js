document.addEventListener('DOMContentLoaded', () => {
    const sidebarToggle = document.getElementById('sidebarToggle');
    console.log('Sidebar Toggle:', sidebarToggle);
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
            // formContent.classList.toggle('full-width');
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
        creditForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(creditForm);
            try {
                const response = await fetch('/risk_model/predict/', {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                    }
                });

                if (response.ok) {
                    const data = await response.json();
                    alert(`Prediction Result: ${data.prediction_result}`);
                    window.location.href = '/risk_model/show_prediction/';
                } else {
                    alert('Error in prediction submission.');
                }
            } catch (error) {
                console.error('Error submitting form:', error);
                alert('An unexpected error occurred.');
            }
        });
    }

    const adminForm = document.getElementById('adminForm');
    if (adminForm) {
        adminForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const formData = new FormData(adminForm);
            try {
                const response = await fetch('/risk_model/admin_login/', {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                    }
                });

                if (response.ok) {
                    const data = await response.json();
                    if (data.success) {
                        alert('Login Successful!');
                        window.location.href = '/risk_model/admin/';
                    } else {
                        alert('Invalid Login Credentials');
                    }
                } else {
                    alert('Error logging in.');
                }
            } catch (error) {
                console.error('Error during login:', error);
                alert('An unexpected error occurred.');
            }
        });
    }
});
