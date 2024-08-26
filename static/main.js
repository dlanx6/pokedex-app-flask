document.addEventListener('DOMContentLoaded', () => {
    // Timeout for flash messages
    setTimeout(() => {
        document.querySelector('.flash-message').style.display = 'none';
    }, 3000);

    // Pokemon types
    const types = document.querySelectorAll('.pokemon-type');

    // Add colors based on the Pokemon types
    types.forEach(type => {
        let text = type.textContent.toLowerCase();
        type.classList.add(text);
    });
});