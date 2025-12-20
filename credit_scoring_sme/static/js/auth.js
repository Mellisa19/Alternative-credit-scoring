document.addEventListener('DOMContentLoaded', () => {
    const togglePasswordButtons = document.querySelectorAll('.toggle-password');

    togglePasswordButtons.forEach(btn => {
        btn.addEventListener('click', function () {
            const input = this.closest('.slider-group').querySelector('input');
            const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
            input.setAttribute('type', type);

            // Toggle eye icon
            const eyePath = 'M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z';
            const eyeOpenPath = 'M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z';
            const circlePath = 'M12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6z';
            const slashPath = 'M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24';

            if (type === 'text') {
                this.innerHTML = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="${eyeOpenPath}"></path><path d="${circlePath}"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>`;
            } else {
                this.innerHTML = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="${eyeOpenPath}"></path><path d="${circlePath}"></path></svg>`;
            }
        });
    });
});
