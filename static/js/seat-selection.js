/* Interactive Seat Selection Logic */
document.addEventListener('DOMContentLoaded', () => {
    const seatGrid = document.getElementById('seatGrid');
    if (!seatGrid) return;

    let selectedSeatIds = [];
    let selectedSeatNumbers = [];
    let timerInterval = null;

    const selectedSeatsText = document.getElementById('selectedSeatsText');
    const ticketCountText = document.getElementById('ticketCountText');
    const subtotalText = document.getElementById('subtotalText');
    const totalAmountText = document.getElementById('totalAmountText');
    const proceedBtn = document.getElementById('proceedBtn');
    const seatIdsInput = document.getElementById('seatIdsInput');
    const showtimeId = document.getElementById('showtimeId')?.value;
    const timerDisplay = document.getElementById('timerDisplay');

    // Live seat map polling every 3 seconds
    if (showtimeId) {
        setInterval(() => {
            fetch(`/api/showtimes/${showtimeId}/seats`)
                .then(res => res.json())
                .then(data => {
                    if (data.success && data.seats) {
                        syncCustomerSeatMap(data.seats);
                    }
                })
                .catch(err => console.error("Seat Map Poll Error:", err));
        }, 3000);
    }

    function syncCustomerSeatMap(seats) {
        seats.forEach(s => {
            const btn = document.querySelector(`.seat-btn[data-seat-id="${s.seat_id}"]`);
            if (btn && !btn.classList.contains('selected')) {
                if (s.status === 'BOOKED') {
                    btn.className = 'seat-btn booked';
                    btn.disabled = true;
                } else if (s.status === 'HELD') {
                    btn.className = 'seat-btn held';
                    btn.disabled = true;
                } else if (s.status === 'AVAILABLE') {
                    const isVip = btn.classList.contains('seat-vip') || (btn.title && btn.title.includes('VIP'));
                    btn.className = isVip ? 'seat-btn seat-vip' : 'seat-btn';
                    btn.disabled = false;
                }
            }
        });
    }

    seatGrid.addEventListener('click', (e) => {
        const btn = e.target.closest('.seat-btn');
        if (!btn || btn.classList.contains('booked') || btn.classList.contains('held')) return;

        const seatId = parseInt(btn.dataset.seatId);
        const seatNum = btn.dataset.seatNum;
        const price = parseFloat(btn.dataset.price);

        if (btn.classList.contains('selected')) {
            btn.classList.remove('selected');
            selectedSeatIds = selectedSeatIds.filter(id => id !== seatId);
            selectedSeatNumbers = selectedSeatNumbers.filter(num => num !== seatNum);
        } else {
            btn.classList.add('selected');
            selectedSeatIds.push(seatId);
            selectedSeatNumbers.push(seatNum);
        }

        updateSummary();
    });

    function updateSummary() {
        if (selectedSeatIds.length === 0) {
            selectedSeatsText.innerText = 'None';
            ticketCountText.innerText = '0';
            subtotalText.innerText = 'Rs. 0.00';
            totalAmountText.innerText = 'Rs. 0.00';
            proceedBtn.disabled = true;
            if (seatIdsInput) seatIdsInput.value = '';
            stopTimer();
            return;
        }

        let subtotal = 0;
        document.querySelectorAll('.seat-btn.selected').forEach(btn => {
            subtotal += parseFloat(btn.dataset.price);
        });

        const bookingFee = 50.00;
        const total = subtotal + bookingFee;

        selectedSeatsText.innerText = selectedSeatNumbers.join(', ');
        ticketCountText.innerText = selectedSeatIds.length;
        subtotalText.innerText = `Rs. ${subtotal.toLocaleString('en-US', {minimumFractionDigits: 2})}`;
        totalAmountText.innerText = `Rs. ${total.toLocaleString('en-US', {minimumFractionDigits: 2})}`;
        
        if (seatIdsInput) seatIdsInput.value = selectedSeatIds.join(',');
        proceedBtn.disabled = false;

        startHoldTimer();
    }

    function startHoldTimer() {
        if (timerInterval) return;
        let timeLeft = 300; // 5 minutes (300 seconds)

        timerDisplay.style.display = 'block';
        
        timerInterval = setInterval(() => {
            timeLeft--;
            const mins = Math.floor(timeLeft / 60);
            const secs = timeLeft % 60;
            timerDisplay.innerText = `Seats Reserved For: ${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;

            if (timeLeft <= 0) {
                stopTimer();
                alert("Your seat reservation timer expired. Please re-select your seats.");
                location.reload();
            }
        }, 1000);
    }

    function stopTimer() {
        if (timerInterval) {
            clearInterval(timerInterval);
            timerInterval = null;
        }
        if (timerDisplay) timerDisplay.style.display = 'none';
    }
});
