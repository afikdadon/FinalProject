// forgot_password.js (place in Login_Page/static/js)
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('forgotPasswordForm');
    const emailInput = document.getElementById('email');

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
        clearError(emailInput);

        const formData = new FormData(form);

        try {
            const response = await fetch(form.action, {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                // Replace form with success message
                form.innerHTML = `
                    <div class="success-message">
                        <p>קישור לאיפוס הסיסמה נשלח לכתובת האימייל שלך.</p>
                        <p>הקישור תקף למשך שעה אחת.</p>
                    </div>`;
            } else {
                showError(emailInput, result.error);
            }
        } catch (error) {
            console.error('Error:', error);
            showError(emailInput, 'אירעה שגיאה. אנא נסה שנית מאוחר יותר');
        }
    });

    emailInput.addEventListener('input', () => {
        clearError(emailInput);
    });
});