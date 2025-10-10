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

// ✅ Set session (Admin Login)
async function setAdminSession() {
    const response = await fetch('/set_session', {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ admin: true })  // Set admin session
    });
    const data = await response.json();
    console.log(data.message);
    checkSession(); // Refresh UI without reloading page
}

// ✅ Remove session (Logout)
async function removeAdminSession() {
    const response = await fetch('/set_session', {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ admin: false })  // Remove session
    });
    const data = await response.json();
    console.log(data.message);
    checkSession(); // Refresh UI without reloading page
}

// ✅ Run check when page loadso
document.addEventListener("DOMContentLaded", checkSession);

// Function to log in (to be called after successful login)
function loginUser() {
    localStorage.setItem("isLoggedIn", "true");
    checkLoginStatus();
}

// Function to log out
function logoutUser() {
    localStorage.removeItem("isLoggedIn");
    checkLoginStatus();
}

// Run on page load

// Toast Notification
document.addEventListener('DOMContentLoaded', () => {
    const toasts = document.querySelectorAll('.toast');
    toasts.forEach(toast => {
        // Make toast visible immediately (no smooth animation due to current CSS)
        toast.style.opacity = '1';
        toast.style.transform = 'translateY(0)';
        // Auto-dismiss after 4 seconds
        setTimeout(() => {
            if (document.body.contains(toast)) {
                toast.remove();
            }
        }, 4000);

        // Manual dismissal via close button
        const closeButton = toast.querySelector('.close');
        if (closeButton) {
            closeButton.addEventListener('click', () => {
                toast.remove();
            });
        }
    });
});