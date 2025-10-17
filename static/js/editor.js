// On page load, check if full-screen mode was enabled
window.onload = function () {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('fullscreen') === 'true') {
        FullScreen();
    }
};
const editor = document.getElementById("editor");

editor.addEventListener("keydown", function (event) {
    const cursorPos = editor.selectionStart;
    const value = editor.value;

    // Handle auto-closing only when typing '>'
    if (event.key === ">" && cursorPos > 1) {
        const beforeCursor = value.substring(0, cursorPos);
        const match = beforeCursor.match(/<([a-zA-Z0-9]+)$/);

        if (match) {
            event.preventDefault();
            const tag = match[1];
            const closingTag = `>${`</${tag}>`}`;

            editor.value = value.substring(0, cursorPos) + closingTag + value.substring(cursorPos);
            editor.selectionStart = editor.selectionEnd = cursorPos + 1;
        }
    }

    if (event.key === "Backspace" || event.key === "Delete") {
        return;
    }
});

function FullScreen() {
    const container = document.querySelector(".form");
    const button = document.querySelector(".form").querySelector("button");
    const full_screen_button = document.querySelector(".full-screen-button");
    const form_text_input = document.querySelector(".form-text-input");
    const editor = document.getElementById("editor");
    const form_file_input = document.querySelector(".form-file-input");
    const popup = document.getElementById('popup');

    container.classList.toggle("full-screen");
    button.classList.toggle("full-screen");
    full_screen_button.classList.toggle("full-screen");
    form_text_input.classList.toggle("full-screen");
    form_file_input.classList.toggle("full-screen");
    editor.classList.toggle("full-screen");
    if (editor.classList.contains("full-screen")) {
        popup.classList.add('show');
    }
    if (container.classList.contains("full-screen")) {
        window.history.pushState({}, '', '?fullscreen=true');
    } else {
        window.history.pushState({}, '', window.location.pathname);
    }


    setTimeout(() => {
        popup.classList.remove('show');
    }, 1500);
}
editor.addEventListener('keydown', function (event) {
    if (event.shiftKey && event.key === 'Enter') {
        event.preventDefault();

        const content = editor.value;
        const title = document.querySelector('input[name="title"]').value;
        const formData = new FormData();
        formData.append('title', title);
        formData.append('content', content);

        fetch('/new', {
            method: 'POST',
            body: formData,
        })
            .then(response => {
                if (response.ok) {
                    console.log('Post submitted successfully.');
                    if (editor.classList.contains("full-screen")) {
                        editor.value = '';
                    } else {
                        window.location.href = '/new';
                    }
                } else {
                    alert('Error while submitting the post.');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Something went wrong while submitting the post.');
            });
    }
    if (event.key === 'Escape') {
        if (editor.classList.contains("full-screen")) {
            FullScreen();
        }
    }
});