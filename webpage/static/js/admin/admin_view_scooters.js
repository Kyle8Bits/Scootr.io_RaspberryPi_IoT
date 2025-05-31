// --- Data & UI handles ---
const scooters     = JSON.parse(document.getElementById("scooter-data").textContent);
const body         = document.getElementById("scooter-body");
const search       = document.getElementById("search-make");
const status       = document.getElementById("filter-status");
const zoneFilter   = document.getElementById("filter-zone");
const exportBtn    = document.getElementById("export-csv");
const prevBtn      = document.getElementById("prev-page");
const nextBtn      = document.getElementById("next-page");
const pageInfo     = document.getElementById("page-info");

// Add/Edit modal elements
const modal        = document.getElementById("scooter-modal");
const btnAdd       = document.getElementById("btn-add-scooter");
const btnClose     = document.getElementById("close-modal");
const scooterForm  = document.getElementById("scooter-form");
const modalTitle   = document.getElementById("modal-title");
const submitBtn    = scooterForm.querySelector("button[type=submit]");

// Delete confirmation modal elements
const confirmModal = document.getElementById("confirm-modal");
const confirmYes   = document.getElementById("confirm-yes");
const confirmNo    = document.getElementById("confirm-no");

let toDeleteId     = null;
const rowsPerPage  = 10;
let currentPage    = 1;
let filteredData   = [...scooters];
let currentSort    = { field: "id", ascending: true };

// --- Flash display (after reload) ---
const flashMsg = sessionStorage.getItem("flash");
if (flashMsg) {
  const alert = document.createElement("div");
  alert.className = "alert alert-success";
  alert.textContent = flashMsg;
  document.body.prepend(alert);
  setTimeout(() => alert.remove(), 3000);
  sessionStorage.removeItem("flash");
}

// ---------- Render Logic ----------
function renderTable(data) {
  const start = (currentPage - 1) * rowsPerPage;
  const end   = start + rowsPerPage;
  const page  = data.slice(start, end);

  body.innerHTML = "";
  page.forEach(s => {
    body.innerHTML += `
      <tr>
        <td>${s.id}</td>
        <td>${s.make}</td>
        <td>${s.color}</td>
        <td><span class="status-tag ${s.status.toLowerCase()}">${s.status}</span></td>
        <td>${s.power_remaining}%</td>
        <td>${s.location}</td>
        <td>
          <button class="btn-edit" data-id="${s.id}">✏️</button>
          <button class="btn-delete" data-id="${s.id}">🗑</button>
        </td>
      </tr>`;
  });

  pageInfo.textContent = `Page ${currentPage} of ${Math.ceil(data.length / rowsPerPage)}`;
  prevBtn.disabled     = currentPage === 1;
  nextBtn.disabled     = currentPage >= Math.ceil(data.length / rowsPerPage);

  attachEditListeners();
  attachDeleteListeners();
}

// ---------- Filtering ----------
function filterTable() {
  const q = search.value.toLowerCase();
  const s = status.value.toLowerCase();
  const z = zoneFilter.value.toLowerCase();

  filteredData = scooters.filter(item =>
    item.make.toLowerCase().includes(q) &&
    (s === "" || item.status.toLowerCase() === s) &&
    (z === "" || item.location.toLowerCase() === z)
  );
  currentPage = 1;
  sortTable(currentSort.field, currentSort.ascending);
}

// ---------- Sorting ----------
function sortTable(field, asc = true) {
  currentSort = { field, ascending: asc };
  filteredData.sort((a, b) => {
    if (a[field] < b[field]) return asc ? -1 : 1;
    if (a[field] > b[field]) return asc ? 1 : -1;
    return 0;
  });
  renderTable(filteredData);
}

// ---------- CSV Export ----------
function exportCSV() {
  const headers = ["ID","Make","Color","Status","Power","Zone"];
  const rows    = [headers.join(",")];

  filteredData.forEach(s => {
    rows.push([s.id, s.make, s.color, s.status, s.power_remaining, s.location]
      .map(String).join(","));
  });

  const blob = new Blob([rows.join("\n")], { type: "text/csv" });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement("a");
  a.href     = url;
  a.download = "scooters.csv";
  a.click();
  URL.revokeObjectURL(url);
}

