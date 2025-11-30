/**
 * Checks if the user has an active session.
 * @returns {Promise<boolean>}
 */
export async function checkSession() {
    try {
        const response = await fetch('/check_session');
        const data = await response.json();
        return data.admin;
    } catch {
        return false;
    }
}