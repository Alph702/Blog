import { showToast } from '../modules/ui.js'
/**
 * Video player with HLS support.
 */
export class VideoPlayer {
    /**
     * @param {HTMLElement} container 
     */
    constructor(container) {
        this.container = container;
        this.videoEl = container.querySelector('.video-player');
        this.hlsInstance = null;
        this.currentQualityLevel = -1;
        this.controlsTimeout = null;
        this.warningCount = 0;
        this.maxWarnings = 10;

        this.bindMethods();
        this.initControls();
        this.initVideo();
    }

    bindMethods() {
        this.togglePlayPause = this.togglePlayPause.bind(this);
        this.updatePlayPauseButton = this.updatePlayPauseButton.bind(this);
        this.updateProgressBar = this.updateProgressBar.bind(this);
        this.seekVideo = this.seekVideo.bind(this);
        this.toggleMute = this.toggleMute.bind(this);
        this.changeVolume = this.changeVolume.bind(this);
        this.updateMuteButton = this.updateMuteButton.bind(this);
        this.toggleFullscreen = this.toggleFullscreen.bind(this);
        this.updateFullscreenButton = this.updateFullscreenButton.bind(this);
        this.togglePip = this.togglePip.bind(this);
        this.showControls = this.showControls.bind(this);
        this.hideControls = this.hideControls.bind(this);
        this.hideControlsAfterDelay = this.hideControlsAfterDelay.bind(this);
    }

