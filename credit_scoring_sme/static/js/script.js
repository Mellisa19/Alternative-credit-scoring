document.addEventListener('DOMContentLoaded', () => {
    // --- Phase I: Wizard Logic (Enhanced) ---
    const wizardForm = document.getElementById('wizard-form');
    if (!wizardForm) {
        handleResultsLogic();
        return;
    }

    const steps = Array.from(document.querySelectorAll('.step-card'));
    const progressBar = document.querySelector('.progress-fill');
    const nextButtons = document.querySelectorAll('.btn-next');
    const submitBtn = document.getElementById('submit-btn');
    const loadingScreen = document.getElementById('loading-screen');
    const wizardContent = document.getElementById('wizard-content');
    const journeyIndicator = document.querySelector('.journey-indicator');

    let currentStep = 0;
    let riskFactor = 50; // Neutral start

    const updateJourney = () => {
        if (!journeyIndicator) return;

        // Dynamic color/pos based on simulated risk
        journeyIndicator.style.left = `${riskFactor}%`;
        if (riskFactor > 60) {
            journeyIndicator.style.background = 'var(--emerald)';
        } else if (riskFactor < 40) {
            journeyIndicator.style.background = 'var(--amber)';
        } else {
            journeyIndicator.style.background = 'var(--forest)';
        }
    };

    const calculateSimulatedRisk = () => {
        const rev = parseFloat(document.getElementById('daily_revenue')?.value || 0);
        const exp = parseFloat(document.getElementById('daily_expenses')?.value || 0);
        const ads = parseFloat(document.getElementById('ad_spend')?.value || 0);

        // Simple heuristic for reactive visual feedback
        let score = 50;
        if (rev > 0) score += Math.min(20, (rev / 5000) * 10);
        if (exp > 0) score -= Math.min(20, (exp / rev) * 15 || 0);
        if (ads > 0) score += 5; // Direct investment signal

        riskFactor = Math.max(10, Math.min(90, score));
        updateJourney();
    };

    // Listen for input changes to drive the journey meter
    document.querySelectorAll('.input-field').forEach(input => {
        input.addEventListener('input', calculateSimulatedRisk);
    });

    const updateProgress = () => {
        const percent = ((currentStep) / (steps.length - 1)) * 100;
        progressBar.style.width = `${percent}%`;
    };

    const showStep = (index) => {
        steps.forEach((step, i) => {
            step.classList.toggle('active', i === index);
        });
        updateProgress();
        const firstInput = steps[index].querySelector('input');
        if (firstInput) firstInput.focus();
    };

    nextButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            if (validateStep(currentStep)) {
                currentStep++;
                showStep(currentStep);
            }
        });
    });

    const validateStep = (index) => {
        const step = steps[index];
        if (!step) return true;
        const input = step.querySelector('input, select');
        if (!input || !input.checkValidity()) {
            if (input) input.reportValidity();
            return false;
        }
        return true;
    };

    const handleSubmit = () => {
        // Find whichever submit button is currently visible/active
        wizardContent.style.opacity = '0';
        setTimeout(() => {
            wizardContent.style.display = 'none';
            loadingScreen.style.display = 'block';
            setTimeout(() => { wizardForm.submit(); }, 2800);
        }, 400);
    };

    // Global listener for submit buttons inside the wizard
    wizardForm.addEventListener('click', (e) => {
        if (e.target && e.target.id === 'submit-btn') {
            if (validateStep(currentStep)) {
                handleSubmit();
            }
        }
    });

    showStep(0);
});

// --- Phase II: Results & "What-If" Logic ---
function handleResultsLogic() {
    const scoreValue = document.getElementById('score-value');
    if (!scoreValue) return;

    // 1. Animated Reveal
    const targetScore = parseInt(scoreValue.getAttribute('data-target'));
    animateScore(scoreValue, targetScore);
    initProgressCircle(targetScore);

    // 2. Progressive Text Reveal
    revealInsights();

    // 3. What-If Simulator
    initSimulator(targetScore);
}

function animateScore(el, target) {
    let current = 0;
    const duration = 2000;
    const start = performance.now();

    const frame = (time) => {
        const progress = Math.min((time - start) / duration, 1);
        const ease = 1 - Math.pow(1 - progress, 4); // Quartic ease out
        current = Math.floor(ease * target);
        el.textContent = current;
        if (progress < 1) requestAnimationFrame(frame);
    };
    requestAnimationFrame(frame);
}

function initProgressCircle(score) {
    const circle = document.querySelector('.score-circle-svg circle.progress');
    if (!circle) return;
    const radius = circle.r.baseVal.value;
    const circumference = 2 * Math.PI * radius;
    circle.style.strokeDasharray = `${circumference} ${circumference}`;
    circle.style.strokeDashoffset = circumference;

    setTimeout(() => {
        const offset = circumference - (score / 100) * circumference;
        circle.style.strokeDashoffset = offset;
    }, 100);
}

function revealInsights() {
    const insights = document.querySelectorAll('.typewriter');
    insights.forEach((el, i) => {
        setTimeout(() => {
            el.classList.add('revealed');
        }, 1500 + (i * 400));
    });
}

function initSimulator(baseScore) {
    const adSlider = document.getElementById('sim-ad-spend');
    const simScoreVal = document.getElementById('sim-score-value');
    const simImpact = document.getElementById('sim-impact');

    if (!adSlider) return;

    const baseAd = parseFloat(adSlider.value);

    adSlider.addEventListener('input', (e) => {
        const newVal = parseFloat(e.target.value);
        const diff = (newVal - baseAd) / 100; // Normalized change

        // Simulated heuristic: Increasing ad spend improves ROI signal slightly
        let multiplier = diff > 0 ? 15 : 25; // Penalty for cutting spend is higher
        let newScore = baseScore + (diff * multiplier);
        newScore = Math.max(0, Math.min(100, Math.round(newScore)));

        simScoreVal.textContent = newScore;

        // Dynamic impact tag
        if (newScore > baseScore) {
            simImpact.textContent = `+${newScore - baseScore} point potential`;
            simImpact.style.color = 'var(--emerald)';
        } else if (newScore < baseScore) {
            simImpact.textContent = `${newScore - baseScore} risk shift`;
            simImpact.style.color = '#ef4444';
        } else {
            simImpact.textContent = 'Stable';
            simImpact.style.color = 'white';
        }
    });
}
