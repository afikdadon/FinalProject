document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('feedbackForm');
    const successMessage = document.querySelector('.success-message');
    const errorMessage = document.querySelector('.error-message');
    const submitButton = form.querySelector('.submit-btn');

    if (!form) {
        console.error('Feedback form not found');
        return;
    }

    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        try {
            // Hide previous messages if they exist
            if (successMessage) successMessage.style.display = 'none';
            if (errorMessage) errorMessage.style.display = 'none';

            // Show loading state
            if (submitButton) {
                submitButton.textContent = 'שולח...';
                submitButton.disabled = true;
                submitButton.classList.add('loading');
            }

            // Collect form data
            const formData = {
                // Usability questions
                usability_easy_to_use: getRadioValue('usability_easy_to_use'),
                usability_clear_questions: getRadioValue('usability_clear_questions'),
                usability_clear_interface: getRadioValue('usability_clear_interface'),
                usability_easy_navigation: getRadioValue('usability_easy_navigation'),

                // Educational value
                educational_concepts: getRadioValue('educational_concepts'),
                educational_theorems: getRadioValue('educational_theorems'),
                educational_guidance: getRadioValue('educational_guidance'),
                educational_learning: getRadioValue('educational_learning'),

                // Format questions
                format_dont_know_helpful: getRadioValue('format_dont_know_helpful'),
                format_sufficient_options: getRadioValue('format_sufficient_options'),
                format_would_use_again: getRadioValue('format_would_use_again'),

                // System intelligence
                intelligence_understood_responses: getRadioValue('intelligence_understood_responses'),
                intelligence_relevant_questions: getRadioValue('intelligence_relevant_questions'),

                // Open questions
                missing_questions: document.getElementById('missing_questions')?.value.trim() ?? '',
                unclear_questions: document.getElementById('unclear_questions')?.value.trim() ?? '',
                suggested_improvements: document.getElementById('suggested_improvements')?.value.trim() ?? '',
                expected_questions: document.getElementById('expected_questions')?.value.trim() ?? ''
            };

            console.log('Submitting feedback:', formData); // Debug log

            const response = await fetch('/feedback/submit', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData),
                credentials: 'include'
            });

            const result = await response.json();
            console.log('Server response:', result); // Debug log

            if (result.success) {
                form.reset();
                const modal = document.getElementById('thankYouModal');
                modal.style.display = 'flex';

                // Redirect after 3 seconds
                setTimeout(() => {
                    window.location.href = '/';
                }, 3000);
            } else {
                throw new Error(result.error || 'Failed to submit feedback');
            }
        } catch (error) {
            console.error('Submission error:', error);
            console.error('Full error details:', {
                message: error.message,
                response: error.response,
                stack: error.stack
            });

            // Try to extract the most useful error message
            let errorMsg = error.message;
            if (error.response) {
                try {
                    const errorData = await error.response.json();
                    errorMsg = errorData.error || errorMsg;
                } catch (e) {
                    console.error('Could not parse error response:', e);
                }
            }

            // Display error message
            if (!errorMessage) {
                const newErrorMessage = document.createElement('div');
                newErrorMessage.className = 'error-message';
                newErrorMessage.textContent = 'אירעה שגיאה בשליחת המשוב: ' + errorMsg;
                form.parentNode.insertBefore(newErrorMessage, form.nextSibling);
            } else {
                errorMessage.style.display = 'block';
                errorMessage.textContent = 'אירעה שגיאה בשליחת המשוב: ' + errorMsg;
            }
        } finally {
            // Reset button state
            if (submitButton) {
                submitButton.textContent = 'שלח משוב';
                submitButton.disabled = false;
                submitButton.classList.remove('loading');
            }
        }
    });

    // Helper function to get radio button value
    function getRadioValue(name) {
        const radio = document.querySelector(`input[name="${name}"]:checked`);
        return radio ? radio.value : null;
    }

    // Smooth scroll to sections when clicking on validation errors
    document.querySelectorAll('input[required]').forEach(input => {
        input.addEventListener('invalid', function(e) {
            e.preventDefault();
            this.closest('.feedback-section').scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        });
    });
});