    initControls() {
        this.playOverlay = this.container.querySelector(".play-overlay");
        this.playPauseBtn = this.container.querySelector(".play-pause-btn");
        this.playPauseIcon = this.playPauseBtn.querySelector(".play-icon");
        this.progressBar = this.container.querySelector(".progress-bar");
        this.currentTimeDisplay = this.container.querySelector(".current-time-display");
        this.durationDisplay = this.container.querySelector(".duration-display");
        this.muteBtn = this.container.querySelector(".mute-btn");
        this.volumeIcon = this.muteBtn.querySelector(".volume-icon");
        this.volumeSlider = this.container.querySelector(".volume-slider");
        this.fullscreenBtn = this.container.querySelector(".fullscreen-btn");
        this.fullscreenIcon = this.fullscreenBtn.querySelector(".fullscreen-icon");
        this.qualityBtn = this.container.querySelector(".quality-btn");
        this.qualityOptionsUl = this.container.querySelector(".quality-options");
        this.speedBtn = this.container.querySelector(".speed-btn");
        this.speedOptionsUl = this.container.querySelector(".speed-options");
        this.pipBtn = this.container.querySelector(".pip-btn");
        this.controlsOverlay = this.container.querySelector(".controls-overlay");

        // --- Event Listeners ---
        this.playOverlay.addEventListener("click", this.togglePlayPause);
        this.playPauseBtn.addEventListener("click", this.togglePlayPause);
        this.videoEl.addEventListener("click", this.togglePlayPause);
        this.videoEl.addEventListener("play", this.updatePlayPauseButton);
        this.videoEl.addEventListener("pause", this.updatePlayPauseButton);
        this.videoEl.addEventListener("ended", this.updatePlayPauseButton);
        this.videoEl.addEventListener("timeupdate", this.updateProgressBar);
        this.videoEl.addEventListener("loadedmetadata", () => {
            this.durationDisplay.textContent = this.formatTime(this.videoEl.duration);
            this.progressBar.max = 100;
            this.progressBar.value = 0;
            this.currentTimeDisplay.textContent = this.formatTime(0);
            this.updatePlayPauseButton();
            this.updateMuteButton();
            this.changePlaybackSpeed(1);
            this.updateSliderBackground(this.progressBar);
            this.updateSliderBackground(this.volumeSlider);
        });
        this.progressBar.addEventListener("input", this.seekVideo);

        this.muteBtn.addEventListener("click", this.toggleMute);
        this.volumeSlider.addEventListener("input", this.changeVolume);
        this.videoEl.addEventListener("volumechange", this.updateMuteButton);

        this.fullscreenBtn.addEventListener("click", this.toggleFullscreen);
        document.addEventListener("fullscreenchange", this.updateFullscreenButton);
        document.addEventListener("webkitfullscreenchange", this.updateFullscreenButton);
        document.addEventListener("mozfullscreenchange", this.updateFullscreenButton);
        document.addEventListener("msfullscreenchange", this.updateFullscreenButton);

        this.qualityBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            this.qualityOptionsUl.classList.toggle("active");
            this.speedOptionsUl.classList.remove("active");
        });

        this.speedBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            this.speedOptionsUl.classList.toggle("active");
            this.qualityOptionsUl.classList.remove("active");
        });

        this.speedOptionsUl.querySelectorAll("li").forEach((li) => {
            li.addEventListener("click", () =>
                this.changePlaybackSpeed(parseFloat(li.dataset.speed))
            );
        });

        if (this.pipBtn && document.pictureInPictureEnabled && !this.videoEl.disablePictureInPicture) {
            this.pipBtn.addEventListener("click", this.togglePip);
            this.videoEl.addEventListener("enterpictureinpicture", () =>
                this.pipBtn.classList.add("active")
            );
            this.videoEl.addEventListener("leavepictureinpicture", () =>
                this.pipBtn.classList.remove("active")
            );
        } else if (this.pipBtn) {
            this.pipBtn.style.display = "none";
        }

        document.addEventListener("click", (e) => {
            if (!this.qualityOptionsUl.contains(e.target) && e.target !== this.qualityBtn) {
                this.qualityOptionsUl.classList.remove("active");
            }
            if (!this.speedOptionsUl.contains(e.target) && e.target !== this.speedBtn) {
                this.speedOptionsUl.classList.remove("active");
            }
        });
        this.container.addEventListener("mouseenter", this.showControls);
        this.container.addEventListener("mousemove", this.showControls);
        this.container.addEventListener("mouseleave", this.hideControlsAfterDelay);

        this.updatePlayPauseButton();
        this.updateMuteButton();
        this.volumeSlider.value = this.videoEl.volume * 100;
    }

    initVideo() {
        const url = this.videoEl.dataset.filepath;
        const status = this.videoEl.dataset.status;

        if (url && status === "processed") {
            if (typeof Hls !== "undefined" && Hls.isSupported()) {
                this.hlsInstance = new Hls();
                this.hlsInstance.loadSource(url);
                this.hlsInstance.attachMedia(this.videoEl);
                this.hlsInstance.on(Hls.Events.MANIFEST_PARSED, (event, data) => {
                    console.log("HLS Manifest Parsed. Available levels:", data.levels);
                    if (data.levels && data.levels.length > 1) {
                        this.buildQualityOptions(data.levels);
                        this.qualityBtn.style.display = "";
                    } else {
                        this.qualityBtn.style.display = "none";
                    }
                });

                this.hlsInstance.on(Hls.Events.LEVEL_SWITCHED, (event, data) => {
                    this.currentQualityLevel = data.level;
                    this.qualityOptionsUl.querySelectorAll("li").forEach((li) => {
                        li.classList.remove("active");
                        if (parseInt(li.dataset.level) === data.level) {
                            li.classList.add("active");
                        }
                    });
                });

                this.hlsInstance.on(Hls.Events.ERROR, (event, data) => {
                    if (data.fatal) {
                        switch (data.type) {
                            case "networkError":
                                showToast("A network error occurred while streaming the video.", "error");
                                console.error("HLS fatal network error:", data);
                                break;
                            case "mediaError":
                                showToast("A media error occurred while streaming the video.", "error");
                                console.error("HLS fatal media error:", data);
                                this.hlsInstance.recoverMediaError();
                                break;
                            default:
                                showToast("An unrecoverable error occurred while streaming the video.", "error");
                                console.error("HLS fatal error:", data);
                                this.hlsInstance.destroy();
                                break;
                        }
                    } else {
                        this.warningCount++;
                        if (this.warningCount >= this.maxWarnings) {
                            showToast("Multiple non-fatal errors occurred while streaming the video.", "warning");
                            console.warn("HLS multiple non-fatal errors, destroying HLS instance.");
                        } else {
                            console.warn("HLS non-fatal error:", data);
                        }
                    }
                });
            } else if (this.videoEl.canPlayType("application/vnd.apple.mpegurl")) {
                this.videoEl.src = url;
                this.qualityBtn.style.display = "none";
            } else {
                showToast("This browser does not support HLS natively or via hls.js", "info");
                console.error(
                    "This browser does not support HLS natively or via hls.js"
                );
            }
        } else if (url) {
            this.videoEl.src = url;
            this.qualityBtn.style.display = "none";
        }
    }

    formatTime(seconds) {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = Math.floor(seconds % 60);
        return `${minutes.toString().padStart(2, "0")}:${remainingSeconds
            .toString()
            .padStart(2, "0")}`;
    }

    updateSliderBackground(slider) {
        const percentage =
            ((slider.value - slider.min) / (slider.max - slider.min)) * 100;
        slider.style.background = `linear-gradient(to right, var(--primary-color) 0%, var(--primary-color) ${percentage}%,rgba(255, 255, 255, 0.4) ${percentage}%, rgba(255, 255, 255, 0.4) 100%)`;
    }

    togglePlayPause() {
        if (this.videoEl.paused || this.videoEl.ended) {
            this.videoEl.play();
        } else {
            this.videoEl.pause();
        }
    }

    updatePlayPauseButton() {
        if (this.videoEl.paused || this.videoEl.ended) {
            this.playPauseIcon.src = "/static/svg/play.svg";
            this.playOverlay.classList.remove("hidden");
            this.container.classList.remove("playing");
            this.container.classList.add("paused");
            this.showControls();
        } else {
            this.playPauseIcon.src = "/static/svg/pause.svg";
            this.playOverlay.classList.add("hidden");
            this.container.classList.add("playing");
            this.container.classList.remove("paused");
            this.hideControlsAfterDelay();
        }
    }

    updateProgressBar() {
        this.progressBar.value = (this.videoEl.currentTime / this.videoEl.duration) * 100;
        this.currentTimeDisplay.textContent = this.formatTime(this.videoEl.currentTime);
        this.updateSliderBackground(this.progressBar);
    }

    seekVideo() {
        const seekTime = (this.progressBar.value / 100) * this.videoEl.duration;
        this.videoEl.currentTime = seekTime;
    }

    toggleMute() {
        this.videoEl.muted = !this.videoEl.muted;
        this.updateMuteButton();
        this.volumeSlider.value = this.videoEl.muted ? 0 : this.videoEl.volume * 100;
        this.updateSliderBackground(this.volumeSlider);
    }

    updateMuteButton() {
        if (this.videoEl.muted || this.videoEl.volume === 0) {
            this.volumeIcon.src = "/static/svg/volume-mute.svg";
        } else {
            this.volumeIcon.src = "/static/svg/volume-up.svg";
        }
    }

    changeVolume() {
        this.videoEl.volume = this.volumeSlider.value / 100;
        this.videoEl.muted = this.videoEl.volume === 0;
        this.updateMuteButton();
        this.updateSliderBackground(this.volumeSlider);
    }

    toggleFullscreen() {
        if (!document.fullscreenElement) {
            this.container.requestFullscreen().catch((err) => {
                showToast("Error attempting to enable full-screen mode.", "error");
                console.error(
                    `Error attempting to enable full-screen mode: ${err.message} (${err.name})`
                );
            });
        } else {
            document.exitFullscreen();
        }
    }

    updateFullscreenButton() {
        if (document.fullscreenElement === this.container) {
            this.fullscreenIcon.src = "/static/svg/fullscreen-exit.svg";
            this.container.classList.add("fullscreen");
        } else {
            this.fullscreenIcon.src = "/static/svg/fullscreen.svg";
            this.container.classList.remove("fullscreen");
        }
    }

    buildQualityOptions(levels) {
        this.qualityOptionsUl.innerHTML = ""; // Clear existing options

        // Add 'Auto' option
        const autoLi = document.createElement("li");
        autoLi.textContent = "Auto";
        autoLi.dataset.level = -1;
        if (this.currentQualityLevel === -1) {
            autoLi.classList.add("active");
        }
        autoLi.addEventListener("click", () => this.selectQualityLevel(-1));
        this.qualityOptionsUl.appendChild(autoLi);

        levels
            .sort((a, b) => b.height - a.height)
            .forEach((level, index) => {
                const li = document.createElement("li");
                li.textContent = `${level.height}p`;
                li.dataset.level = index; // Use index for Hls.js level
                if (this.currentQualityLevel === index) {
                    li.classList.add("active");
                }
                li.addEventListener("click", () => this.selectQualityLevel(index));
                this.qualityOptionsUl.appendChild(li);
            });
    }

    selectQualityLevel(levelIndex) {
        if (this.hlsInstance) {
            this.hlsInstance.currentLevel = levelIndex;
            this.currentQualityLevel = levelIndex;
            // Update active class
            this.qualityOptionsUl.querySelectorAll("li").forEach((li) => {
                li.classList.remove("active");
                if (parseInt(li.dataset.level) === levelIndex) {
                    li.classList.add("active");
                }
            });
        }
        this.qualityOptionsUl.classList.remove("active"); // Hide options after selection
    }

    changePlaybackSpeed(speed) {
        this.videoEl.playbackRate = speed;
        this.speedBtn.textContent = `${speed}x`;
        this.speedOptionsUl.querySelectorAll("li").forEach((li) => {
            li.classList.remove("active");
            if (parseFloat(li.dataset.speed) === speed) {
                li.classList.add("active");
            }
        });
        this.speedOptionsUl.classList.remove("active");
    }

    togglePip() {
        if (document.pictureInPictureElement) {
            document.exitPictureInPicture();
        } else if (this.videoEl.requestPictureInPicture) {
            this.videoEl.requestPictureInPicture();
        }
    }

    hideControls() {
        this.container.classList.remove("show-controls");
        this.container.classList.add("hide-controls");
    }

    showControls() {
        this.container.classList.remove("hide-controls");
        this.container.classList.add("show-controls");
        clearTimeout(this.controlsTimeout);
        if (!this.videoEl.paused) {
            this.hideControlsAfterDelay();
        }
    }

    hideControlsAfterDelay() {
        clearTimeout(this.controlsTimeout);
        this.controlsTimeout = setTimeout(() => {
            if (!this.videoEl.paused && !this.container.matches(":hover")) {
                this.hideControls();
            }
        }, 3000); // Hide after 3 seconds of inactivity
    }
}