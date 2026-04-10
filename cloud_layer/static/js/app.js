document.addEventListener("DOMContentLoaded", () => {
    const pageType = document.getElementById("pageType")?.value;

    if (pageType === "dashboard") {
        initDashboard();
    } else if (pageType === "citizen") {
        initCitizenPortal();
    }
});

// --- Dashboard Logic --- //

function initDashboard() {
    fetchDashboardData();
    // Poll every 5 seconds for real-time vibe
    setInterval(fetchDashboardData, 5000);

    // Search filter
    document.getElementById("searchInput").addEventListener("input", function(e) {
        const term = e.target.value.toLowerCase();
        const rows = document.querySelectorAll("#violationTableBody tr");
        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(term) ? "" : "none";
        });
    });
}

async function fetchDashboardData() {
    try {
        const res = await fetch(`/api/dashboard/data?t=${new Date().getTime()}`);
        const data = await res.json();
        
        const tbody = document.getElementById("violationTableBody");
        tbody.innerHTML = "";
        
        let totalFine = 0;
        
        if(data.violations.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" class="text-center text-secondary py-4">No violations recorded yet.</td></tr>`;
        }

        data.violations.forEach(v => {
            const tr = document.createElement("tr");
            
            // Format time
            const dateObj = new Date(v.timestamp);
            const timeStr = dateObj.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            
            // Format Violations into badges
            let badges = v.violations.map(type => {
                let badgeClass = "bg-primary bg-opacity-25 text-primary border border-primary border-opacity-50";
                if(type === "NO_HELMET") badgeClass = "badge-danger";
                else if(type === "SPITTING") badgeClass = "badge-warning";
                
                return `<span class="badge badge-custom ${badgeClass} me-1 mb-1">${type.replace('_', ' ')}</span>`;
            }).join("");
            
            // Add to total fine for top card
            if (v.challan && v.challan.total_fine) {
                totalFine += v.challan.total_fine;
            }
            
            const challanId = v.challan ? `<br><a href="/challan/${v.challan.challan_id}" target="_blank" class="text-secondary small fw-bold text-decoration-none"><i class="fa-solid fa-file-invoice me-1"></i>${v.challan.challan_id}</a>` : "";

            tr.innerHTML = `
                <td class="text-secondary fw-medium">${timeStr}</td>
                <td class="fw-bold">${v.vehicle_number === 'UNKNOWN_PLATE' ? '<span class="text-secondary">Unknown</span>' : v.vehicle_number} ${challanId}</td>
                <td>${badges}</td>
                <td class="text-secondary"><i class="fa-solid fa-location-dot me-1 small"></i>${v.location}</td>
                <td class="fw-bold text-danger">₹${v.challan ? v.challan.total_fine : 0}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick="window.open('/challan/${v.challan ? v.challan.challan_id : ''}', '_blank')">View Challan</button>
                    <img src="${v.image_path}" class="violation-img ms-2" onclick="showModal('${v.image_path}')" onerror="this.src='https://via.placeholder.com/80x60?text=No+Image'">
                </td>
            `;
            tbody.appendChild(tr);
        });

        // Update Stats Cards
        document.getElementById("totalViolations").innerText = data.violations.length;
        document.querySelector(".stat-card .text-gradient").innerText = `₹${totalFine}`;

    } catch (e) {
        console.error("Error fetching dashboard data", e);
    }
}

function showModal(imgSrc) {
    document.getElementById("modalImg").src = imgSrc;
    const modal = new bootstrap.Modal(document.getElementById('imageModal'));
    modal.show();
}

// --- Citizen Portal Logic --- //

function initCitizenPortal() {
    const form = document.getElementById("reportForm");
    
    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        const btn = document.getElementById("submitBtn");
        const alertArea = document.getElementById("alertArea");
        
        // Gather selected violations
        let violations = [];
        if(document.getElementById("v1").checked) violations.push("NO_HELMET");
        if(document.getElementById("v2").checked) violations.push("TRIPLE_RIDING");
        if(document.getElementById("v3").checked) violations.push("SPITTING");
        
        if (violations.length === 0) {
            showAlert(alertArea, "Please select at least one violation type.", "warning");
            return;
        }

        const fileInput = document.getElementById("reportFile");
        if (fileInput.files.length === 0) {
            showAlert(alertArea, "Please upload evidence.", "warning");
            return;
        }

        btn.disabled = true;
        btn.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Submitting...`;

        const formData = new FormData();
        formData.append("device_id", "Citizen_App");
        formData.append("timestamp", new Date().toISOString());
        formData.append("violations", JSON.stringify(violations));
        formData.append("image", fileInput.files[0]);

        try {
            const res = await fetch('/api/violations', {
                method: "POST",
                body: formData
            });

            if(res.ok) {
                showAlert(alertArea, "Report submitted successfully! Under review.", "success");
                form.reset();
                // Simulate wallet increase after 2 seconds
                setTimeout(() => {
                    const el = document.getElementById("walletAmt");
                    let current = parseFloat(el.innerText);
                    el.innerText = (current + 50.00).toFixed(2);
                }, 2000);
            } else {
                showAlert(alertArea, "Failed to submit report.", "danger");
            }
        } catch (err) {
            showAlert(alertArea, "Network error.", "danger");
        } finally {
            btn.disabled = false;
            btn.innerHTML = `<i class="fa-solid fa-paper-plane me-2"></i>Submit Report`;
        }
    });
}

function showAlert(container, msg, type) {
    container.innerHTML = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${msg}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
}
