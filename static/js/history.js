(function () {
    'use strict';
    const filter = document.querySelector('[data-session-filter]');
    const sessionList = document.querySelector('.session-list');
    const chart = document.querySelector('.chart-area svg');
    const chartLabels = document.querySelector('.chart-x-labels');
    const chartCallout = document.querySelector('.chart-callout');
    const scenarioIcons = { entrevista: '↗', presentacion: '▱', exposicion: '◫' };

    function formatDate(value) {
        const date = new Date(value.replace(' ', 'T') + 'Z');
        return {
            day: date.toLocaleDateString('es', { day: '2-digit' }),
            month: date.toLocaleDateString('es', { month: 'short' }).replace('.', '').toUpperCase(),
        };
    }

    function renderChart(scores) {
        if (!chart) return;
        const points = scores.map(function (score, index) {
            return `${index * 140} ${230 - (score * 1.78)}`;
        });
        const line = points.join(' L');
        chart.querySelector('.chart-fill').setAttribute('d', `M${line} L700 230 L0 230 Z`);
        chart.querySelector('.chart-line').setAttribute('d', `M${line}`);
        chart.querySelectorAll('circle').forEach(function (circle, index) {
            const [x, y] = points[index].split(' ');
            circle.setAttribute('cx', x);
            circle.setAttribute('cy', y);
        });
        chartLabels.innerHTML = scores.map(function (_, index) {
            const date = new Date();
            date.setDate(date.getDate() - (5 - index) * 7);
            return `<span>${date.toLocaleDateString('es', { day: 'numeric', month: 'short' }).replace('.', '')}</span>`;
        }).join('');
    }

    function renderSessions(sessions) {
        if (!sessionList) return;
        sessionList.innerHTML = sessions.length ? sessions.map(function (item) {
            const date = formatDate(item.created_at);
            return `<a class="session-row" data-session-type="${item.type}" href="/results?session_id=${item.id}">
                <span class="session-date"><strong>${date.day}</strong><span>${date.month}</span></span>
                <span class="session-icon">${scenarioIcons[item.type] || '◉'}</span>
                <span class="session-info"><strong>${item.scenario}</strong><span>${item.duration}s de practica</span></span>
                <span class="session-score"><strong>${item.score}</strong><span>/ 100</span></span><span class="session-arrow">→</span>
            </a>`;
        }).join('') : '<p class="empty-sessions">Aun no tienes sesiones. Completa tu primera practica para ver tu progreso aqui.</p>';
    }

    function applyFilter() {
        const rows = document.querySelectorAll('[data-session-type]');
        rows.forEach(function (row) {
            row.hidden = filter.value !== 'all' && row.dataset.sessionType !== filter.value;
        });
    }

    fetch('/api/history')
        .then(function (response) { return response.ok ? response.json() : Promise.reject(response); })
        .then(function (data) {
            renderChart(data.scores);
            renderSessions(data.sessions);
            chartCallout.querySelector('strong').textContent = `${data.change >= 0 ? '+' : ''}${data.change} pts`;
            chartCallout.querySelector('span').textContent = data.sessions.length ? 'desde que empezaste' : 'sin sesiones aun';
            filter?.addEventListener('change', applyFilter);
        })
        .catch(function () {
            if (sessionList) sessionList.innerHTML = '<p class="empty-sessions">No pudimos cargar tu historial. Recarga la pagina para intentarlo de nuevo.</p>';
        });
})();