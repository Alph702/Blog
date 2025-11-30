/**
 * Shows a toast notification.
 * @param {string} message 
 * @param {string} type - 'success', 'error', 'info', 'warning'
 */
export const showToast = (message, type = 'info') => {
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container';
        document.body.appendChild(toastContainer);
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    toast.innerHTML = `
        <div class="toast-body">
            ${message}
        </div>
        <button type="button" class="close" data-dismiss="toast" aria-label="Close">
            <span aria-hidden="true">&times;</span>
        </button>
    `;
    toastContainer.appendChild(toast);
    toastContainer.style.opacity = '1';
    toastContainer.style.transform = 'translateY(0)';
    setTimeout(() => toast.remove(), 4000);
}

/**
 * Initializes toast handlers.
 */
export const initToastHandlers = () => {
    const toasts = document.querySelectorAll('.toast');
    toasts.forEach(toast => {
        toast.style.opacity = '1';
        setTimeout(() => toast.remove(), 4000);
    });
}

/**
 * Toggles the filter panel.
 */
export const toggleFilter = () => {
    const panel = document.getElementById('filterPanel');
    const btn = document.getElementById('toggleFilterBtn');

    if (panel.classList.contains('open')) {
        panel.classList.remove('open');
        btn.textContent = 'Show Filter Options';
    } else {
        panel.classList.add('open');
        btn.textContent = 'Hide Filter Options';
    }
}

/** Initializes lazy loading of posts on scroll. */
export const initLazyPostLoading = () => {
    const postsContainer = document.getElementById('posts-container');
    const loadingIndicator = document.getElementById('loading-indicator');
    const endOfPostsMessage = document.getElementById('end-of-posts-message');

    if (!postsContainer) return;

    window.addEventListener('scroll', () => {
        // Load more posts when the user is 100px from the bottom
        if ((window.innerHeight + window.scrollY) >= document.body.offsetHeight - 100) {
            loadMorePosts(postsContainer, loadingIndicator, endOfPostsMessage);
        }
    });
}

/** Loads more posts and appends them to the container.
 * @param {HTMLElement} postsContainer 
 * @param {HTMLElement} loadingIndicator 
 * @param {HTMLElement} endOfPostsMessage 
 */
const loadMorePosts = async (postsContainer, loadingIndicator, endOfPostsMessage) => {

    let page = 2; // Start with page 2, since page 1 is loaded initially
    let isLoading = false;
    let hasNext = true;

    if (isLoading || !hasNext) return;

    isLoading = true;
    loadingIndicator.style.display = 'flex';
    loadingIndicator.style.alignItems = 'center';
    loadingIndicator.style.alignContent = 'center';
    loadingIndicator.style.justifyContent = 'center';

    try {
        const response = await fetch(`/api/posts?page=${page}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();

        if (data.posts && data.posts.length > 0) {
            const isAdmin = await fetch('/api/check_admin')
                .then(res => res.json())
                .then(resData => resData.is_admin)
                .catch(() => false);
            data.posts.forEach(post => {
                const postLink = document.createElement('div');
                postLink.className = 'post';

                let adminLinks = '';
                if (isAdmin) {
                    adminLinks = `
                            <a style="padding-right: 5px;" href="/edit/${post.id}">Edit</a>
                            <a href="/delete/${post.id}">Delete</a>
                        `;
                }

                let imageHTML = '';
                if (post.image) {
                    imageHTML = `
                            <div class="gallery">
                                <img src="${post.image}" alt="Post Image" class="image" loading="lazy">
                            </div>
                            <br>
                        `;
                }

                let videoHTML = '';
                if (post.video) {
                    const video = post.video;
                    videoHTML = `
                            <div class="video-container" data-id="${video.id}">
                                <div class="play-overlay">
                                    <img src="/static/svg/play.svg" alt="Play" class="play-overlay-icon">
                                </div>
                                <video
                                    id="videoPlayer${video.id}"
                                    class="video-player"
                                    preload="auto"
                                    data-id="${video.id}"
                                    data-filename="${video.filename}"
                                    data-filepath="${video.filepath}"
                                    data-status="${video.status}"
                                    data-url="${video.url}">
                                </video>
                                <div class="controls-overlay">
                                    <div class="controls-bar">
                                        <button class="play-pause-btn" aria-label="Play/Pause">
                                            <img src="/static/svg/play.svg" alt="Play" class="play-icon">
                                        </button>
                                        <div class="progress-bar-container">
                                            <input type="range" class="progress-bar" value="0" min="0" max="100" step="0.1">
                                            <div class="time-display">
                                                <span class="current-time-display">00:00</span> / <span class="duration-display">00:00</span>
                                            </div>
                                        </div>
                                        <div class="volume-container">
                                            <button class="mute-btn" aria-label="Mute/Unmute">
                                                <img src="/static/svg/volume-up.svg" alt="Volume" class="volume-icon">
                                            </button>
                                            <input type="range" class="volume-slider" value="100" min="0" max="100">
                                        </div>
                                        <div class="playback-speed-selector">
                                            <button class="speed-btn">1x</button>
                                            <ul class="speed-options">
                                                <li data-speed="0.5">0.5x</li>
                                                <li data-speed="0.75">0.75x</li>
                                                <li data-speed="1">1x</li>
                                                <li data-speed="1.25">1.25x</li>
                                                <li data-speed="1.5">1.5x</li>
                                                <li data-speed="2">2x</li>
                                            </ul>
                                        </div>
                                        <div class="quality-selector-container">
                                            <button class="quality-btn" aria-label="Quality">
                                                <img src="/static/svg/gear.svg" alt="Quality" class="quality-icon">
                                            </button>
                                            <ul class="quality-options"></ul>
                                        </div>
                                        <button class="pip-btn" aria-label="Picture-in-Picture">
                                            <img src="/static/svg/pip.svg" alt="PiP" class="pip-icon">
                                        </button>
                                        <button class="fullscreen-btn" aria-label="Fullscreen">
                                            <img src="/static/svg/fullscreen.svg" alt="Fullscreen" class="fullscreen-icon">
                                        </button>
                                    </div>
                                </div>
                            </div>
                        `;
                }

                postLink.innerHTML = `
                        <a href="/post/${post.id}" class="post-button">
                            <h1 class="Heding">${post.title}</h1>
                            <p class="text">${post.content}</p>
                            ${imageHTML}
                            <a>
                            ${videoHTML}
                            </a>
                            <small>Posted on ${post.timestamps ? new Date(post.timestamps).toLocaleDateString(undefined, {
                    year: 'numeric',
                    month: 'numeric',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                    hour12: true // * set to false if you prefer 24-hour format
                }) : ''}</small>
                            <br>
                            ${adminLinks}
                        </a>
                    `;
                postsContainer.appendChild(postLink);

                if (post.video) {
                    const newVideoContainer = postLink.querySelector('.video-container');
                    if (newVideoContainer && typeof initializeVideoPlayer === 'function') {
                        initializeVideoPlayer(newVideoContainer);
                    }
                }
            });
            page++;
        }

        hasNext = data.has_next;
        if (!hasNext) {
            endOfPostsMessage.style.display = 'block';
        }

    } catch (error) {
        console.error("Failed to load more posts:", error);
        // Optionally, display an error message to the user
    } finally {
        isLoading = false;
        loadingIndicator.style.display = 'none';
    }
};