document.addEventListener("DOMContentLoaded", () => {
    const videoContainers = document.querySelectorAll(".video-container");

    videoContainers.forEach((container) => {
        const videoEl = container.querySelector(".video-player");
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
            const primaryColor = getComputedStyle(document.documentElement)
                .getPropertyValue("--primary-color")
                .trim();
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
                        // Only build if there are multiple quality levels
                        buildQualityOptions(data.levels);
                        qualityBtn.style.display = ""; // Show quality button if levels are available
                    } else {
                        qualityBtn.style.display = "none"; // Hide if no quality levels
                    }
                });

                hlsInstance.on(Hls.Events.LEVEL_SWITCHED, function (event, data) {
                    currentQualityLevel = data.level;
                    // Update UI if needed, e.g., highlight active quality
                    qualityOptionsUl.querySelectorAll("li").forEach((li) => {
                        li.classList.remove("active");
                        if (parseInt(li.dataset.level) === data.level) {
                            li.classList.add("active");
                        }
                    });
                });
            } else if (videoEl.canPlayType("application/vnd.apple.mpegurl")) {
                // Native HLS support (Safari)
                videoEl.src = url;
                qualityBtn.style.display = "none"; // Hide quality button for native HLS
            } else {
                console.error(
                    "This browser does not support HLS natively or via hls.js"
                );
            }
        } else if (url) {
            // Fallback for non-processed videos (e.g., direct MP4 link)
            videoEl.src = url;
            qualityBtn.style.display = "none"; // Hide quality button for non-HLS
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
            progressBar.max = 100; // Reset max to 100 for percentage
            progressBar.value = 0;
            currentTimeDisplay.textContent = formatTime(0);
            updatePlayPauseButton(); // Initial button state
            updateMuteButton(); // Initial mute button state
            changePlaybackSpeed(1); // Initial speed
            updateSliderBackground(progressBar); // Initial progress bar background
            updateSliderBackground(volumeSlider); // Initial volume slider background
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
            e.stopPropagation(); // Prevent document click from immediately closing
            qualityOptionsUl.classList.toggle("active");
            speedOptionsUl.classList.remove("active"); // Close speed options if open
        });

        speedBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            speedOptionsUl.classList.toggle("active");
            qualityOptionsUl.classList.remove("active"); // Close quality options if open
        });

        speedOptionsUl.querySelectorAll("li").forEach((li) => {
            li.addEventListener("click", () =>
                changePlaybackSpeed(parseFloat(li.dataset.speed))
            );
        });

        if (pipBtn) {
            // Check if PiP button exists (browser support)
            pipBtn.addEventListener("click", togglePip);
            videoEl.addEventListener("enterpictureinpicture", () =>
                pipBtn.classList.add("active")
            );
            videoEl.addEventListener("leavepictureinpicture", () =>
                pipBtn.classList.remove("active")
            );
        } else {
            // Hide PiP button if not supported
            pipBtn.style.display = "none";
        }

        // Hide options when clicking outside
        document.addEventListener("click", (e) => {
            if (!qualityOptionsUl.contains(e.target) && e.target !== qualityBtn) {
                qualityOptionsUl.classList.remove("active");
            }
            if (!speedOptionsUl.contains(e.target) && e.target !== speedBtn) {
                speedOptionsUl.classList.remove("active");
            }
        });

        // Hide controls on mouseout and show on mouseenter
        container.addEventListener("mouseenter", showControls);
        container.addEventListener("mousemove", showControls);
        container.addEventListener("mouseleave", hideControlsAfterDelay);

        // Initial state setup
        updatePlayPauseButton();
        updateMuteButton();
        volumeSlider.value = videoEl.volume * 100;
    });
});
