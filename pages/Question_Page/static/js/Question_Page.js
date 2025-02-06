//Question_Page.js
let currentQuestionId = null;
let inactivityTimer = null;
let lastActivityTime = Date.now();
let triangleChart = null;
let questionAnswerCount = 0;
let tooltipTimer = null;
let highRelevanceModal = null;
let currentHighRelevanceTheorems = new Set();
let isDeliberateExit = false;



console.log('Script starting...');
console.log('Question_Page.js loaded successfully');

const TRIANGLE_TYPES = {
    0: {
        name: 'משולש כללי',
        class: 'triangle-general'
    },
    1: {
        name: 'משולש שווה צלעות',
        class: 'triangle-equilateral'
    },
    2: {
        name: 'משולש שווה שוקיים',
        class: 'triangle-isosceles'
    },
    3: {
        name: 'משולש ישר זווית',
        class: 'triangle-right'
    }
};

function updateTheoremsModal(theorems) {
    console.log('Updating theorems modal with:', theorems);
    const theoremList = document.querySelector('.theorem-list');
    let highRelevanceTheorems = [];

    if (theoremList && theorems && theorems.length > 0) {
        let theoremsHTML = '';
        theorems.forEach(theorem => {
            // Handle both array and object formats
            const text = Array.isArray(theorem) ? theorem[1] : theorem.text;
            const weight = Array.isArray(theorem) ? theorem[2] : theorem.weight;
            const category = Array.isArray(theorem) ? theorem[3] : theorem.category;

            // Get triangle type based on category
            const triangleType = TRIANGLE_TYPES[category] || TRIANGLE_TYPES[0];

            // Check for high relevance (90% or higher)
            if (weight >= 0.9) {
                const theoremKey = Array.isArray(theorem) ? theorem[0] : theorem.id;
                if (!currentHighRelevanceTheorems.has(theoremKey)) {
                    highRelevanceTheorems.push({
                        id: theoremKey,
                        text: text
                    });
                    currentHighRelevanceTheorems.add(theoremKey);
                }
            }

            theoremsHTML += `
                <div class="theorem-item">
                    <div class="theorem-text">
                        ${text}
                        <span class="theorem-type ${triangleType.class}">
                            (${triangleType.name})
                        </span>
                    </div>
                    <div class="theorem-weight">רלוונטיות: ${(weight * 100).toFixed(1)}%</div>
                </div>
            `;
        });
        theoremList.innerHTML = theoremsHTML;

        // Show high relevance modal if we have new highly relevant theorems
        if (highRelevanceTheorems.length > 0) {
            showHighRelevanceModal(highRelevanceTheorems);
        }
    } else {
        theoremList.innerHTML = '<div class="theorem-item"><div class="theorem-text">אין משפטים רלוונטיים כרגע</div></div>';
    }
}

function initializeHighRelevanceModal() {
    highRelevanceModal = document.getElementById('highRelevanceModal');

    // Add click event for close button
    const closeBtn = document.querySelector('.close-relevance');
    if (closeBtn) {
        closeBtn.addEventListener('click', hideHighRelevanceModal);
    }
}

function showHighRelevanceModal(theorems) {
    const modal = document.getElementById('highRelevanceModal');
    const theoremsContainer = modal.querySelector('.high-relevance-theorems');

    // Clear previous content
    theoremsContainer.innerHTML = '';

    // Add each theorem
    theorems.forEach(theorem => {
        const theoremDiv = document.createElement('div');
        theoremDiv.className = 'high-relevance-theorem';
        theoremDiv.textContent = theorem.text;
        theoremsContainer.appendChild(theoremDiv);
    });

    // Show the modal with animation
    modal.classList.add('show');
}

function hideHighRelevanceModal() {
    const modal = document.getElementById('highRelevanceModal');
    modal.classList.remove('show');
}

// Debounce function to avoid too frequent resets
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

const debouncedResetTimer = debounce(function() {
    clearTimeout(inactivityTimer);
    inactivityTimer = setTimeout(checkInactivity, 120000); // 2 minutes
}, 1000);

function resetInactivityTimer() {
    console.log('resetInactivityTimer called at:', new Date().toISOString());
    lastActivityTime = Date.now();

    if (inactivityTimer) {
        console.log('Clearing existing timer');
        clearTimeout(inactivityTimer);
    }

    console.log('Setting new timer for 15 minutes');
    inactivityTimer = setTimeout(() => {
        console.log('Timer triggered! Calling checkInactivity');
        checkInactivity();
    }, 900000); // 15 minutes
}

