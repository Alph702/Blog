import { fetchPosts, initTimestampHandlers } from './modules/api.js';
import { checkSession } from './modules/auth.js';
import { initToastHandlers, initLazyPostLoading, toggleFilter } from './modules/ui.js';
import { VideoPlayer } from './modules/video_player.js';

document.addEventListener('DOMContentLoaded', async () => {
    // Check admin status
    const isAdmin = await checkSession();
    console.log("Admin:", isAdmin);
    
    // Initialize modules
    initToastHandlers();
    initTimestampHandlers();
    initLazyPostLoading();
    
    // Initialize all video players
    document.querySelectorAll('.video-container').forEach(container => {
        new VideoPlayer(container);
    });
});

export { fetchPosts, toggleFilter };

// Make toggleFilter available globally for inline onclick handlers
window.toggleFilter = toggleFilter;