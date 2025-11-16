document.addEventListener("DOMContentLoaded", () => {
    const videoContainers = document.querySelectorAll(".video-container");
    videoContainers.forEach(initializeVideoPlayer);
});

function initializeVideoPlayer(container) {
    const videoEl = container.querySelector(".video-player");
    if (!videoEl) {
        console.error("Video player element not found in container.");
        return;
    }
    const url = videoEl.dataset.url;
    const status = videoEl.dataset.status;

    // Get control elements
    const playOverlay = container.querySelector(".play-overlay");
    const playPauseBtn = container.querySelector(".play-pause-btn");
    const playPauseIcon = playPauseBtn.querySelector(".play-icon");
    const progressBar = container.querySelector(".progress-bar");
    const currentTimeDisplay = container.querySelector(".current-time-display");
    const durationDisplay = container.querySelector(".duration-display");
    const muteBtn = container.querySelector(".mute-btn");
    const volumeIcon = muteBtn.querySelector(".volume-icon");
    const volumeSlider = container.querySelector(".volume-slider");
    const fullscreenBtn = container.querySelector(".fullscreen-btn");
    const fullscreenIcon = fullscreenBtn.querySelector(".fullscreen-icon");
    const qualityBtn = container.querySelector(".quality-btn");
    const qualityOptionsUl = container.querySelector(".quality-options");
    const speedBtn = container.querySelector(".speed-btn");
    const speedOptionsUl = container.querySelector(".speed-options");
    const pipBtn = container.querySelector(".pip-btn");
    const controlsOverlay = container.querySelector(".controls-overlay");

    let hlsInstance = null;
    let currentQualityLevel = -1; // -1 for auto
    let controlsTimeout;

    // --- Helper Functions ---
    function formatTime(seconds) {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = Math.floor(seconds % 60);
        return `${minutes.toString().padStart(2, "0")}:${remainingSeconds
            .toString()
            .padStart(2, "0")}`;
    }

    function updateSliderBackground(slider) {
        const percentage =
            ((slider.value - slider.min) / (slider.max - slider.min)) * 100;
        slider.style.background = `linear-gradient(to right, var(--primary-color) 0%, var(--primary-color) ${percentage}%,rgba(255, 255, 255, 0.4) ${percentage}%, rgba(255, 255, 255, 0.4) 100%)`;
    }

    function togglePlayPause() {
        if (videoEl.paused || videoEl.ended) {
            videoEl.play();
        } else {
            videoEl.pause();
        }
    }

    function updatePlayPauseButton() {
        if (videoEl.paused || videoEl.ended) {
            playPauseIcon.src = "/static/svg/play.svg";
            playOverlay.classList.remove("hidden");
            container.classList.remove("playing");
            container.classList.add("paused");
            showControls();
        } else {
            playPauseIcon.src = "/static/svg/pause.svg";
            playOverlay.classList.add("hidden");
            container.classList.add("playing");
            container.classList.remove("paused");
            hideControlsAfterDelay();
        }
    }

    function updateProgressBar() {
        progressBar.value = (videoEl.currentTime / videoEl.duration) * 100;
        currentTimeDisplay.textContent = formatTime(videoEl.currentTime);
        updateSliderBackground(progressBar);
    }

    function seekVideo() {
        const seekTime = (progressBar.value / 100) * videoEl.duration;
        videoEl.currentTime = seekTime;
    }

    function toggleMute() {
        videoEl.muted = !videoEl.muted;
        updateMuteButton();
        volumeSlider.value = videoEl.muted ? 0 : videoEl.volume * 100;
        updateSliderBackground(volumeSlider);
    }

    function updateMuteButton() {
        if (videoEl.muted || videoEl.volume === 0) {
            volumeIcon.src = "/static/svg/volume-mute.svg";
        } else {
            volumeIcon.src = "/static/svg/volume-up.svg";
        }
    }

    function changeVolume() {
        videoEl.volume = volumeSlider.value / 100;
        videoEl.muted = videoEl.volume === 0;
        updateMuteButton();
        updateSliderBackground(volumeSlider);
    }

    function toggleFullscreen() {
        if (!document.fullscreenElement) {
            container.requestFullscreen().catch((err) => {
                console.error(
                    `Error attempting to enable full-screen mode: ${err.message} (${err.name})`
                );
            });
        } else {
            document.exitFullscreen();
        }
    }

    function updateFullscreenButton() {
        if (document.fullscreenElement === container) {
            fullscreenIcon.src = "/static/svg/fullscreen-exit.svg";
            container.classList.add("fullscreen");
        } else {
            fullscreenIcon.src = "/static/svg/fullscreen.svg";
            container.classList.remove("fullscreen");
        }
    }

    function buildQualityOptions(levels) {
        qualityOptionsUl.innerHTML = ""; // Clear existing options

        // Add 'Auto' option
        const autoLi = document.createElement("li");
        autoLi.textContent = "Auto";
        autoLi.dataset.level = -1;
        if (currentQualityLevel === -1) {
            autoLi.classList.add("active");
        }
        autoLi.addEventListener("click", () => selectQualityLevel(-1));
        qualityOptionsUl.appendChild(autoLi);

        levels
            .sort((a, b) => b.height - a.height)
            .forEach((level, index) => {
                const li = document.createElement("li");
                li.textContent = `${level.height}p`;
                li.dataset.level = index; // Use index for Hls.js level
                if (currentQualityLevel === index) {
                    li.classList.add("active");
                }
                li.addEventListener("click", () => selectQualityLevel(index));
                qualityOptionsUl.appendChild(li);
            });
    }

    function selectQualityLevel(levelIndex) {
        if (hlsInstance) {
            hlsInstance.currentLevel = levelIndex;
            currentQualityLevel = levelIndex;
            // Update active class
            qualityOptionsUl.querySelectorAll("li").forEach((li) => {
                li.classList.remove("active");
                if (parseInt(li.dataset.level) === levelIndex) {
                    li.classList.add("active");
                }
            });
        }
        qualityOptionsUl.classList.remove("active"); // Hide options after selection
    }

    function changePlaybackSpeed(speed) {
        videoEl.playbackRate = speed;
        speedBtn.textContent = `${speed}x`;
        speedOptionsUl.querySelectorAll("li").forEach((li) => {
            li.classList.remove("active");
            if (parseFloat(li.dataset.speed) === speed) {
                li.classList.add("active");
            }
        });
        speedOptionsUl.classList.remove("active");
    }

    function togglePip() {
        if (document.pictureInPictureElement) {
            document.exitPictureInPicture();
        } else if (videoEl.requestPictureInPicture) {
            videoEl.requestPictureInPicture();
        }
    }

    function hideControls() {
        container.classList.remove("show-controls");
        container.classList.add("hide-controls");
    }

    function showControls() {
        container.classList.remove("hide-controls");
        container.classList.add("show-controls");
        clearTimeout(controlsTimeout);
        if (!videoEl.paused) {
            hideControlsAfterDelay();
        }
    }

    function hideControlsAfterDelay() {
        clearTimeout(controlsTimeout);
        controlsTimeout = setTimeout(() => {
            if (!videoEl.paused && !container.matches(":hover")) {
                hideControls();
            }
        }, 3000); // Hide after 3 seconds of inactivity
    }

    // --- Initialize HLS or Native Playback ---
    if (url && status === "processed") {
        if (Hls.isSupported()) {
            hlsInstance = new Hls();
            hlsInstance.loadSource(url);
            hlsInstance.attachMedia(videoEl);

            hlsInstance.on(Hls.Events.MANIFEST_PARSED, function (event, data) {
                console.log("HLS Manifest Parsed. Available levels:", data.levels);
                if (data.levels && data.levels.length > 1) {
                    buildQualityOptions(data.levels);
                    qualityBtn.style.display = "";
                } else {
                    qualityBtn.style.display = "none";
                }
            });

            hlsInstance.on(Hls.Events.LEVEL_SWITCHED, function (event, data) {
                currentQualityLevel = data.level;
                qualityOptionsUl.querySelectorAll("li").forEach((li) => {
                    li.classList.remove("active");
                    if (parseInt(li.dataset.level) === data.level) {
                        li.classList.add("active");
                    }
                });
            });

            hlsInstance.on(Hls.Events.ERROR, function (event, data) {
                if (data.fatal) {
                    switch (data.type) {
                        case Hls.ErrorTypes.NETWORK_ERROR:
                            console.error("HLS fatal network error:", data);
                            break;
                        case Hls.ErrorTypes.MEDIA_ERROR:
                            console.error("HLS fatal media error:", data);
                            hlsInstance.recoverMediaError();
                            break;
                        default:
                            console.error("HLS fatal error:", data);
                            hlsInstance.destroy();
                            break;
                    }
                } else {
                    console.warn("HLS non-fatal error:", data);
                }
            });
        } else if (videoEl.canPlayType("application/vnd.apple.mpegurl")) {
            videoEl.src = url;
            qualityBtn.style.display = "none";
        } else {
            console.error(
                "This browser does not support HLS natively or via hls.js"
            );
        }
    } else if (url) {
        videoEl.src = url;
        qualityBtn.style.display = "none";
    }

    // --- Event Listeners ---
    playOverlay.addEventListener("click", togglePlayPause);
    playPauseBtn.addEventListener("click", togglePlayPause);
    videoEl.addEventListener("click", togglePlayPause);
    videoEl.addEventListener("play", updatePlayPauseButton);
    videoEl.addEventListener("pause", updatePlayPauseButton);
    videoEl.addEventListener("ended", updatePlayPauseButton);

    videoEl.addEventListener("timeupdate", updateProgressBar);
    videoEl.addEventListener("loadedmetadata", () => {
        durationDisplay.textContent = formatTime(videoEl.duration);
        progressBar.max = 100;
        progressBar.value = 0;
        currentTimeDisplay.textContent = formatTime(0);
        updatePlayPauseButton();
        updateMuteButton();
        changePlaybackSpeed(1);
        updateSliderBackground(progressBar);
        updateSliderBackground(volumeSlider);
    });
    progressBar.addEventListener("input", seekVideo);

    muteBtn.addEventListener("click", toggleMute);
    volumeSlider.addEventListener("input", changeVolume);
    videoEl.addEventListener("volumechange", updateMuteButton);

    fullscreenBtn.addEventListener("click", toggleFullscreen);
    document.addEventListener("fullscreenchange", updateFullscreenButton);
    document.addEventListener("webkitfullscreenchange", updateFullscreenButton);
    document.addEventListener("mozfullscreenchange", updateFullscreenButton);
    document.addEventListener("msfullscreenchange", updateFullscreenButton);

    qualityBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        qualityOptionsUl.classList.toggle("active");
        speedOptionsUl.classList.remove("active");
    });

    speedBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        speedOptionsUl.classList.toggle("active");
        qualityOptionsUl.classList.remove("active");
    });

    speedOptionsUl.querySelectorAll("li").forEach((li) => {
        li.addEventListener("click", () =>
            changePlaybackSpeed(parseFloat(li.dataset.speed))
        );
    });

    if (pipBtn && document.pictureInPictureEnabled && !videoEl.disablePictureInPicture) {
        pipBtn.addEventListener("click", togglePip);
        videoEl.addEventListener("enterpictureinpicture", () =>
            pipBtn.classList.add("active")
        );
        videoEl.addEventListener("leavepictureinpicture", () =>
            pipBtn.classList.remove("active")
        );
    } else if (pipBtn) {
        pipBtn.style.display = "none";
    }

    document.addEventListener("click", (e) => {
        if (!qualityOptionsUl.contains(e.target) && e.target !== qualityBtn) {
            qualityOptionsUl.classList.remove("active");
        }
        if (!speedOptionsUl.contains(e.target) && e.target !== speedBtn) {
            speedOptionsUl.classList.remove("active");
        }
    });

    container.addEventListener("mouseenter", showControls);
    container.addEventListener("mousemove", showControls);
    container.addEventListener("mouseleave", hideControlsAfterDelay);

    updatePlayPauseButton();
    updateMuteButton();
    volumeSlider.value = videoEl.volume * 100;
}

