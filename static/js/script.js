let Post = document.getElementsByClassName("Post-Container");

function checkSession() {
    let isLoggedIn = localStorage.getItem("isLoggedIn");

    if (isLoggedIn === "true") {
        console.log("✅ User is logged in as admin");
        setAdminSession()
    } else {
        console.log("❌ User is NOT logged in");

    }
}

async function setAdminSession() {
    const response = await fetch('/set_session', {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ admin: true })
    });
    const data = await response.json();
    console.log(data.message);
    checkSession();
}

async function removeAdminSession() {
    const response = await fetch('/set_session', {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ admin: false })
    });
    const data = await response.json();
    console.log(data.message);
    checkSession();
}

document.addEventListener("DOMContentLaded", checkSession);

function loginUser() {
    localStorage.setItem("isLoggedIn", "true");
    checkLoginStatus();
}

function logoutUser() {
    localStorage.removeItem("isLoggedIn");
    checkLoginStatus();
}

// Run on page load

// Toast Notification
document.addEventListener('DOMContentLoaded', () => {
    const toasts = document.querySelectorAll('.toast');
    toasts.forEach(toast => {
        toast.style.opacity = '1';
        toast.style.transform = 'translateY(0)';
        setTimeout(() => {
            if (document.body.contains(toast)) {
                toast.remove();
            }
        }, 4000);

        const closeButton = toast.querySelector('.close');
        if (closeButton) {
            closeButton.addEventListener('click', () => {
                toast.remove();
            });
        }
    });
});

function toggleFilter() {
    var filterPanel = document.getElementById('filterPanel');
    var toggleBtn = document.getElementById('toggleFilterBtn');
    if (filterPanel.classList.contains('open')) {
        filterPanel.classList.remove('open');
        toggleBtn.textContent = 'Show Filter Options';
    } else {
        filterPanel.classList.add('open');
        toggleBtn.textContent = 'Hide Filter Options';
    }
}