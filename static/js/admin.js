/* Admin Dashboard Helpers & Overlap Validators */
document.addEventListener('DOMContentLoaded', () => {
    // Showtime overlap helper check
    const showtimeForm = document.getElementById('addShowtimeForm');
    if (showtimeForm) {
        showtimeForm.addEventListener('submit', (e) => {
            const start = document.getElementById('startTimeInput').value;
            const end = document.getElementById('endTimeInput').value;

            if (start && end && start >= end) {
                e.preventDefault();
                alert("End time must be after start time.");
            }
        });
    }
});
