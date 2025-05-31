let topupRecords = [];
const rowsPerPage = 10;
let currentPage = 1;

// Fetch all top-up records on page load
function fetchTopUpHistory() {
  fetch("/admin/topups/api")
    .then(response => response.json())
    .then(data => {
      topupRecords = Array.isArray(data) ? data : [];
      renderTopupTable();
    })
    .catch(err => {
      console.error("❌ Failed to load top-up history:", err);
    });
}

// Render top-up records with pagination
function renderTopupTable() {
  const tbody = document.getElementById("topup-body");
  const pageInfo = document.getElementById("page-info");
  const prevBtn = document.getElementById("prev-page");
  const nextBtn = document.getElementById("next-page");

  tbody.innerHTML = "";

  const sorted = topupRecords.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
  const start = (currentPage - 1) * rowsPerPage;
  const paginated = sorted.slice(start, start + rowsPerPage);

  paginated.forEach(record => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${record.id}</td>
      <td>${record.username || "Unknown User"}</td>
      <td>$${parseFloat(record.amount).toFixed(2)}</td>
      <td>${formatDate(record.timestamp)}</td>
      <td><button class="btn-info" onclick="viewUser(${record.user_id})">👤 View</button></td>
    `;
    tbody.appendChild(row);
  });

  const totalPages = Math.max(1, Math.ceil(topupRecords.length / rowsPerPage));
  pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
  prevBtn.disabled = currentPage === 1;
  nextBtn.disabled = currentPage === totalPages;
}

// Format timestamp into readable date
function formatDate(dateStr) {
  const d = new Date(dateStr);
  return isNaN(d) ? "-" : d.toLocaleString();
}

// View user profile modal
function viewUser(userId) {
  fetch(`/admin/users/api/${userId}`)
    .then(res => res.json())
    .then(user => {
      if (user && !user.error) {
        const fullName = [user.first_name, user.last_name].filter(Boolean).join(" ") || "N/A";

        const container = document.getElementById("user-details");
        container.innerHTML = `
          <div class="profile-header">
            <div class="profile-avatar">👤</div>
            <h3>${user.username}</h3>
            <p class="text-secondary">${fullName}</p>
          </div>
          <div class="profile-fields">
            <p><strong>Email:</strong> ${user.email || "N/A"}</p>
            <p><strong>Phone:</strong> ${user.phone_number || "Not provided"}</p>
            <p><strong>Balance:</strong> $${user.balance ?? "0"}</p>
            <p><strong>Created At:</strong> ${formatDate(user.created_at)}</p>
          </div>
        `;

        document.getElementById("user-modal").classList.remove("hidden");
      } else {
        alert("User not found.");
      }
    })
    .catch(err => {
      console.error("❌ Failed to load user info:", err);
      alert("Unable to load user profile.");
    });
}

// Close modal
function closeModal() {
  document.getElementById("user-modal").classList.add("hidden");
}

// Pagination buttons
document.getElementById("prev-page").onclick = () => {
  if (currentPage > 1) {
    currentPage--;
    renderTopupTable();
  }
};

document.getElementById("next-page").onclick = () => {
  const totalPages = Math.ceil(topupRecords.length / rowsPerPage);
  if (currentPage < totalPages) {
    currentPage++;
    renderTopupTable();
  }
};

// Close modal on outside click
window.onclick = e => {
  const modal = document.getElementById("user-modal");
  if (e.target === modal) {
    closeModal();
  }
};

// Initial load
window.onload = fetchTopUpHistory;
