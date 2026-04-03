// main.js — students will add JavaScript here as features are built

// ------------------------------------------------------------------ //
// Video Modal                                                         //
// ------------------------------------------------------------------ //

(function () {
    const openBtn    = document.getElementById('openModal');
    const modal      = document.getElementById('videoModal');
    const closeBtn   = document.getElementById('modalClose');
    const iframe     = document.getElementById('videoFrame');

    // Guard — only run if modal exists on this page
    if (!openBtn || !modal || !iframe) return;

    function openModal() {
        // Load the video src only when modal opens (prevents autoload)
        iframe.src = iframe.dataset.src;
        modal.classList.add('active');
        document.body.style.overflow = 'hidden'; // prevent background scroll
    }

    function closeModal() {
        // Wipe src completely — this stops the video immediately
        iframe.src = '';
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }

    openBtn.addEventListener('click', openModal);
    closeBtn.addEventListener('click', closeModal);

    // Click outside the modal box to close
    modal.addEventListener('click', function (e) {
        if (e.target === modal) closeModal();
    });

    // Press Escape to close
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && modal.classList.contains('active')) {
            closeModal();
        }
    });
})();