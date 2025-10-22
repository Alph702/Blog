document.addEventListener("DOMContentLoaded", () => {
    // Find all players with class "video-js"
    const videoElements = document.querySelectorAll(".video-js");

    videoElements.forEach((videoEl) => {
        const id = videoEl.dataset.id;
        const filename = videoEl.dataset.filename;
        const filepath = videoEl.dataset.filepath;
        const status = videoEl.dataset.status;
        const url = videoEl.dataset.url;

        // Initialize player
        const player = videojs(`videoPlayer${id}`, {
    fluid: true,
    controlBar: {
        volumePanel: { inline: false },
    },
});

        console.log(`🎬 Initialized ${id} (${filename})`);

        //  Quality Levels Plugin
const qualityLevels = player.qualityLevels();

        //  Create Quality Button
const Button = videojs.getComponent("MenuButton");
const qualityButton = new Button(player, { name: "QualityButton" });
qualityButton.addClass("vjs-quality-button");
qualityButton.el().innerHTML =
    '<span class="vjs-icon-cog" title="Quality"></span>';

player.controlBar.addChild(
    qualityButton,
    {},
    player.controlBar.children_.length - 1
);

        //  Create dropdown menu for quality options
const menu = document.createElement("div");
menu.className = "vjs-quality-menu";
menu.style.display = "none";
menu.style.position = "absolute";
menu.style.bottom = "35px";
menu.style.right = "10px";
qualityButton.el().appendChild(menu);

let qualityOptions = [];

        // Fill in quality levels when detected
qualityLevels.on("addqualitylevel", (event) => {
    const level = event.qualityLevel;
    if (!qualityOptions.find((q) => q.height === level.height)) {
        qualityOptions.push(level);
    }
});

// Toggle menu on click
qualityButton.el().addEventListener("click", (e) => {
    e.stopPropagation();
    if (qualityOptions.length === 0) {
        menu.innerHTML = '<div style="padding:8px;">No quality levels yet</div>';
        menu.style.display = "block";
        return;
    }

    menu.innerHTML = "";
    qualityOptions
        .sort((a, b) => b.height - a.height)
        .forEach((level) => {
            const btn = document.createElement("button");
            btn.textContent = `${level.height}p (${Math.round(
                level.bitrate / 1000
            )} kbps)`;
            btn.onclick = () => {
                for (let i = 0; i < qualityLevels.length; i++) {
                            qualityLevels[i].enabled =
                                qualityLevels[i].height === level.height;
                }
                menu.style.display = "none";
            };
            menu.appendChild(btn);
        });

    menu.style.display = menu.style.display === "none" ? "block" : "none";
});

        // Hide when clicking outside
document.addEventListener("click", (e) => {
    if (!qualityButton.el().contains(e.target)) {
        menu.style.display = "none";
    }
});

        // Load video source (auto)
        if (status === "processed") {
            const hlsUrl = `${url}/master.m3u8`;
            player.src({ src: hlsUrl, type: "application/x-mpegURL" });
            console.log(`🎥 ${id} → HLS (${hlsUrl})`);
        } else {
            const normalUrl = `/uploads/${filename}`;
            player.src({ src: normalUrl, type: "video/mp4" });
            console.log(`📁 ${id} → MP4 (${normalUrl})`);
        }
        
        // Stop anchor click when interacting with the player or its children
        videoEl.addEventListener("click", e => {
        e.stopPropagation();
        e.preventDefault();
        });

        // Also stop clicks inside Video.js overlay elements
        videoEl.addEventListener("mousedown", e => {
        e.stopPropagation();
        });
        videoEl.addEventListener("mouseup", e => {
        e.stopPropagation();
        });

        // Fix for internal control buttons created by Video.js
        videoEl.addEventListener("touchstart", e => e.stopPropagation());
        videoEl.addEventListener("touchend", e => e.stopPropagation());
    });
});
