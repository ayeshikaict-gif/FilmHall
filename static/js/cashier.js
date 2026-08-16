/* Cashier POS Real-Time Seat Sync & Walk-In Desk Logic */
document.addEventListener('DOMContentLoaded', () => {
    const posSeatGrid = document.getElementById('posSeatGrid');
    if (!posSeatGrid) return;

    const showtimeId = document.getElementById('posShowtimeId').value;
    let selectedSeatIds = [];
    let selectedSeatNumbers = [];

    // Live seat polling every 3 seconds
    setInterval(() => {
        fetch(`/api/showtimes/${showtimeId}/seats`)
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    syncSeatMap(data.seats);
                }
            })
            .catch(err => console.error("POS Seat Poll Error:", err));
    }, 3000);

    function syncSeatMap(seats) {
        seats.forEach(s => {
            const btn = document.querySelector(`.seat-btn[data-seat-id="${s.seat_id}"]`);
            if (btn && !btn.classList.contains('selected')) {
                if (s.status === 'BOOKED') {
                    btn.className = 'seat-btn booked';
                } else if (s.status === 'HELD') {
                    btn.className = 'seat-btn held';
                } else if (s.status === 'AVAILABLE') {
                    btn.className = s.seat_type_name === 'VIP' ? 'seat-btn seat-vip' : 'seat-btn';
                }
            }
        });
    }

    posSeatGrid.addEventListener('click', (e) => {
        const btn = e.target.closest('.seat-btn');
        if (!btn || btn.classList.contains('booked') || btn.classList.contains('held')) return;

        const seatId = parseInt(btn.dataset.seatId);
        const seatNum = btn.dataset.seatNum;

        if (btn.classList.contains('selected')) {
            btn.classList.remove('selected');
            selectedSeatIds = selectedSeatIds.filter(id => id !== seatId);
            selectedSeatNumbers = selectedSeatNumbers.filter(n => n !== seatNum);
        } else {
            btn.classList.add('selected');
            selectedSeatIds.push(seatId);
            selectedSeatNumbers.push(seatNum);
        }

        updatePosSummary();
    });

    function updatePosSummary() {
        const summaryText = document.getElementById('posSelectedSeatsText');
        const countText = document.getElementById('posTicketCountText');
        const totalText = document.getElementById('posTotalAmountText');
        const confirmBtn = document.getElementById('posConfirmBtn');

        if (selectedSeatIds.length === 0) {
            summaryText.innerText = 'None';
            countText.innerText = '0';
            totalText.innerText = 'Rs. 0.00';
            confirmBtn.disabled = true;
            return;
        }

        let total = 0;
        document.querySelectorAll('.seat-btn.selected').forEach(btn => {
            total += parseFloat(btn.dataset.price);
        });

        summaryText.innerText = selectedSeatNumbers.join(', ');
        countText.innerText = selectedSeatIds.length;
        totalText.innerText = `Rs. ${total.toLocaleString('en-US', {minimumFractionDigits: 2})}`;
        confirmBtn.disabled = false;
    }

    const posForm = document.getElementById('posBookingForm');
    if (posForm) {
        posForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const confirmBtn = document.getElementById('posConfirmBtn');
            const customerName = document.getElementById('posCustomerName').value || 'Walk-in Customer';
            const customerPhone = document.getElementById('posCustomerPhone').value || '+94700000000';
            const paymentMethod = document.getElementById('posPaymentMethod').value;

            if (!selectedSeatIds || selectedSeatIds.length === 0) {
                alert("Please click and select at least one available seat from the grid before confirming.");
                return;
            }

            confirmBtn.disabled = true;
            confirmBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Processing & Printing...';

            fetch('/api/cashier/process-booking', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    showtime_id: parseInt(showtimeId),
                    seat_ids: selectedSeatIds,
                    customer_name: customerName,
                    customer_phone: customerPhone,
                    payment_method: paymentMethod
                })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    window.location.href = data.redirect_url;
                } else {
                    alert("POS Booking Failed: " + data.message);
                    confirmBtn.disabled = false;
                    confirmBtn.innerHTML = '<i class="fa-solid fa-check"></i> Confirm POS Booking & Print';
                }
            })
            .catch(err => {
                alert("POS System Error: " + err);
                confirmBtn.disabled = false;
                confirmBtn.innerHTML = '<i class="fa-solid fa-check"></i> Confirm POS Booking & Print';
            });
        });
    }
});