// ---------- Edit Handlers ----------
function attachEditListeners() {
  document.querySelectorAll(".btn-edit").forEach(btn => {
    btn.addEventListener("click", async () => {
      const id = btn.dataset.id;
      const resp = await fetch(`/admin/scooters/api/${id}`);
      if (!resp.ok) return alert("Failed to load scooter details.");
      const data = await resp.json();

      scooterForm.dataset.mode = "edit";
      scooterForm.dataset.id   = id;
      modalTitle.textContent   = "Edit Scooter";
      submitBtn.textContent    = "Update Scooter";

      document.getElementById("scooter-make").value   = data.make;
      document.getElementById("scooter-color").value  = data.color;
      document.getElementById("scooter-power").value  = data.power_remaining;
      document.getElementById("scooter-cost").value   = data.cost_per_minute;
      document.getElementById("scooter-zone").value   = data.zone_id;
      document.getElementById("scooter-status").value = data.status;

      modal.classList.remove("hidden");
    });
  });
}

// ---------- Delete Handlers ----------
function attachDeleteListeners() {
  document.querySelectorAll(".btn-delete").forEach(btn => {
    btn.addEventListener("click", () => {
      toDeleteId = btn.dataset.id;
      confirmModal.classList.remove("hidden");
    });
  });
}

confirmNo.addEventListener("click", () => {
  toDeleteId = null;
  confirmModal.classList.add("hidden");
});

confirmYes.addEventListener("click", async () => {
  if (!toDeleteId) return;
  confirmModal.classList.add("hidden");

  const resp = await fetch(`/admin/scooters/delete/${toDeleteId}`, { method: "POST" });
  if (resp.ok) {
    const msg = encodeURIComponent("✅ Scooter deleted successfully!");
    window.location.href = `/admin/scooters?message=${msg}`;
  } else {
    alert("Failed to delete scooter.");
  }
});

// ---------- Modal Logic ----------
btnAdd.addEventListener("click", () => {
  scooterForm.reset();
  delete scooterForm.dataset.id;
  scooterForm.dataset.mode = "add";
  modalTitle.textContent   = "Add New Scooter";
  submitBtn.textContent    = "Save Scooter";
  modal.classList.remove("hidden");
});

btnClose.addEventListener("click", () => modal.classList.add("hidden"));
window.addEventListener("click", e => {
  if (e.target === modal) modal.classList.add("hidden");
});

// ---------- AJAX Form Submit ----------
scooterForm.addEventListener("submit", async e => {
  e.preventDefault();
  const mode   = scooterForm.dataset.mode;
  const formId = scooterForm.dataset.id;
  const data   = new FormData(scooterForm);

  let url = mode === "edit" ? `/admin/scooters/edit/${formId}` : "/admin/scooters/add";

  try {
    const resp = await fetch(url, { method: "POST", body: data });
    const result = await resp.json();

    console.log("✅ Response:", result);

    if (resp.ok && result.success) {
      modal.classList.add("hidden");

      const msg = mode === "edit"
        ? "✅ Scooter updated successfully!"
        : "✅ Scooter added successfully!";

      // Option A: Full redirect (default)
      window.location.href = `/admin/scooters?message=${encodeURIComponent(msg)}`;

      // Option B: Use flash message without redirect:
      // sessionStorage.setItem("flash", msg);
      // window.location.reload();

    } else {
      alert("Error: " + (result.error || "Unknown server error"));
    }
  } catch (err) {
    console.error("❌ Submit failed:", err);
    alert("Something went wrong.");
  }
});

// ---------- Filter + Pagination ----------
search.addEventListener("input", filterTable);
status.addEventListener("change", filterTable);
zoneFilter.addEventListener("change", filterTable);
exportBtn.addEventListener("click", exportCSV);

prevBtn.addEventListener("click", () => {
  if (currentPage > 1) {
    currentPage--;
    renderTable(filteredData);
  }
});

nextBtn.addEventListener("click", () => {
  const max = Math.ceil(filteredData.length / rowsPerPage);
  if (currentPage < max) {
    currentPage++;
    renderTable(filteredData);
  }
});

document.querySelectorAll("th[data-sort]").forEach(th => {
  th.style.cursor = "pointer";
  th.addEventListener("click", () => {
    const fld = th.getAttribute("data-sort");
    const asc = (currentSort.field === fld) ? !currentSort.ascending : true;
    sortTable(fld, asc);
  });
});

// Initial load
filterTable();
