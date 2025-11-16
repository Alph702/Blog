const uploadBoxImage = document.getElementById('uploadBoxImage');
const fileInputImage = document.getElementById('image');
const placeholderImage = document.getElementById('placeholderImage');

const uploadBoxVideo = document.getElementById('uploadBoxVideo');
const fileInputVideo = document.getElementById('video');
const placeholderVideo = document.getElementById('placeholderVideo');

function showToast(message, type='info') {
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

uploadBoxVideo.addEventListener('click', () => fileInputVideo.click());
fileInputVideo.addEventListener('change', () => {
    const file = fileInputVideo.files[0];
    if (file) placeholderVideo.textContent = `Selected: ${file.name}`;
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
        placeholderVideo.textContent = `Selected: ${file.name}`;
    } else {
        showToast('Please upload a valid video file.', 'warning');
    }    
});