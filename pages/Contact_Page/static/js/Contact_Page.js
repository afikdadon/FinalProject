document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('contactForm');
    const submitBtn = document.getElementById('submitBtn');
    const inputs = form.querySelectorAll('input, textarea');

    // Add focus animation to inputs
    inputs.forEach(input => {
        input.addEventListener('focus', function() {
            this.parentElement.classList.add('focused');
        });

        input.addEventListener('blur', function() {
            if (!this.value) {
                this.parentElement.classList.remove('focused');
            }
        });
    });

    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        // Validate form
        if (!validateForm()) return;

        // Add sending class for animation
        submitBtn.classList.add('sending');

        try {
            const formData = new FormData(form);
            const response = await fetch(form.action, {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                // Animate the form away
                form.style.animation = 'sendMessage 0.5s ease-out forwards';

                // Show success message with animation
                const successMessage = document.createElement('div');
                successMessage.className = 'flash-message flash-success';
                successMessage.textContent = 'ההודעה נשלחה בהצלחה!';
                form.parentElement.insertBefore(successMessage, form);

                // Wait for animation to complete then reload
                setTimeout(() => {
                    window.location.href = '/';
                }, 1500);
            } else {
                throw new Error('Something went wrong');
            }
        } catch (error) {
            console.error('Error:', error);
            submitBtn.classList.remove('sending');

            // Show error message
            const errorMessage = document.createElement('div');
            errorMessage.className = 'flash-message flash-error';
            errorMessage.textContent = 'אירעה שגיאה בשליחת ההודעה. אנא נסה שוב.';
            form.parentElement.insertBefore(errorMessage, form);
        }
    });

    function validateForm() {
        let isValid = true;
        const requiredInputs = form.querySelectorAll('[required]');

        requiredInputs.forEach(input => {
            if (!input.value.trim()) {
                isValid = false;
                highlightError(input);
            } else {
                removeError(input);
            }

            // Email validation
            if (input.type === 'email' && input.value) {
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                if (!emailRegex.test(input.value)) {
                    isValid = false;
                    highlightError(input, 'אנא הזן כתובת אימייל תקינה');
                }
            }
        });

        return isValid;
    }

    function highlightError(input, message = 'שדה זה הינו חובה') {
        input.classList.add('error');

        // Add or update error message
        let errorDiv = input.parentElement.querySelector('.error-message');
        if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.className = 'error-message';
            input.parentElement.appendChild(errorDiv);
        }
        errorDiv.textContent = message;
    }

    function removeError(input) {
        input.classList.remove('error');
        const errorDiv = input.parentElement.querySelector('.error-message');
        if (errorDiv) {
            errorDiv.remove();
        }
    }
});