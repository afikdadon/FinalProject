// Reset_Password.js
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('resetPasswordForm');
    const newPasswordInput = document.getElementById('new_password');
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

    function clearError(input) {
        const formGroup = input.closest('.form-group');
        const errorDiv = formGroup.querySelector('.error-message');
        if (errorDiv) {
            errorDiv.remove();
        }
        input.classList.remove('error');
    }

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        clearError(newPasswordInput);
        clearError(confirmPasswordInput);

        const formData = new FormData(form);

        try {
            const response = await fetch(form.action, {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                // Replace form with success message and redirect
                form.innerHTML = `
                    <div class="success-message">
                        <p>הסיסמה עודכנה בהצלחה!</p>
                        <p>מעביר אותך לדף ההתחברות...</p>
                    </div>`;
                setTimeout(() => {
                    window.location.href = '/login';
                }, 3000);
            } else {
                if (result.error.includes('תואמות')) {
                    showError(confirmPasswordInput, result.error);
                } else {
                    showError(newPasswordInput, result.error);
                }
            }
        } catch (error) {
            console.error('Error:', error);
            showError(newPasswordInput, 'אירעה שגיאה. אנא נסה שנית מאוחר יותר');
        }
    });

    newPasswordInput.addEventListener('input', () => {
        clearError(newPasswordInput);
    });

    confirmPasswordInput.addEventListener('input', () => {
        clearError(confirmPasswordInput);
    });
});