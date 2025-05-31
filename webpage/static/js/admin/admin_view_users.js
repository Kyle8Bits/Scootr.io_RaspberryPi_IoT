// static/js/admin/admin_view_users.js

document.addEventListener("DOMContentLoaded", () => {
  // Show flash if present
  const adminContent = document.querySelector(".admin-content");
  const flashMsg = sessionStorage.getItem("flash");
  if (flashMsg) {
    adminContent.insertAdjacentHTML(
      "afterbegin",
      `<div class="alert alert-success">${flashMsg}</div>`
    );
    setTimeout(() => {
      const alertEl = adminContent.querySelector(".alert");
      if (alertEl) alertEl.remove();
    }, 3000);
    sessionStorage.removeItem("flash");
  }

  // parse embedded JSON
  const raw = document.getElementById("user-data").textContent;
  let users;
  try {
    users = JSON.parse(raw);
  } catch (e) {
    console.error("Failed to parse user-data JSON", e);
    return;
  }

  // DOM refs
  const tbody         = document.getElementById("user-body");
  const searchInput   = document.getElementById("search-user");
  const filterRole    = document.getElementById("filter-role");
  const exportBtn     = document.getElementById("export-csv");
  const prevBtn       = document.getElementById("prev-page");
  const nextBtn       = document.getElementById("next-page");
  const pageInfo      = document.getElementById("page-info");

  const modal         = document.getElementById("user-modal");
  const closeBtn      = document.getElementById("close-user-modal");
  const modalTitle    = document.getElementById("modal-title");
  const userForm      = document.getElementById("user-form");
  const submitBtn     = userForm.querySelector("button[type=submit]");
  const roleSelect    = document.getElementById("user-role");
  const usernameInput = document.getElementById("user-username");
  const emailInput    = document.getElementById("user-email");
  const pwdInput      = document.getElementById("user-password");
  const pwdWrapper    = document.getElementById("password-wrapper");

  const firstInput    = document.getElementById("user-first");
  const lastInput     = document.getElementById("user-last");
  const phoneInput    = document.getElementById("user-phone");

  const confirmModal  = document.getElementById("confirm-modal");
  const confirmYes    = document.getElementById("confirm-yes");
  const confirmNo     = document.getElementById("confirm-no");

  const btnAddCust    = document.getElementById("btn-add-customer");
  const btnAddEng     = document.getElementById("btn-add-engineer");

  // state
  const rowsPerPage   = 10;
  let currentPage     = 1;
  let filteredData    = [...users];
  let currentSort     = { field: "role", ascending: true };
  let toDeleteId      = null;

  // Render table
  function renderTable() {
    tbody.innerHTML = "";
    const start = (currentPage - 1) * rowsPerPage;
    filteredData.slice(start, start + rowsPerPage).forEach(u => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${u.role||""}</td>
        <td>${u.username||""}</td>
        <td>${u.first_name||""}</td>
        <td>${u.last_name||""}</td>
        <td>${u.email||""}</td>
        <td>${u.phone_number||""}</td>
        <td>${(u.balance||0).toFixed(2)}</td>
        <td>
          <button class="btn-edit"   data-id="${u.id}">✏️</button>
          <button class="btn-delete" data-id="${u.id}">🗑️</button>
        </td>`;
      tbody.appendChild(tr);
    });

    const totalPages = Math.max(1, Math.ceil(filteredData.length / rowsPerPage));
    pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
    prevBtn.disabled = currentPage === 1;
    nextBtn.disabled = currentPage === totalPages;

    attachEditListeners();
    attachDeleteListeners();
  }

  // Apply filters
  function applyFilters() {
    const q = searchInput.value.trim().toLowerCase();
    const r = filterRole.value;
    filteredData = users.filter(u => {
      if (r && u.role !== r) return false;
      return (
        u.username.toLowerCase().includes(q) ||
        u.email.toLowerCase().includes(q) ||
        (u.first_name||"").toLowerCase().includes(q) ||
        (u.last_name||"").toLowerCase().includes(q)
      );
    });
    currentPage = 1;
    renderTable();
  }

  // Export CSV
  function exportCSV() {
    const headers = ["Role","Username","First Name","Last Name","Email","Phone","Balance"];
    const rows = [headers.join(",")];
    filteredData.forEach(u => {
      rows.push([
        u.role, u.username, u.first_name, u.last_name,
        u.email, u.phone_number, (u.balance||0).toFixed(2)
      ].map(v => `"${v||""}"`).join(","));
    });
    const blob = new Blob([rows.join("\n")], { type:"text/csv" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "users.csv";
    a.click();
    URL.revokeObjectURL(a.href);
  }

  // Open modal for add/edit
  function openModal(mode, data = {}) {
    userForm.reset();
    userForm.dataset.mode = mode;
    delete userForm.dataset.id;

    // In BOTH add and edit, show role but keep it disabled
    if (mode === "add") {
      roleSelect.value = data.role || "";
    } else {
      roleSelect.value = data.role || "";
    }
    roleSelect.disabled = true;

    modalTitle.textContent = mode === "add" ? "Add User" : "Edit User";
    submitBtn.textContent  = mode === "add" ? "Save" : "Update";

    if (mode === "add") {
      usernameInput.required = true;
      emailInput.required    = true;
      pwdInput.required      = true;
      pwdWrapper.style.display = "";
    } else {
      usernameInput.required = false;
      emailInput.required    = false;
      pwdInput.required      = false;
      pwdWrapper.style.display = "none";
    }

    if (mode === "edit") {
      userForm.dataset.id     = data.id;
      usernameInput.value     = data.username || "";
      emailInput.value        = data.email || "";
      firstInput.value        = data.first_name || "";
      lastInput.value         = data.last_name || "";
      phoneInput.value        = data.phone_number || "";
    }

    modal.classList.remove("hidden");
  }

  // Edit listeners
  async function attachEditListeners() {
    tbody.querySelectorAll(".btn-edit").forEach(btn => {
      btn.onclick = async () => {
        const res = await fetch(`/admin/users/api/${btn.dataset.id}`);
        if (!res.ok) return alert("Could not load user");
        const data = await res.json();
        openModal("edit", data);
      };
    });
  }

  // Delete listeners
  function attachDeleteListeners() {
    tbody.querySelectorAll(".btn-delete").forEach(btn => {
      btn.onclick = () => {
        toDeleteId = btn.dataset.id;
        confirmModal.classList.remove("hidden");
      };
    });
  }

  // Form submission
  userForm.onsubmit = async e => {
    e.preventDefault();
    if (roleSelect.disabled) roleSelect.disabled = false;

    const mode = userForm.dataset.mode;
    const id   = userForm.dataset.id;
    const url  = mode === "edit"
      ? `/admin/users/edit/${id}`
      : "/admin/users/add";

    const resp = await fetch(url, { method: "POST", body: new FormData(userForm) });
    if (!resp.ok) {
      const txt = await resp.text();
      return alert(`Error ${resp.status}:\n${txt}`);
    }
    let result;
    try {
      result = await resp.json();
    } catch {
      return alert("Invalid JSON response");
    }
    if (result.success) {
      modal.classList.add("hidden");
      const msg = mode === "edit"
        ? "User updated successfully!"
        : "User added successfully!";
      sessionStorage.setItem("flash", msg);
      window.location.reload();
    } else {
      alert("Operation failed: " + (result.error || "unknown error"));
    }
  };

  // Delete confirmation
  confirmYes.onclick = async () => {
    confirmModal.classList.add("hidden");
    if (!toDeleteId) return;
    const resp = await fetch(`/admin/users/delete/${toDeleteId}`, { method: "POST" });
    if (resp.ok) {
      sessionStorage.setItem("flash", "User deleted successfully!");
      window.location.reload();
    } else {
      alert("Delete failed");
    }
  };
  confirmNo.onclick = () => confirmModal.classList.add("hidden");

  // Global listeners
  btnAddCust.onclick = () => openModal("add", { role: "customer" });
  btnAddEng.onclick  = () => openModal("add", { role: "engineer" });
  closeBtn.onclick   = () => modal.classList.add("hidden");
  window.onclick     = e => { if (e.target === modal) modal.classList.add("hidden"); };

  searchInput.oninput = applyFilters;
  filterRole.onchange = applyFilters;
  exportBtn.onclick   = exportCSV;
  prevBtn.onclick     = () => { if (currentPage > 1) { currentPage--; renderTable(); } };
  nextBtn.onclick     = () => {
    const total = Math.ceil(filteredData.length / rowsPerPage);
    if (currentPage < total) { currentPage++; renderTable(); }
  };

  // Sorting
  document.querySelectorAll("th[data-sort]").forEach(th => {
    th.style.cursor = "pointer";
    th.onclick = () => {
      const fld = th.dataset.sort;
      if (currentSort.field === fld) {
        currentSort.ascending = !currentSort.ascending;
      } else {
        currentSort.field     = fld;
        currentSort.ascending = true;
      }
      filteredData.sort((a,b) => {
        if (a[fld] < b[fld]) return currentSort.ascending ? -1 : 1;
        if (a[fld] > b[fld]) return currentSort.ascending ? 1 : -1;
        return 0;
      });
      renderTable();
    };
  });

  // Initial render
  renderTable();
});
