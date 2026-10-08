(function () {
    'use strict';

    const recordButton = document.querySelector('[data-record]');
    const recordLabel = document.querySelector('[data-record-label]');
    const cancelButton = document.querySelector('[data-cancel]');
    const timerElement = document.querySelector('[data-timer]');
    const timerProgress = document.querySelector('[data-timer-progress]');
    const statusElement = document.querySelector('[data-practice-status]');
    const coachBubble = document.querySelector('[data-coach-bubble]');
    const waveform = document.querySelector('[data-waveform]');
    const recordingNote = document.querySelector('[data-recording-note]');
    const scenarioName = document.querySelector('[data-scenario-name]')?.dataset.scenarioName || 'Entrevista de trabajo';
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';
    const totalSeconds = 60;
    const circumference = 2 * Math.PI * 78;
    let elapsedSeconds = 0;
    let timerId;
    let mediaRecorder;
    let audioChunks = [];
    let recordingStartedAt;

    if (!recordButton) return;
    timerProgress.style.strokeDasharray = circumference;
    timerProgress.style.strokeDashoffset = circumference;

    function renderTime() {
        const remaining = totalSeconds - elapsedSeconds;
        const minutes = String(Math.floor(remaining / 60)).padStart(2, '0');
        const seconds = String(remaining % 60).padStart(2, '0');
        timerElement.textContent = `${minutes}:${seconds}`;
        timerProgress.style.strokeDashoffset = circumference * (1 - elapsedSeconds / totalSeconds);
    }

    function setRecordingState(isRecording) {
        document.body.classList.toggle('is-recording', isRecording);
        recordButton.classList.toggle('is-recording', isRecording);
        waveform.classList.toggle('is-active', isRecording);
        recordLabel.textContent = isRecording ? 'Detener grabacion' : 'Grabar respuesta';
        statusElement.textContent = isRecording ? 'Te escucho...' : 'Listo cuando tu lo estés';
        coachBubble.textContent = isRecording ? 'Te escucho...' : '¿Listo para empezar?';
    }

    function stopRecording(save = true) {
        clearInterval(timerId);
        if (mediaRecorder && mediaRecorder.state === 'recording') mediaRecorder.stop();
        setRecordingState(false);
        if (!save) audioChunks = [];
    }

    async function saveSession() {
        const audio = new Blob(audioChunks, { type: mediaRecorder?.mimeType || 'audio/webm' });
        const formData = new FormData();
        formData.append('scenario', scenarioName);
        formData.append('duration_seconds', String(Math.max(0, Math.round((Date.now() - recordingStartedAt) / 1000))));
        formData.append('audio', audio, 'respuesta.webm');
        statusElement.textContent = 'Guardando tu practica...';
        try {
            const response = await fetch('/api/sessions', {
                method: 'POST',
                body: formData,
                headers: csrfToken ? { 'X-CSRFToken': csrfToken } : {},
            });
            if (!response.ok) throw new Error('No se pudo guardar la sesion.');
            const result = await response.json();
            window.location.href = result.redirect;
        } catch (error) {
            statusElement.textContent = 'No pudimos guardar la practica. Intentalo de nuevo.';
        }
    }

    function startTimer() {
        clearInterval(timerId);
        timerId = setInterval(function () {
            elapsedSeconds += 1;
            renderTime();
            if (elapsedSeconds >= totalSeconds) {
                stopRecording();
                statusElement.textContent = 'Tiempo cumplido. ¡Buen trabajo!';
                coachBubble.textContent = '¡Buen trabajo!';
            }
        }, 1000);
    }

    async function startRecording() {
        if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
            statusElement.textContent = 'Tu navegador no permite grabar audio aqui.';
            recordingNote.textContent = 'Puedes practicar en voz alta y continuar cuando quieras.';
            return;
        }
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            audioChunks = [];
            mediaRecorder = new MediaRecorder(stream);
            mediaRecorder.addEventListener('dataavailable', function (event) { audioChunks.push(event.data); });
            mediaRecorder.addEventListener('stop', function () {
                stream.getTracks().forEach(function (track) { track.stop(); });
                if (audioChunks.length) saveSession();
            });
            mediaRecorder.start();
            recordingStartedAt = Date.now();
            elapsedSeconds = 0;
            renderTime();
            setRecordingState(true);
            startTimer();
        } catch (error) {
            statusElement.textContent = 'Necesitamos permiso para escuchar tu respuesta.';
            recordingNote.textContent = 'Activa el microfono del navegador para comenzar.';
        }
    }

    recordButton.addEventListener('click', function () {
        if (mediaRecorder?.state === 'recording') stopRecording();
        else startRecording();
    });

    cancelButton.addEventListener('click', function () {
        stopRecording(false);
        elapsedSeconds = 0;
        renderTime();
        statusElement.textContent = 'Listo cuando tu lo estés';
        coachBubble.textContent = '¿Listo para empezar?';
        recordingNote.innerHTML = '<span aria-hidden="true">●</span> Solo se grabara tu voz para darte retroalimentacion.';
    });

    renderTime();
})();