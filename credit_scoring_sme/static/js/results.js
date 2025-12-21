// Results Animation Logic
document.addEventListener('DOMContentLoaded', () => {
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
});

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
