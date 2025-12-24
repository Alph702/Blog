const uploadBoxImage = document.getElementById('uploadBoxImage');
const fileInputImage = document.getElementById('image');
const placeholderImage = document.getElementById('placeholderImage');

const uploadBoxVideo = document.getElementById('uploadBoxVideo');
const fileInputVideo = document.getElementById('video');
const placeholderVideo = document.getElementById('placeholderVideo');

// Store uploaded video ID
let uploadedVideoId = null;

function showToast(message, type = 'info') {
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
 * Show loader in the video upload box
 */
function showVideoLoader() {
    // Hide the placeholder text and show loader
    placeholderVideo.style.display = 'none';

    // Remove existing loader if any
    const existingLoader = uploadBoxVideo.querySelector('.upload-loader-container');
    if (existingLoader) existingLoader.remove();

    // Create loader container
    const loaderContainer = document.createElement('div');
    loaderContainer.className = 'upload-loader-container';
    loaderContainer.style.cssText = 'display: flex; flex-direction: column; align-items: center; gap: 10px; padding: 20px;';

    // Create loader spinner
    const loader = document.createElement('div');
    loader.className = 'loader';

    // Create loading text
    const loadingText = document.createElement('p');
    loadingText.className = 'upload-status-text';
    loadingText.textContent = 'Uploading video...';
    loadingText.style.cssText = 'margin: 0; color: var(--primary-color);';

    loaderContainer.appendChild(loader);
    loaderContainer.appendChild(loadingText);
    uploadBoxVideo.appendChild(loaderContainer);

    // Disable clicking during upload
    uploadBoxVideo.style.pointerEvents = 'none';
    uploadBoxVideo.style.opacity = '0.7';

    // Disable submit button during upload
    const submitBtn = uploadBoxVideo.closest('form')?.querySelector('button[type="submit"]');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.style.opacity = '0.5';
        submitBtn.style.cursor = 'not-allowed';
    }
}

/**
 * Hide loader and show success/error state
 */
function hideVideoLoader(success, filename = '') {
    const loaderContainer = uploadBoxVideo.querySelector('.upload-loader-container');
    if (loaderContainer) loaderContainer.remove();

    // Re-enable submit button
    const submitBtn = uploadBoxVideo.closest('form')?.querySelector('button[type="submit"]');
    if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.style.opacity = '1';
        submitBtn.style.cursor = 'pointer';
    }

    placeholderVideo.style.display = 'block';
    uploadBoxVideo.style.pointerEvents = 'auto';
    uploadBoxVideo.style.opacity = '1';

    if (success) {
        placeholderVideo.innerHTML = `<span style="color: var(--primary-color);">✓ Uploaded:</span> ${filename}`;
        uploadBoxVideo.style.borderColor = '#28a745';
    } else {
        placeholderVideo.textContent = 'Drag & Drop video file here or click to select';
        uploadBoxVideo.style.borderColor = 'var(--primary-color)';
    }
}

/**
 * Upload video immediately when file is selected
 */
async function uploadVideoFile(file) {
    if (!file || !file.type.startsWith('video/')) {
        showToast('Please upload a valid video file.', 'warning');
        return;
    }

    showVideoLoader();

    const formData = new FormData();
    formData.append('video', file);

    try {
        const response = await fetch('/api/upload-video', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok && data.success) {
            uploadedVideoId = data.video_id;

            // Create or update hidden input for video_id
            let hiddenInput = document.querySelector('input[name="video_id"]');
            if (!hiddenInput) {
                hiddenInput = document.createElement('input');
                hiddenInput.type = 'hidden';
                hiddenInput.name = 'video_id';
                uploadBoxVideo.closest('form').appendChild(hiddenInput);
            }
            hiddenInput.value = uploadedVideoId;

            hideVideoLoader(true, file.name);
            showToast('Video uploaded successfully!', 'success');
        } else {
            hideVideoLoader(false);
            showToast(data.error || 'Video upload failed.', 'error');
        }
    } catch (error) {
        console.error('Video upload error:', error);
        hideVideoLoader(false);
        showToast('Video upload failed. Please try again.', 'error');
    }
}

// Image upload handlers (unchanged functionality)
if (uploadBoxImage && fileInputImage && placeholderImage) {
    uploadBoxImage.addEventListener('click', () => fileInputImage.click());
    fileInputImage.addEventListener('change', () => {
        const file = fileInputImage.files[0];
        if (file) placeholderImage.textContent = `Selected: ${file.name}`;
    });

    uploadBoxImage.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadBoxImage.classList.add('dragover');
    });

    uploadBoxImage.addEventListener('dragleave', () => {
        uploadBoxImage.classList.remove('dragover');
    });

    uploadBoxImage.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadBoxImage.classList.remove('dragover');
        const file = e.dataTransfer.files[0];
        if (file && file.type.startsWith('image/')) {
            fileInputImage.files = e.dataTransfer.files;
            placeholderImage.textContent = `Selected: ${file.name}`;
        } else {
            showToast('Please upload a valid image file.', 'warning');
        }
    });
}

// Video upload handlers - now with immediate upload
if (uploadBoxVideo && fileInputVideo && placeholderVideo) {
    uploadBoxVideo.addEventListener('click', () => fileInputVideo.click());
    fileInputVideo.addEventListener('change', () => {
        const file = fileInputVideo.files[0];
        if (file) {
            uploadVideoFile(file);
        }
    });

    uploadBoxVideo.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadBoxVideo.classList.add('dragover');
    });

    uploadBoxVideo.addEventListener('dragleave', () => {
        uploadBoxVideo.classList.remove('dragover');
    });

    uploadBoxVideo.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadBoxVideo.classList.remove('dragover');
        const file = e.dataTransfer.files[0];
        if (file && file.type.startsWith('video/')) {
            fileInputVideo.files = e.dataTransfer.files;
            uploadVideoFile(file);
        } else {
            showToast('Please upload a valid video file.', 'warning');
        }
    });
}