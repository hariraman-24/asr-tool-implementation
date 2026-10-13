/**
 * MeetBrief - Meeting Platform Client Engine
 * Handles Real-Time ASR, Minutes of Meeting (MoM) Formatting, Text-to-Speech (TTS), and Persistence.
 */

document.addEventListener('DOMContentLoaded', () => {
  // Elements
  const meetingTitleInput = document.getElementById('meetingTitleInput');
  const momAgendaDisplay = document.getElementById('momAgendaDisplay');
  const toggleMicBtn = document.getElementById('toggleMicBtn');
  const micBtnText = document.getElementById('micBtnText');
  const speakerTile = document.querySelector('.speaker-tile');
  const micStatusPrompt = document.getElementById('micStatusPrompt');
  const meetingStatusBadge = document.getElementById('meetingStatusBadge');
  const meetingStatusText = document.getElementById('meetingStatusText');
  const meetingTimer = document.getElementById('meetingTimer');
  const wordCountBadge = document.getElementById('wordCountBadge');

  const momOutput = document.getElementById('momOutput');
  const interimOutput = document.getElementById('interimOutput');
  const clearMomBtn = document.getElementById('clearMomBtn');

  const ttsPlayBtn = document.getElementById('ttsPlayBtn');
  const ttsBtnText = document.getElementById('ttsBtnText');
  const saveMomBtn = document.getElementById('saveMomBtn');
  const downloadTxtBtn = document.getElementById('downloadTxtBtn');
  const audioUploadInput = document.getElementById('audioUploadInput');

  const archivesGrid = document.getElementById('archivesGrid');
  const canvas = document.getElementById('audioVisualizer');
  const canvasCtx = canvas ? canvas.getContext('2d') : null;

  // State Variables
  let isListening = false;
  let recognition = null;
  let restartTimeout = null;
  let timerInterval = null;
  let meetingStartTime = null;
  let isSpeakingTTS = false;
  let animFrameId = null;

  // Buffer state for continuous infinite dictation
  let committedMomEntries = [];
  let currentSessionFinal = '';

  // 1. Sync Meeting Agenda Title
  if (meetingTitleInput && momAgendaDisplay) {
    meetingTitleInput.addEventListener('input', () => {
      momAgendaDisplay.textContent = meetingTitleInput.value.trim() || 'General Meeting';
    });
  }

  // 2. Format Timestamp helper
  function getFormattedTime() {
    const now = new Date();
    return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  }

  // 3. Initialize Web Speech API for Real-Time Streaming ASR
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

  function initSpeechEngine() {
    if (!SpeechRecognition) {
      micStatusPrompt.textContent = 'Web Speech ASR not supported in this browser. Please use Google Chrome or Edge.';
      return null;
    }

    const rec = new SpeechRecognition();
    rec.continuous = true;
    rec.interimResults = true;
    rec.lang = 'en-US';

    rec.onresult = (event) => {
      let interim = '';
      let sessionFinal = '';

      for (let i = 0; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          sessionFinal += event.results[i][0].transcript + ' ';
        } else {
          interim += event.results[i][0].transcript;
        }
      }

      currentSessionFinal = sessionFinal.trim();
      interimOutput.textContent = interim;

      // Update Word Count
      updateWordCount();
      autoScrollMom();
    };

    rec.onerror = (event) => {
      console.warn('Speech engine warning:', event.error);
      if (event.error === 'not-allowed') {
        alert('Microphone access denied. Please permit microphone access in browser settings.');
        stopListening();
      }
    };

    rec.onend = () => {
      // Commit final chunk to MoM entry
      commitCurrentSpeech();

      // Continuous auto-restart (avoids 60-word / timeout drop)
      if (isListening) {
        clearTimeout(restartTimeout);
        restartTimeout = setTimeout(() => {
          if (isListening) {
            try { recognition.start(); } catch (e) {}
          }
        }, 150);
      }
    };

    return rec;
  }

  recognition = initSpeechEngine();

  // Commit text with timestamp to MoM
  function commitCurrentSpeech() {
    if (currentSessionFinal) {
      const timeStr = getFormattedTime();
      addMomEntry(timeStr, currentSessionFinal);
      currentSessionFinal = '';
      interimOutput.textContent = '';
      updateWordCount();
      autoScrollMom();
    }
  }

  function addMomEntry(timeStr, text) {
    const entryText = `[${timeStr}] ${text.trim()}\n\n`;
    momOutput.innerText = (momOutput.innerText.trim() ? momOutput.innerText.trim() + '\n\n' : '') + `[${timeStr}] ${text.trim()}`;
    committedMomEntries.push({ time: timeStr, text: text.trim() });
  }

  function autoScrollMom() {
    const container = document.querySelector('.mom-editor-container');
    if (container) {
      container.scrollTop = container.scrollHeight;
    }
  }

  function updateWordCount() {
    const text = (momOutput.innerText + ' ' + interimOutput.textContent).trim();
    const count = text ? text.split(/\s+/).filter(Boolean).length : 0;
    wordCountBadge.textContent = `${count} words`;
  }

  // 4. Toggle Microphone
  toggleMicBtn.addEventListener('click', () => {
    if (!isListening) {
      startListening();
    } else {
      stopListening();
    }
  });

  function startListening() {
    isListening = true;
    toggleMicBtn.classList.add('active');
    toggleMicBtn.innerHTML = '<i class="fa-solid fa-microphone"></i> Mute Mic';

    speakerTile.classList.add('active');
    meetingStatusBadge.className = 'meet-status active';
    meetingStatusText.textContent = 'Meeting in Progress';
    micStatusPrompt.textContent = 'Microphone active • Live speech is transcribing to Minutes of Meeting (MoM)...';

    // Meeting Duration Timer
    if (!meetingStartTime) {
      meetingStartTime = Date.now();
    }
    clearInterval(timerInterval);
    timerInterval = setInterval(() => {
      const elapsed = Math.floor((Date.now() - meetingStartTime) / 1000);
      const m = String(Math.floor(elapsed / 60)).padStart(2, '0');
      const s = String(elapsed % 60).padStart(2, '0');
      meetingTimer.textContent = `${m}:${s}`;
    }, 500);

    // Audio Visualizer Waveform
    startVisualizer();

    if (recognition) {
      try { recognition.start(); } catch (e) {}
    }
  }

  function stopListening() {
    isListening = false;
    clearTimeout(restartTimeout);

    toggleMicBtn.classList.remove('active');
    toggleMicBtn.innerHTML = '<i class="fa-solid fa-microphone-slash"></i> Unmute Mic';

    speakerTile.classList.remove('active');
    meetingStatusBadge.className = 'meet-status ready';
    meetingStatusText.textContent = 'Paused';
    micStatusPrompt.textContent = 'Microphone paused. Click "Unmute Mic" to resume discussion.';

    if (recognition) {
      try { recognition.stop(); } catch (e) {}
    }

    commitCurrentSpeech();
    stopVisualizer();
  }

  // 5. Visualizer Canvas
  function startVisualizer() {
    if (!canvasCtx || !canvas) return;
    let step = 0;

    function renderBars() {
      if (!isListening) return;
      canvasCtx.clearRect(0, 0, canvas.width, canvas.height);
      const bars = 32;
      const barWidth = canvas.width / bars;

      for (let i = 0; i < bars; i++) {
        const height = Math.abs(Math.sin((i + step) * 0.3)) * (canvas.height * 0.75) + 4;
        const x = i * barWidth;
        const y = (canvas.height - height) / 2;

        canvasCtx.fillStyle = '#06b6d4';
        canvasCtx.fillRect(x + 2, y, barWidth - 4, height);
      }
      step += 0.4;
      animFrameId = requestAnimationFrame(renderBars);
    }
    renderBars();
  }

  function stopVisualizer() {
    if (animFrameId) cancelAnimationFrame(animFrameId);
    if (canvasCtx && canvas) {
      canvasCtx.clearRect(0, 0, canvas.width, canvas.height);
    }
  }

  // 6. Text-to-Speech (TTS): Read Aloud Minutes of Meeting
  ttsPlayBtn.addEventListener('click', () => {
    const textToRead = momOutput.innerText.trim();
    if (!textToRead) {
      alert("No Minutes of Meeting text available to read aloud. Please record or type some minutes first.");
      return;
    }

    if (isSpeakingTTS) {
      window.speechSynthesis.cancel();
      isSpeakingTTS = false;
      ttsPlayBtn.classList.remove('speaking');
      ttsBtnText.textContent = 'Read Aloud MoM';
    } else {
      window.speechSynthesis.cancel(); // Reset any existing speech
      const utterance = new SpeechSynthesisUtterance(textToRead);
      utterance.rate = 1.0;
      utterance.pitch = 1.0;

      utterance.onstart = () => {
        isSpeakingTTS = true;
        ttsPlayBtn.classList.add('speaking');
        ttsBtnText.textContent = 'Stop Speaking';
      };

      utterance.onend = () => {
        isSpeakingTTS = false;
        ttsPlayBtn.classList.remove('speaking');
        ttsBtnText.textContent = 'Read Aloud MoM';
      };

      utterance.onerror = () => {
        isSpeakingTTS = false;
        ttsPlayBtn.classList.remove('speaking');
        ttsBtnText.textContent = 'Read Aloud MoM';
      };

      window.speechSynthesis.speak(utterance);
    }
  });

  // Global helper for card Read Aloud
  window.readAloudText = function(text) {
    if (!text) return;
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    window.speechSynthesis.speak(u);
  };

  // 7. Save MoM to SQLite Database
  saveMomBtn.addEventListener('click', async () => {
    commitCurrentSpeech();
    const text = momOutput.innerText.trim();
    if (!text) {
      alert("Cannot save empty Minutes of Meeting. Please speak or type meeting notes first.");
      return;
    }

    const title = meetingTitleInput.value.trim() || 'General Team Discussion';
    const duration = meetingTimer.textContent || '00:00';

    const formData = new FormData();
    formData.append('title', title);
    formData.append('mom_text', text);
    formData.append('duration', duration);

    try {
      const res = await fetch('/api/save-mom', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();

      if (data.success) {
        saveMomBtn.innerHTML = '<i class="fa-solid fa-check"></i> <span>Saved!</span>';
        setTimeout(() => {
          saveMomBtn.innerHTML = '<i class="fa-solid fa-floppy-disk"></i> <span>Save MoM</span>';
        }, 2200);
        appendArchiveCard(data);
      } else {
        alert("Error saving meeting: " + (data.error || "Unknown error"));
      }
    } catch (e) {
      console.error('Save error:', e);
      alert("Failed to save meeting: " + e.message);
    }
  });

  function appendArchiveCard(data) {
    const emptyState = document.getElementById('emptyArchivesState');
    if (emptyState) emptyState.remove();

    const card = document.createElement('div');
    card.className = 'archive-card';
    card.id = `meeting-card-${data.meeting_id}`;
    card.innerHTML = `
      <div class="card-head">
        <h4 class="card-title">${data.title}</h4>
        <div class="card-actions">
          <button class="icon-btn" onclick="readAloudText(${JSON.stringify(momOutput.innerText.trim())})" title="Read Aloud">
            <i class="fa-solid fa-volume-high"></i>
          </button>
          <a href="/api/meeting/${data.meeting_id}/download" class="icon-btn" title="Download TXT">
            <i class="fa-solid fa-download"></i>
          </a>
          <button class="icon-btn delete" onclick="deleteSavedMeeting(${data.meeting_id})" title="Delete">
            <i class="fa-solid fa-trash-can"></i>
          </button>
        </div>
      </div>
      <div class="card-meta">
        <span><i class="fa-regular fa-calendar"></i> ${data.date}</span>
        <span><i class="fa-regular fa-clock"></i> ${data.time}</span>
        <span><i class="fa-solid fa-stopwatch"></i> ${data.duration}</span>
      </div>
      <div class="card-snippet">${momOutput.innerText.trim()}</div>
    `;
    archivesGrid.prepend(card);
  }

  // 8. Delete Meeting
  window.deleteSavedMeeting = async function(id) {
    if (!confirm("Delete this saved Minutes of Meeting record?")) return;
    try {
      const res = await fetch(`/api/meeting/${id}`, { method: 'DELETE' });
      const data = await res.json();
      if (data.success) {
        const el = document.getElementById(`meeting-card-${id}`);
        if (el) el.remove();
      }
    } catch (e) {
      console.error('Delete error:', e);
    }
  };

  // 9. Export TXT Directly from Browser
  downloadTxtBtn.addEventListener('click', () => {
    commitCurrentSpeech();
    const text = momOutput.innerText.trim();
    if (!text) {
      alert("No Minutes of Meeting text to export.");
      return;
    }

    const title = meetingTitleInput.value.trim() || 'Meeting_Minutes';
    const blob = new Blob([
      `MINUTES OF THE MEETING (MoM)\n`,
      `Subject: ${title}\n`,
      `Date: ${new Date().toLocaleDateString()}\n`,
      `Duration: ${meetingTimer.textContent}\n`,
      `==================================================\n\n`,
      text
    ], { type: 'text/plain;charset=utf-8' });

    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `MoM_${title.replace(/[^a-zA-Z0-9_-]/g, '_')}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  });

  // 10. Clear MoM text
  clearMomBtn.addEventListener('click', () => {
    if (confirm("Clear the current Minutes of Meeting editor?")) {
      momOutput.innerText = '';
      interimOutput.textContent = '';
      committedMomEntries = [];
      updateWordCount();
    }
  });

  // 11. Upload Audio File ASR
  audioUploadInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    micStatusPrompt.textContent = `Transcribing audio file "${file.name}" using Faster-Whisper ASR...`;
    const formData = new FormData();
    formData.append('audio', file);

    try {
      const res = await fetch('/api/transcribe-audio', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();

      if (data.success) {
        addMomEntry(getFormattedTime(), data.transcript);
        updateWordCount();
        autoScrollMom();
        micStatusPrompt.textContent = `File transcribed via ${data.engine}.`;
      } else {
        alert("ASR Error: " + (data.error || "Could not transcribe audio."));
        micStatusPrompt.textContent = 'Audio transcription error.';
      }
    } catch (err) {
      console.error('Audio upload error:', err);
      alert("Failed to transcribe audio file: " + err.message);
    }
  });

  // 12. Starter Discussion Chips
  document.querySelectorAll('.starter-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      const text = chip.getAttribute('data-text');
      addMomEntry(getFormattedTime(), text);
      updateWordCount();
      autoScrollMom();
    });
  });
});
