document.addEventListener('DOMContentLoaded', function () {
  const dateInput = document.getElementById('date');
  const timeInput = document.getElementById('checkin-time');

  const currentDate = new Date().toISOString().split('T')[0];
  dateInput.setAttribute('min', currentDate);

  flatpickr(timeInput, {
    enableTime: true,
    noCalendar: true,
    dateFormat: "H:i",
    time_24hr: true,
    minuteIncrement: 5,
    minTime: "06:00",
    maxTime: "21:00"
  });

  document.getElementById('booking-form').addEventListener('submit', function (event) {
    const selectedDate = dateInput.value;
    const selectedTime = timeInput.value;

    if (!selectedDate || !selectedTime) return;

    const selectedDatetime = new Date(`${selectedDate}T${selectedTime}`);
    const now = new Date();

    if (selectedDatetime < now) {
      event.preventDefault();
      alert("❌ The selected date and time must be in the future.");
    }
  });

  const img = document.getElementById('scooter-zoom');
  const zoomResult = document.getElementById('zoom-result');

  img.addEventListener('mousemove', function(e) {
    const rect = img.getBoundingClientRect();
    const x = e.pageX - window.scrollX - rect.left;
    const y = e.pageY - window.scrollY - rect.top;

    const xPercent = (x / rect.width) * 100;
    const yPercent = (y / rect.height) * 100;

    zoomResult.style.display = "block";
    zoomResult.style.left = `${e.pageX + 20}px`;
    zoomResult.style.top = `${e.pageY - 75}px`;
    zoomResult.style.backgroundImage = `url('${img.src}')`;
    zoomResult.style.backgroundPosition = `${xPercent}% ${yPercent}%`;
  });

  img.addEventListener('mouseleave', function() {
    zoomResult.style.display = "none";
  });
});