async function checkInactivity() {
    console.log('checkInactivity called at:', new Date().toISOString());
    console.log('Time since last activity:', (Date.now() - lastActivityTime) / 1000, 'seconds');

    try {
        console.log('Sending timeout check request to server');
        const response = await fetch('/question/check-timeout');
        const data = await response.json();
        console.log('Server response:', data);

        if (data.timeout) {
            console.log('Timeout detected, showing modal');
            showTimeoutModal();
        } else {
            console.log('No timeout detected');
            resetInactivityTimer();
        }
    } catch (error) {
        console.error('Error in checkInactivity:', error);
    }
}


document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded at:', new Date().toISOString());

    const questionElement = document.querySelector('.question-text');
    currentQuestionId = questionElement?.dataset.questionId;
    console.log('Initial question ID:', currentQuestionId);

    // Add event listeners for user activity
    ['click', 'keypress', 'mousemove', 'touchstart'].forEach(eventType => {
        document.addEventListener(eventType, () => {
            console.log(`${eventType} detected at:`, new Date().toISOString());
            resetInactivityTimer();
        });
    });

    // Add answer button listeners
    document.querySelectorAll('.answer-btn').forEach(button => {
        console.log('Setting up button:', button.textContent);
        button.addEventListener('click', function() {
            console.log('Button clicked:', this.textContent);
            submitAnswer(this.textContent.trim());
        });
    });

    document.querySelectorAll('.modal').forEach(modal => {
        modal.style.display = 'none';
    });

    console.log('Initializing first inactivity timer');
    resetInactivityTimer();

    initializeDebugInfo();
    switchTab('weights');
    initializeTriangleChart();
    initializeHighRelevanceModal();

});

async function submitAnswer(answer) {
    console.log('submitAnswer called with:', answer);
    if (!currentQuestionId) {
        console.error('No current question ID');
        return;
    }
    try {
        console.log(`Submitting: Q${currentQuestionId} - ${answer}`);
        const response = await fetch('/question/answer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                question_id: parseInt(currentQuestionId),
                answer: answer
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            alert(`Error: ${errorData.error}`);
            return;
        }

        const data = await response.json();
        if (data.success) {
            questionAnswerCount++;

            // Show tooltip every 5 questions
            if (questionAnswerCount % 5 === 0) {
                showTheoremsTooltip();
            }

            updateUI(data);
            resetInactivityTimer();
        } else {
            console.error('Error:', data.error);
        }
    } catch (error) {
        alert(`Failed to submit answer: ${error.message}`);
    }
}

function updateUI(data) {
    // Update question
    if (data.nextQuestion?.id && data.nextQuestion?.text) {
        const questionElement = document.querySelector('.question-text');
        currentQuestionId = data.nextQuestion.id;
        questionElement.textContent = data.nextQuestion.text;
        questionElement.dataset.questionId = data.nextQuestion.id;
    }

    // Update theorems list if available
    if (data.theorems?.length >= 0) {
        updateTheoremsModal(data.theorems);
    }

    // Update debug info for admin
    if (data.debug) {
        updateDebugInfo(data.debug);
    }

    if (data.triangle_weights) {
        updateTriangleChart(data.triangle_weights);
    } else if (data.debug?.triangle_weights) {
        updateTriangleChart(data.debug.triangle_weights);
    }
}

// function updateTheoremsModal(theorems) {
//     console.log('Updating theorems modal with:', theorems);
//     const theoremList = document.querySelector('.theorem-list');
//     if (theoremList && theorems && theorems.length > 0) {
//         let theoremsHTML = '';
//         theorems.forEach(theorem => {
//             // Handle both array and object formats
//             const text = Array.isArray(theorem) ? theorem[1] : theorem.text;
//             const weight = Array.isArray(theorem) ? theorem[2] : theorem.weight;
//
//             theoremsHTML += `
//                 <div class="theorem-item">
//                     <div class="theorem-text">${text}</div>
//                     <div class="theorem-weight">רלוונטיות: ${(weight * 100).toFixed(1)}%</div>
//                 </div>
//             `;
//         });
//         theoremList.innerHTML = theoremsHTML;
//     } else {
//         theoremList.innerHTML = '<div class="theorem-item"><div class="theorem-text">אין משפטים רלוונטיים כרגע</div></div>';
//     }
// }

function switchTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });

    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    document.getElementById(tabName + 'Tab').classList.add('active');
    document.querySelector(`[onclick="switchTab('${tabName}')"]`).classList.add('active');
}

