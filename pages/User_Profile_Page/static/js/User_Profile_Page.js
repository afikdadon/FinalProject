// Modal handling functions
function showTheorems() {
    const modal = document.getElementById('theoremsModal');
    if (modal) {
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden'; // Prevent background scrolling
    }
}

function closeTheoremsModal() {
    const modal = document.getElementById('theoremsModal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = ''; // Restore scrolling
    }
}

function showQuestions() {
    const modal = document.getElementById('questionsModal');
    if (modal) {
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden';
    }
}

function closeQuestionsModal() {
    const modal = document.getElementById('questionsModal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = '';
    }
}

// Close modals when clicking outside
window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.style.display = 'none';
        document.body.style.overflow = '';
    }
}

// Close modals with Escape key
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        const modals = document.getElementsByClassName('modal');
        for (let modal of modals) {
            if (modal.style.display === 'block') {
                modal.style.display = 'none';
                document.body.style.overflow = '';
            }
        }
    }
});

function filterTheorems(category) {
    const theorems = document.querySelectorAll('.theorem-card');
    theorems.forEach(theorem => {
        if (category === 'all' || theorem.dataset.category === category.toString()) {
            theorem.style.display = 'block';
        } else {
            theorem.style.display = 'none';
        }
    });
}
function showDifficulty(level) {
    const cards = document.querySelectorAll('.question-stat-card');
    const tabs = document.querySelectorAll('.tab-btn');

    tabs.forEach(tab => tab.classList.remove('active'));
    event.target.classList.add('active');

    cards.forEach(card => {
        if (level === 'all' || card.dataset.difficulty === level.toString()) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
}
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('questionSearch');
    const filterBtns = document.querySelectorAll('.filter-btn');
    const questions = document.querySelectorAll('.question-box');

    // Search functionality
    searchInput.addEventListener('input', filterQuestions);

    // Filter buttons
    filterBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            filterBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            filterQuestions();
        });
    });

    function filterQuestions() {
        const searchTerm = searchInput.value.toLowerCase();
        const activeFilter = document.querySelector('.filter-btn.active').dataset.filter;

        questions.forEach(question => {
            const questionText = question.querySelector('.question-text').textContent.toLowerCase();
            const difficulty = question.dataset.difficulty;
            const matchesSearch = questionText.includes(searchTerm);
            const matchesFilter = activeFilter === 'all' || difficulty === activeFilter;

            question.style.display = matchesSearch && matchesFilter ? 'block' : 'none';
        });
    }
});

// Initialize all theorems visible
document.addEventListener('DOMContentLoaded', () => {
    filterTheorems('all');
});


