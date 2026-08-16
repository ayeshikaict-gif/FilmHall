/* Ceylon Cineplex Main JavaScript */
document.addEventListener('DOMContentLoaded', () => {
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });

    // Mobile Navbar Toggle
    const navToggle = document.getElementById('navToggle');
    const navWrapper = document.getElementById('navWrapper');

    if (navToggle && navWrapper) {
        navToggle.addEventListener('click', (e) => {
            e.stopPropagation();
            navWrapper.classList.toggle('active');
            const icon = navToggle.querySelector('i');
            if (icon) {
                if (navWrapper.classList.contains('active')) {
                    icon.classList.remove('fa-bars');
                    icon.classList.add('fa-xmark');
                } else {
                    icon.classList.remove('fa-xmark');
                    icon.classList.add('fa-bars');
                }
            }
        });

        // Close navigation menu when clicking outside
        document.addEventListener('click', (e) => {
            if (navWrapper.classList.contains('active') && !navWrapper.contains(e.target) && !navToggle.contains(e.target)) {
                navWrapper.classList.remove('active');
                const icon = navToggle.querySelector('i');
                if (icon) {
                    icon.classList.remove('fa-xmark');
                    icon.classList.add('fa-bars');
                }
            }
        });
    }
});