function updateDebugInfo(debug) {
    if (!debug) return;

    // Update triangle weights table
    const triangleWeightsRow = document.querySelector('.triangle-weights-values');
    if (triangleWeightsRow) {
        triangleWeightsRow.innerHTML = '';
        for (let i = 0; i < 4; i++) {
            const weight = debug.triangle_weights[i] || 0;
            const td = document.createElement('td');
            td.textContent = `${(weight * 100).toFixed(1)}%`;
            triangleWeightsRow.appendChild(td);
        }
    }

    // Update theorem weights
    const theoremWeightsDiv = document.querySelector('.theorem-weights');
    if (theoremWeightsDiv) {
        let weightsHTML = '';
        const sortedTheorems = Object.entries(debug.theorem_weights)
            .sort((a, b) => b[1] - a[1]); // Sort by weight, descending

        for (const [theoremId, weight] of sortedTheorems) {
            const theoremText = debug.theorem_texts?.[theoremId] || '';
            weightsHTML += `
                <div class="theorem-weight-item">
                    <div class="theorem-info">
                        <span>משפט ${theoremId} - ${theoremText}</span>
                    </div>
                    <div class="theorem-weight">
                        <span>${(weight * 100).toFixed(1)}%</span>
                    </div>
                </div>`;
        }
        theoremWeightsDiv.innerHTML = weightsHTML;
    }

    // Update question scores
    const questionScoresDiv = document.querySelector('.question-scores');
    if (questionScoresDiv && debug.question_scores) {
        let scoresHTML = '';
        const sortedScores = Object.entries(debug.question_scores)
            .sort((a, b) => b[1] - a[1]); // Sort by score, descending

        for (const [questionId, score] of sortedScores) {
            const questionText = debug.question_texts?.[questionId] || '';
            scoresHTML += `
                <div class="question-score-item">
                    <div class="question-info">
                        <span>שאלה ${questionId} - ${questionText}</span>
                    </div>
                    <div class="question-score">
                        <span>${score.toFixed(3)}</span>
                    </div>
                </div>`;
        }
        questionScoresDiv.innerHTML = scoresHTML || '<p>אין ציוני שאלות זמינים</p>';
    }

    // Update calculations
    const calculationsDiv = document.querySelector('.current-calculations');
    if (calculationsDiv && debug.calculations) {
        let calcHTML = `<h4>מצב נוכחי:</h4>
        <pre>אנטרופיה נוכחית: ${debug.calculations.current_entropy.toFixed(4)}</pre>`;

        if (debug.calculations.info_gain_details.length > 0) {
            calcHTML += `
                <h4>חישובי Information Gain:</h4>
                <pre>${debug.calculations.info_gain_details.join('\n')}</pre>
                
                <h4>ציוני שאלות:</h4>
                <pre>${debug.calculations.final_scores}</pre>`;
        }

        calculationsDiv.innerHTML = calcHTML;
    } else if (calculationsDiv) {
        calculationsDiv.innerHTML = '<p>אין חישובים זמינים</p>';
    }
}

function initializeDebugInfo() {
    const initialTheoremsData = JSON.parse(
        document.getElementById('initial-theorems-data')?.textContent || '[]'
    );

    const defaultWeights = {
        triangle_weights: {0: 0.25, 1: 0.25, 2: 0.25, 3: 0.25},
        theorem_weights: {},
        theorem_texts: {},
        question_scores: {},
        calculations: {
            current_entropy: 2,
            info_gain_details: [],
            final_scores: ''
        }
    };

    initialTheoremsData.forEach(theorem => {
        const [id, text] = theorem;
        defaultWeights.theorem_weights[id] = 0.01;
        defaultWeights.theorem_texts[id] = text;
    });

    updateDebugInfo(defaultWeights);
}

function confirmFinish() {
    const modal = document.getElementById('finishModal');
    modal.style.display = 'block';
}

// Close modal when clicking outside of it
window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.style.display = 'none';
    }
}

function logout() {
    fetch('/question/cleanup', {
        method: 'POST',
    }).then(() => {
        window.location.href = '/logout';
    });
}


function showTimeoutModal() {
    const modal = document.getElementById('timeoutModal');
    modal.classList.add('show');
    // Force reflow to trigger animation
    modal.offsetHeight;
}

function hideTimeoutModal() {
    const modal = document.getElementById('timeoutModal');
    modal.classList.remove('show');
}

