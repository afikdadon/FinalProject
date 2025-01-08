document.addEventListener('DOMContentLoaded', function() {
    console.log('Registration JavaScript loaded');
    const form = document.getElementById('registrationForm');
    const firstNameInput = document.getElementById('first_name');
    const lastNameInput = document.getElementById('last_name');
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirm_password');

    // Toggle password visibility
    document.querySelectorAll('.toggle-password').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const input = this.parentElement.querySelector('input');
            const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
            input.setAttribute('type', type);
            this.querySelector('i').classList.toggle('fa-eye');
            this.querySelector('i').classList.toggle('fa-eye-slash');
        });
    });

    // Show error message
    function showError(input, message) {
        const formGroup = input.closest('.form-group');
        let errorDiv = formGroup.querySelector('.error-message');

        if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.className = 'error-message';
            formGroup.appendChild(errorDiv);
        }

        errorDiv.textContent = message;
        input.classList.add('error');
    }

    // Clear error message
    function clearError(input) {
        const formGroup = input.closest('.form-group');
        const errorDiv = formGroup.querySelector('.error-message');
        if (errorDiv) {
            errorDiv.remove();
        }
        input.classList.remove('error');
    }

    // Clear all errors
    function clearAllErrors() {
        document.querySelectorAll('.error-message').forEach(err => err.remove());
        document.querySelectorAll('.error').forEach(input => input.classList.remove('error'));
    }

    // Form submission
    form.addEventListener('submit', async function(e) {
        e.preventDefault(); // Prevent default form submission

        clearAllErrors();
        const formData = new FormData(form);

        try {
            const response = await fetch(form.action, {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                window.location.href = '/login';
            } else {
                // Show error message under the relevant field
                if (result.error.includes('אימייל')) {
                    showError(emailInput, result.error);
                } else if (result.error.includes('סיסמה')) {
                    showError(passwordInput, result.error);
                } else if (result.error.includes('שם פרטי')) {
                    showError(firstNameInput, result.error);
                } else if (result.error.includes('שם משפחה')) {
                    showError(lastNameInput, result.error);
                } else {
                    // Show general error under first input
                    showError(firstNameInput, result.error);
                }
            }
        } catch (error) {
            console.error('Error:', error);
            showError(firstNameInput, 'אירעה שגיאה. אנא נסה שנית מאוחר יותר');
        }
    });

    // Real-time validation
    firstNameInput.addEventListener('input', () => {
        clearError(firstNameInput);
    });

    lastNameInput.addEventListener('input', () => {
        clearError(lastNameInput);
    });

    emailInput.addEventListener('input', () => {
        clearError(emailInput);
    });

    passwordInput.addEventListener('input', () => {
        clearError(passwordInput);
        if (confirmPasswordInput.value && confirmPasswordInput.value !== passwordInput.value) {
            showError(confirmPasswordInput, 'הסיסמאות אינן תואמות');
        } else {
            clearError(confirmPasswordInput);
        }
    });

    confirmPasswordInput.addEventListener('input', () => {
        clearError(confirmPasswordInput);
        if (confirmPasswordInput.value !== passwordInput.value) {
            showError(confirmPasswordInput, 'הסיסמאות אינן תואמות');
        }
    });
});