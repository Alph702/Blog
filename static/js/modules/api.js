
/**
 * Fetches posts from the API.
 * @param {number} page 
 * @returns {Promise<Object>}
 */
export async function fetchPosts(page) {
    const response = await fetch(`/api/posts?page=${page}`);
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
}

/**
 * Checks if the current user is an admin.
 * @returns {Promise<boolean>}
 */
export async function checkAdminStatus() {
    try {
        const response = await fetch('/api/check_admin');
        const data = await response.json();
        return data.is_admin;
    } catch {
        return false;
    }
}

/**
 * Handles timestamp conversion and display.
 */
export function initTimestampHandlers() {
    document.querySelectorAll('.timestamp').forEach(el => {
        const utcString = el.dataset.ts;
        console.log("UTC String:", utcString);
        const date = new Date(utcString);

        const local = date.toLocaleString(undefined, {
            year: 'numeric',
            month: 'numeric',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            hour12: true // * set to false if you prefer 24-hour format
        });
        el.textContent = "Posted on " + local;
    });
}