function continueSession() {
    console.log('User chose to continue');
    hideTimeoutModal();
    resetInactivityTimer();
}

function initializeTriangleChart() {
    const ctx = document.getElementById('triangleWeightsChart').getContext('2d');

    triangleChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['משולש כללי', 'משולש שווה צלעות', 'משולש שווה שוקיים', 'משולש ישר זווית'],
            datasets: [{
                data: [0.25, 0.25, 0.25, 0.25],
                backgroundColor: ['#559B92', '#A59C95', '#B8508D', '#565A9B'],
                borderColor: ['#559B92', '#A59C95', '#B8508D', '#565A9B'],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            layout: {
                padding: {
                    top: 20,
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    enabled: false
                },
                datalabels: {
                    color: '#636363',
                    anchor: 'end',
                    align: 'top',
                    offset: 0,
                    font: {
                        weight: 'bold',
                        size: 14
                    },
                    formatter: function(value) {
                        return (value * 100).toFixed(1) + '%';
                    },
                    clamp: true,
                    clip: false,
                    textAlign: 'center'
                }
            },
            scales: {
                y: {
                    display: false,
                    beginAtZero: true,
                    max: 1.1
                },
                x: {
                    ticks: {
                        font: {
                            size: 12,
                            weight: 'bold'
                        },
                        autoSkip: false,
                        maxRotation: 0,
                        minRotation: 0,
                        padding: 10,
                        callback: function (value) {
                            const label = this.getLabelForValue(value);
                            const words = label.split(' ');
                            return words;
                        }
                    }
                }
            },
            barThickness: 40
        }
    });
}

function updateTriangleChart(weights) {
    if (!triangleChart) return;

    triangleChart.data.datasets[0].data = [
        weights[0] || 0,
        weights[1] || 0,
        weights[2] || 0,
        weights[3] || 0
    ];
    triangleChart.update();
}

function showTheoremsTooltip() {
    const tooltip = document.getElementById('theoremTooltip');
    tooltip.classList.remove('hidden');
    tooltip.classList.add('visible');

    // Hide after 1 minute
    if (tooltipTimer) {
        clearTimeout(tooltipTimer);
    }
    tooltipTimer = setTimeout(() => {
        hideTheoremsTooltip();
    }, 60000); // 60 seconds
}

function hideTheoremsTooltip() {
    const tooltip = document.getElementById('theoremTooltip');
    tooltip.classList.remove('visible');
    tooltip.classList.add('hidden');
    if (tooltipTimer) {
        clearTimeout(tooltipTimer);
        tooltipTimer = null;
    }
}

function toggleTheorems() {
    const modal = document.getElementById('theoremsModal');
    modal.style.display = modal.style.display === 'none' ? 'block' : 'none';
    hideTheoremsTooltip(); // Hide tooltip when theorems are viewed
}

function hideFinishModal() {
    const modal = document.getElementById('finishModal');
    modal.style.display = 'none';
}

window.onbeforeunload = function(e) {
    // If it's a deliberate exit (user clicked סיום and chose an option), don't show popup
    if (isDeliberateExit) {
        return undefined; // This prevents the popup
    }

    // Otherwise, for unintentional exits (like closing tab), send data and show popup
    const data = {
        session_type: 'interrupted',
        timestamp: new Date().toISOString(),
        last_question_id: currentQuestionId,
        question_count: questionAnswerCount
    };

    navigator.sendBeacon('/api/end-session', JSON.stringify(data));

    e.preventDefault();
    e.returnValue = 'האם אתה בטוח שברצונך לעזוב את הדף?';
    return e.returnValue;
};

// Modify your finishSession function
async function finishSession(status) {
    try {
        const modal = document.getElementById('finishModal');
        modal.style.display = 'none';

        // Set flag for deliberate exit
        isDeliberateExit = true;

        const response = await fetch('/question/finish', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                status: status
            }),
            credentials: 'include'
        });

        const data = await response.json();

        if (data.success) {
            // If the user wants to try a new exercise
            if (status === 'partial') {
                window.location.href = '/question/';
            } else {
                window.location.href = data.redirect;
            }
        } else {
            throw new Error(data.error || 'Failed to finish session');
        }
    } catch (error) {
        console.error('Error during session finish:', error);
        alert('אירעה שגיאה בסיום המפגש. אנא נסה שוב.');
    }
}

function toggleDebug() {
    const modal = document.getElementById('debugModal');
    if (modal) {
        modal.style.display = modal.style.display === 'none' ? 'block' : 'none';
    }
}