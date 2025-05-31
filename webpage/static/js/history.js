const statusFilter = document.getElementById('filter-status');
  const sortSelect = document.getElementById('sort-order');
  const cards = document.querySelectorAll('.history-card');
  const list = document.getElementById('history-list');

  function filterAndSort() {
    const filterValue = statusFilter.value;
    const sortValue = sortSelect.value;

    const cardArray = Array.from(cards);

    cardArray.forEach(card => {
      const matches = filterValue === 'all' || card.dataset.status === filterValue;
      card.style.display = matches ? 'block' : 'none';
    });

    const sorted = cardArray.sort((a, b) => {
      const aDate = new Date(a.dataset.date);
      const bDate = new Date(b.dataset.date);
      return sortValue === 'asc' ? aDate - bDate : bDate - aDate;
    });

    sorted.forEach(card => list.appendChild(card));
  }

  statusFilter.addEventListener('change', filterAndSort);
  sortSelect.addEventListener('change', filterAndSort);

  function toggleShareCard(id) {
    const card = document.getElementById(`share-card-${id}`);
    if (card.style.display === "none") {
      card.style.display = "block";
    } else {
      card.style.display = "none";
    }
  }