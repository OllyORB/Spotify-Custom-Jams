document.addEventListener("DOMContentLoaded", function () {
    let isPlaying = false;
    let playbackPosition = 0;
    let playbackDuration = 0;
    let lastTrackDuration = 0;
    let flag = false;
    let lastFetchTime = Date.now();
    let shuffleState = "false"; // Use string to match server response
    let repeatState = "off"; // Possible values: 'off', 'track', 'context'
    let isManualAction = false; // Flag for manual actions
    let isUserInteractingWithSlider = false;
    const debounceDelay = 300; // 300 milliseconds delay for debouncing

// Fetch initial playback state
fetchPlaybackState();

// Fetch playback state every 4 seconds
setInterval(() => {
    if (!isManualAction) {
    fetchPlaybackState();
    }
}, 2000);

function fetchPlaybackState() {
    fetch("/check_device")
    .then((response) => response.json())
    .then((data) => {
        if (data.is_active) {
        // Hide the "no active device" message and show the player
        document.getElementById("no-device-message").style.display = "none";
        document.getElementById("song-cover").style.display = "block";
        document.getElementById("song-info").style.display = "block";
        document.getElementById("playback-controls").style.display = "flex";
        document.getElementById("progress-container").style.display =
            "block";
        document.getElementById("volume-container").style.display = "flex";

        fetch("/get_playback_state")
            .then((response) => response.json())
            .then((data) => {
            // Update playback controls, song info, etc.
            updatePlaybackState(data);
            });
        } else {
        // Show the "no active device" message and hide the player
        document.getElementById("no-device-message").style.display =
            "block";
        document.getElementById("song-cover").style.display = "none";
        document.getElementById("song-info").style.display = "none";
        document.getElementById("playback-controls").style.display = "none";
        document.getElementById("progress-container").style.display =
            "none";
        document.getElementById("volume-container").style.display = "none";
        }
    });
}

function updatePlaybackState(data) {
    playbackPosition = data.progress_ms;
    playbackDuration = data.duration_ms;
    if (playbackDuration != lastTrackDuration) {
    flag = true;
    }
    lastTrackDuration = playbackDuration;
    isPlaying = data.is_playing;
    shuffleState = data.shuffle_state;
    repeatState = data.repeat_state;
    lastFetchTime = Date.now();

    updatePlayPauseIcon();
    updateShuffleIcon(shuffleState);
    updateRepeatIcon(repeatState);
    updateSongInfo(data);

    const volume = data.volume;
    document.getElementById("volume-slider").value = volume;
    document.getElementById("volume-display").textContent = volume;

    // Update progress bar and time display
    if (!isUserInteractingWithSlider || flag == true) {
    updateCurrentTimeDisplay(playbackPosition);
    updateProgressBar();
    updateTrackDurationDisplay(playbackDuration);
    flag = false;
    }
}

function debounce(func, delay) {
    let timeout;
    return function (...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), delay);
    };
}

const handlePlayPauseClick = debounce(function () {
    isManualAction = true; // Set flag before performing action
    fetch(isPlaying ? "/pause_playback" : "/play_playback", {
    method: "POST",
    })
    .then((response) => response.json())
    .then((data) => {
        isPlaying = !isPlaying;
        updatePlayPauseIcon();
        isManualAction = false; // Reset flag after action
    })
    .catch((error) => {
        console.error(
        `Error ${isPlaying ? "pausing" : "starting"} playback:`,
        error
        );
        isManualAction = false; // Ensure flag is reset on error
    });
}, debounceDelay);

const handleRepeatClick = debounce(function () {
    isManualAction = true; // Set flag before performing action
    toggleRepeatState();
}, debounceDelay);

const handleShuffleClick = debounce(function () {
    isManualAction = true; // Set flag before performing action
    toggleShuffleState();
}, debounceDelay);

const handleNextClick = debounce(function () {
    isManualAction = true; // Set flag before performing action
    nextTrack();
}, debounceDelay);

const handlePrevClick = debounce(function () {
    isManualAction = true; // Set flag before performing action
    previousTrack();
}, debounceDelay);

document
    .getElementById("play-pause-button")
    .addEventListener("click", handlePlayPauseClick);
document
    .getElementById("repeat-button")
    .addEventListener("click", handleRepeatClick);
document
    .getElementById("shuffle-button")
    .addEventListener("click", handleShuffleClick);
document
    .getElementById("next-button")
    .addEventListener("click", handleNextClick);
document
    .getElementById("prev-button")
    .addEventListener("click", handlePrevClick);

const volumeSlider = document.getElementById("volume-slider");
volumeSlider.addEventListener("input", function () {
    document.getElementById("volume-display").textContent = this.value;
});
volumeSlider.addEventListener("mouseup", function () {
    updateSlider("volume", this.value);
});

