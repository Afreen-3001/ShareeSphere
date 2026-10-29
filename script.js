/* ============================================================
   ShareSphere — Front-end interactivity
   ============================================================ */

document.addEventListener("DOMContentLoaded", () => {

  /* ---------- 1. REGISTER: show NGO fields only for NGOs ---------- */
  const roleSelect = document.getElementById("roleSelect");
  const ngoFields  = document.getElementById("ngoFields");
  if (roleSelect && ngoFields) {
    const toggle = () => {
      ngoFields.style.display = roleSelect.value === "ngo" ? "block" : "none";
    };
    roleSelect.addEventListener("change", toggle);
    toggle(); // run once on load
  }

  /* ---------- 2. NGO PAGE: live search filter ---------- */
  const searchBox = document.getElementById("searchBox");
  if (searchBox) {
    searchBox.addEventListener("input", () => {
      const q = searchBox.value.toLowerCase().trim();
      document.querySelectorAll(".ngo-card").forEach(card => {
        const match =
          card.dataset.name.includes(q) ||
          card.dataset.cause.includes(q);
        card.style.display = match ? "" : "none";
      });
    });
  }

  /* ---------- 3. DONATE FORM: AJAX submit ---------- */
  const donateForm = document.getElementById("donateForm");
  if (donateForm) {
    donateForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const ngoId  = donateForm.dataset.ngo;
      const detail = document.getElementById("detail").value.trim();
      const dtype  = document.getElementById("dtype").value;
      const msg    = document.getElementById("donateMsg");

      if (!detail) {
        msg.textContent = "Please enter donation details.";
        msg.className = "msg err";
        return;
      }

      const fd = new FormData();
      fd.append("dtype", dtype);
      fd.append("detail", detail);

      try {
        const res  = await fetch(`/donate/${ngoId}`, { method: "POST", body: fd });
        const data = await res.json();

        if (data.ok) {
          msg.textContent = data.message;
          msg.className = "msg ok";
          donateForm.reset();
        } else {
          msg.textContent = data.message || "Something went wrong.";
          msg.className = "msg err";
        }
      } catch (err) {
        msg.textContent = "Network error. Please try again.";
        msg.className = "msg err";
      }
    });
  }

  /* ---------- 4. NGO DASHBOARD: add a need (AJAX) ---------- */
  const needForm = document.getElementById("needForm");
  if (needForm) {
    needForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const itemType = document.getElementById("item_type").value.trim();
      const desc     = document.getElementById("need_desc").value.trim();
      const msg      = document.getElementById("needMsg");

      if (!itemType) {
        msg.textContent = "Item type is required.";
        msg.className = "msg err";
        return;
      }

      const fd = new FormData();
      fd.append("item_type", itemType);
      fd.append("description", desc);

      try {
        const res  = await fetch("/add_need", { method: "POST", body: fd });
        const data = await res.json();

        if (data.ok) {
          msg.textContent = data.message;
          msg.className = "msg ok";
          needForm.reset();
          // Simple refresh so the new need shows in the list
          setTimeout(() => location.reload(), 700);
        } else {
          msg.textContent = data.error || "Could not add need.";
          msg.className = "msg err";
        }
      } catch (err) {
        msg.textContent = "Network error. Please try again.";
        msg.className = "msg err";
      }
    });
  }

  /* ---------- 5. ADMIN: verify NGO (AJAX) ---------- */
  document.querySelectorAll(".verify-btn").forEach(btn => {
    btn.addEventListener("click", async () => {
      const id = btn.dataset.id;
      btn.disabled = true;
      btn.textContent = "Verifying...";

      try {
        const res  = await fetch(`/admin/verify/${id}`, { method: "POST" });
        const data = await res.json();

        if (data.ok) {
          btn.textContent = "Verified ✓";
          btn.classList.remove("btn-solid");
          btn.style.background = "transparent";
          btn.style.color = "#2E8B74";
          btn.style.cursor = "default";
        } else {
          btn.disabled = false;
          btn.textContent = "Verify";
          alert("Could not verify. Please try again.");
        }
      } catch (err) {
        btn.disabled = false;
        btn.textContent = "Verify";
        alert("Network error. Please try again.");
      }
    });
  });

});

