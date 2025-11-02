const uploadBoxImage = document.getElementById('uploadBoxImage');
const fileInputImage = document.getElementById('image');
const placeholderImage = document.getElementById('placeholderImage');

const uploadBoxVideo = document.getElementById('uploadBoxVideo');
const fileInputVideo = document.getElementById('video');
const placeholderVideo = document.getElementById('placeholderVideo');

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
    fileInputImage.files = e.dataTransfer.files;
    if (file) placeholderImage.textContent = `Selected: ${file.name}`;
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
    fileInputVideo.files = e.dataTransfer.files;
    if (file) placeholderVideo.textContent = `Selected: ${file.name}`;
});