const progressSlider = document.getElementById("progress-slider");
progressSlider.addEventListener("input", function () {
    isUserInteractingWithSlider = true;
    const newPosition = (this.value / 100) * playbackDuration;
    document.getElementById("current-time").textContent =
    formatTime(newPosition);
});
progressSlider.addEventListener("mouseup", function () {
    isUserInteractingWithSlider = false;
    const newPositionPercent = this.value;
    const newPlaybackPosition = (newPositionPercent / 100) * playbackDuration;
    updateSlider("playback", newPlaybackPosition);
});

document
    .getElementById("device-dropdown")
    .addEventListener("change", function () {
    updateDevice(this.value);
    });

function toggleRepeatState() {
    fetch("/toggle_repeat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ value: repeatState }),
    })
    .then((response) => response.json())
    .then((data) => {
        repeatState = data.repeat_state;
        updateRepeatIcon(repeatState);
        isManualAction = false; // Reset flag after action
    })
    .catch((error) => {
        console.error("Error toggling repeat:", error);
        isManualAction = false; // Ensure flag is reset on error
    });
}

function toggleShuffleState() {
    fetch("/toggle_shuffle", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    })
    .then((response) => response.json())
    .then((data) => {
        shuffleState = data.shuffle_state;
        updateShuffleIcon(shuffleState);
        isManualAction = false; // Reset flag after action
    })
    .catch((error) => {
        console.error("Error toggling shuffle:", error);
        isManualAction = false; // Ensure flag is reset on error
    });
}

function nextTrack() {
    fetch("/next_track", { method: "POST" })
    .then((response) => response.json())
    .then((data) => {
        setTimeout(() => {
        fetchPlaybackState(); // Update playback state after a delay
        }, 500); // Adjust delay duration as needed
        isManualAction = false; // Reset flag after action
    })
    .catch((error) => {
        console.error("Error advancing to next track:", error);
        isManualAction = false; // Ensure flag is reset on error
    });
}

function previousTrack() {
    fetch("/previous_track", { method: "POST" })
    .then((response) => response.json())
    .then((data) => {
        setTimeout(() => {
        fetchPlaybackState(); // Update playback state after a delay
        }, 500); // Adjust delay duration as needed
        isManualAction = false; // Reset flag after action
    })
    .catch((error) => {
        console.error("Error going back to previous track:", error);
        isManualAction = false; // Ensure flag is reset on error
    });
}

function updateSlider(type, value) {
    fetch(`/update_${type}_position`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ value }),
    }).catch((error) =>
    console.error(`Error updating ${type} position:`, error)
    );
}

function updatePlayPauseIcon() {
    document.getElementById("play-pause-icon").src = isPlaying
    ? "/static/buttons/pause.png"
    : "/static/buttons/play.png";
}

function updateShuffleIcon(state) {
    const shuffleIcon = document
    .getElementById("shuffle-button")
    .querySelector("img");
    shuffleIcon.src =
    state === "true"
        ? "/static/buttons/shuffle_on.png"
        : "/static/buttons/shuffle_off.png";
}

function updateRepeatIcon(state) {
    const repeatIcon = document
    .getElementById("repeat-button")
    .querySelector("img");
    repeatIcon.src =
    state === "off"
        ? "/static/buttons/repeat_off.png"
        : state === "track"
        ? "/static/buttons/repeat_one.png"
        : "/static/buttons/repeat_all.png";
}

function updateSongInfo(data) {
    document.getElementById("current-track-title").textContent = data.title;
    document.getElementById("current-track-artist").textContent = data.artist;
    document.getElementById("current-song-image").src = data.image_url;
}

function updateDeviceDropdown(devices, currentDeviceId) {
    const deviceDropdown = document.getElementById("device-dropdown");

    // Clear the existing options
    deviceDropdown.innerHTML = "";

    // Populate the dropdown with available devices
    devices.forEach((device) => {
    const option = document.createElement("option");
    option.value = device.id;
    option.textContent = device.name;

    // Set the selected device
    if (device.id === currentDeviceId) {
        option.selected = true;
    }

    deviceDropdown.appendChild(option);
    });

    if (devices.length === 0) {
    const option = document.createElement("option");
    option.value = "";
    option.textContent = "No devices available";
    option.disabled = true;
    deviceDropdown.appendChild(option);
    }
}

function updateTrackDurationDisplay(duration) {
    document.getElementById("track-duration").textContent =
    formatTime(duration);
}

function updateCurrentTimeDisplay(position) {
    document.getElementById("current-time").textContent =
    formatTime(position);
}

function updateProgressBar() {
    const progress = (playbackPosition / playbackDuration) * 100;
    document.getElementById("progress-slider").value = progress;
}

function formatTime(ms) {
    const minutes = Math.floor(ms / 60000);
    const seconds = Math.floor((ms % 60000) / 1000);
    return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}
});
