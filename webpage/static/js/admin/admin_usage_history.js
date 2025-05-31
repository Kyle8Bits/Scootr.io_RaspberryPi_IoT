const rawData = document.getElementById("booking-data").textContent;
let bookings = [];

try {
  bookings = JSON.parse(rawData);
} catch (err) {
  console.error("Failed to parse booking data:", err);
}

const usageData = bookings;
const body = document.getElementById("usage-body");
const search = document.getElementById("search-username");
const exportBtn = document.getElementById("export-csv");
const prevBtn = document.getElementById("prev-page");
const nextBtn = document.getElementById("next-page");
const pageInfo = document.getElementById("page-info");

const rowsPerPage = 10;
let currentPage = 1;
let filteredData = [...usageData];
let currentSort = { field: "checkout_time", ascending: false };

// ========== Render Table ==========
function renderTable(data) {
  const start = (currentPage - 1) * rowsPerPage;
  const end = start + rowsPerPage;
  const pageData = data.slice(start, end);

  // Update stat cards
  document.getElementById("total-rides").textContent = data.length;
  const totalRevenue = data.reduce((sum, b) => sum + parseFloat(b.total_price || 0), 0);
  document.getElementById("total-revenue").textContent = `$${totalRevenue.toFixed(2)}`;

  body.innerHTML = "";
  for (let b of pageData) {
    const duration = calculateDuration(b.checkin_time, b.checkout_time);
    const formattedTime = formatDate(b.checkout_time);
    const formattedCost = b.total_price !== undefined ? `$${parseFloat(b.total_price).toFixed(2)}` : "-";
    const statusTag = `<span class="status-tag ${b.status?.toLowerCase() || 'unknown'}">${b.status || "-"}</span>`;

    body.innerHTML += `<tr>
      <td>${b.username || "-"}</td>
      <td>${b.scooter_make || "-"}</td>
      <td>${statusTag}</td>
      <td>${formattedTime}</td>
      <td>${duration}</td>
      <td>${formattedCost}</td>
    </tr>`;
  }

  pageInfo.textContent = `Page ${currentPage} of ${Math.ceil(data.length / rowsPerPage)}`;
  prevBtn.disabled = currentPage === 1;
  nextBtn.disabled = currentPage >= Math.ceil(data.length / rowsPerPage);
}

// ========== Filter Logic ==========
function filterTable() {
  const val = search.value.toLowerCase();

  filteredData = usageData.filter(b =>
    b.username?.toLowerCase().includes(val)
  );

  currentPage = 1;
  sortTable(currentSort.field, currentSort.ascending);
}

// ========== Sorting ==========
function sortTable(field, ascending = true) {
  currentSort = { field, ascending };
  filteredData.sort((a, b) => {
    const valA = a[field] ?? "";
    const valB = b[field] ?? "";
    if (valA < valB) return ascending ? -1 : 1;
    if (valA > valB) return ascending ? 1 : -1;
    return 0;
  });

  renderTable(filteredData);
}

// ========== CSV Export ==========
function exportCSV() {
  if (!filteredData || filteredData.length === 0) {
    alert("No data to export.");
    return;
  }

  const headers = ["Username", "Scooter", "Status", "Time", "Duration", "Cost"];
  const csvRows = [headers.join(",")];

  for (let b of filteredData) {
    csvRows.push([
      b.username || "-",
      b.scooter_make || "-",
      b.status || "-",
      formatDate(b.checkout_time),
      calculateDuration(b.checkin_time, b.checkout_time),
      `$${parseFloat(b.total_price || 0).toFixed(2)}`
    ].map(String).join(","));
  }

  const blob = new Blob([csvRows.join("\n")], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "scooter_usage_history.csv";
  a.click();
  URL.revokeObjectURL(url);
}

// ========== Helpers ==========
function calculateDuration(start, end) {
  const startTime = new Date(start);
  const endTime = new Date(end);
  if (isNaN(startTime) || isNaN(endTime)) return "-";

  const diffMs = endTime - startTime;
  const minutes = Math.floor(diffMs / 60000);
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return `${h}h ${m}m`;
}

function formatDate(str) {
  const d = new Date(str);
  return isNaN(d) ? "-" : d.toLocaleString();
}

// ========== Events ==========
search.addEventListener("input", filterTable);
exportBtn.addEventListener("click", exportCSV);

prevBtn.addEventListener("click", () => {
  if (currentPage > 1) {
    currentPage--;
    renderTable(filteredData);
  }
});

nextBtn.addEventListener("click", () => {
  if (currentPage < Math.ceil(filteredData.length / rowsPerPage)) {
    currentPage++;
    renderTable(filteredData);
  }
});

document.querySelectorAll("th[data-sort]").forEach(th => {
  th.style.cursor = "pointer";
  th.addEventListener("click", () => {
    const field = th.getAttribute("data-sort");
    const isAscending = currentSort.field === field ? !currentSort.ascending : true;
    sortTable(field, isAscending);
  });
});

// Initial render
filterTable();
