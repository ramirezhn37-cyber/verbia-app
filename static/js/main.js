(function () {
    'use strict';

    const root = document.documentElement;
    const themeToggle = document.querySelector('[data-theme-toggle]');
    const menuToggle = document.querySelector('[data-menu-toggle]');
    const navLinks = document.querySelector('#nav-links');

    function setTheme(theme) {
        root.dataset.theme = theme;
        localStorage.setItem('verbai-theme', theme);
        document.querySelectorAll('img[src*="/img/logo"]').forEach(function (logo) {
            logo.src = logo.src.replace(/logo(?:-dark)?\.svg/, theme === 'dark' ? 'logo-dark.svg' : 'logo.svg');
        });
        if (themeToggle) {
            const isDark = theme === 'dark';
            themeToggle.setAttribute('aria-pressed', String(isDark));
            themeToggle.setAttribute('aria-label', isDark ? 'Activar modo claro' : 'Activar modo oscuro');
        }
    }

    const savedTheme = localStorage.getItem('verbai-theme');
    const preferredTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    setTheme(savedTheme || preferredTheme);

    themeToggle?.addEventListener('click', function () {
        setTheme(root.dataset.theme === 'dark' ? 'light' : 'dark');
    });

    menuToggle?.addEventListener('click', function () {
        const isOpen = navLinks.classList.toggle('is-open');
        menuToggle.setAttribute('aria-expanded', String(isOpen));
        menuToggle.setAttribute('aria-label', isOpen ? 'Cerrar menu' : 'Abrir menu');
    });

    navLinks?.querySelectorAll('a').forEach(function (link) {
        link.addEventListener('click', function () {
            navLinks.classList.remove('is-open');
            menuToggle?.setAttribute('aria-expanded', 'false');
        });
    });

    const avatarChoices = document.querySelectorAll('[data-avatar-choice]');
    avatarChoices.forEach(function (choice) {
        choice.addEventListener('change', function () {
            document.querySelectorAll('.avatar-style-choice').forEach(function (label) {
                label.classList.toggle('is-selected', label.querySelector('[data-avatar-choice]').checked);
            });
        });
    });

    const scenarioCarousel = document.querySelector('[data-scenario-carousel]');
    if (scenarioCarousel) {
        const track = scenarioCarousel.querySelector('[data-scenario-track]');
        const previousButton = scenarioCarousel.querySelector('[data-scenario-previous]');
        const nextButton = scenarioCarousel.querySelector('[data-scenario-next]');

        function updateScenarioControls() {
            const maxScroll = track.scrollWidth - track.clientWidth;
            previousButton.disabled = track.scrollLeft <= 1;
            nextButton.disabled = track.scrollLeft >= maxScroll - 1;
        }

        previousButton.addEventListener('click', function () {
            track.scrollBy({ left: -track.clientWidth * 0.85, behavior: 'smooth' });
        });
        nextButton.addEventListener('click', function () {
            track.scrollBy({ left: track.clientWidth * 0.85, behavior: 'smooth' });
        });
        track.addEventListener('scroll', updateScenarioControls, { passive: true });
        window.addEventListener('resize', updateScenarioControls);
        updateScenarioControls();
    }

    const authTabs = document.querySelectorAll('[data-auth-tab]');
    const authSwitch = document.querySelector('[data-auth-switch]');
    const authTitle = document.querySelector('[data-auth-title]');
    const authSubtitle = document.querySelector('[data-auth-subtitle]');
    const authSubmit = document.querySelector('[data-auth-submit]');
    const authForm = document.querySelector('[data-auth-form]');
    const authStatus = document.querySelector('[data-auth-status]');
    const authModeInput = document.querySelector('[data-auth-mode]');
    let authMode = 'login';

    function setAuthMode(mode) {
        authMode = mode;
        const isRegister = mode === 'register';
        if (authModeInput) authModeInput.value = mode;
        document.querySelectorAll('[data-register-only]').forEach(function (element) {
            element.hidden = !isRegister;
        });
        document.querySelectorAll('[data-login-only]').forEach(function (element) {
            element.hidden = isRegister;
        });
        document.querySelector('.field-name')?.toggleAttribute('hidden', !isRegister);
        document.querySelector('#name')?.toggleAttribute('required', !isRegister);
        if (authTitle) authTitle.textContent = isRegister ? 'Crea tu espacio.' : 'Bienvenido de vuelta.';
        if (authSubtitle) authSubtitle.textContent = isRegister ? 'Empieza a practicar tu voz con Verbai.' : 'Continua entrenando tu voz con Verbai.';
        if (authSubmit) authSubmit.innerHTML = isRegister ? 'Crear mi cuenta <span aria-hidden="true">↗</span>' : 'Entrar a Verbai <span aria-hidden="true">↗</span>';
        authSwitch.innerHTML = isRegister ? '¿Ya tienes cuenta? <button type="button" data-auth-switch>Iniciar sesion</button>' : '¿Todavia no tienes cuenta? <button type="button" data-auth-switch>Crear una cuenta</button>';
        if (authStatus) authStatus.textContent = '';
        document.querySelectorAll('[data-auth-tab]').forEach(function (tab) {
            const active = tab.dataset.authTab === mode;
            tab.classList.toggle('is-active', active);
            tab.setAttribute('aria-selected', String(active));
        });
        authSwitch.querySelector('[data-auth-switch]').addEventListener('click', function () {
            setAuthMode(isRegister ? 'login' : 'register');
        });
    }

    authTabs.forEach(function (tab) {
        tab.addEventListener('click', function () { setAuthMode(tab.dataset.authTab); });
    });

    if (authTabs.length && authModeInput) setAuthMode(authModeInput.value || 'login');

    authForm?.addEventListener('submit', function (event) {
        if (authStatus) {
            authStatus.textContent = authMode === 'register'
                ? 'Creando tu espacio...'
                : 'Abriendo tu espacio...';
        }
    });

    const notificationSettings = document.querySelector('[data-notification-settings]');
    if (notificationSettings) {
        const userId = notificationSettings.dataset.userId;
        notificationSettings.querySelectorAll('[data-notification-setting]').forEach(function (toggle) {
            const storageKey = 'verbai-notification-' + userId + '-' + toggle.dataset.notificationSetting;
            const savedPreference = localStorage.getItem(storageKey);

            if (savedPreference !== null) {
                toggle.checked = savedPreference === 'true';
            }

            toggle.addEventListener('change', function () {
                localStorage.setItem(storageKey, String(toggle.checked));
            });
        });
    }

    async function inlineVerboAssets() {
        const images = Array.from(document.querySelectorAll('[data-verbo-stage] img.verbo-image'));
        await Promise.all(images.map(async function (image) {
            try {
                const response = await fetch(image.src);
                if (!response.ok) return;
                const svgDocument = new DOMParser().parseFromString(await response.text(), 'image/svg+xml');
                const svg = svgDocument.documentElement;
                if (svg.localName !== 'svg' || svgDocument.querySelector('parsererror')) return;
                svg.setAttribute('class', 'verbo-image');
                svg.setAttribute('role', 'img');
                svg.setAttribute('aria-label', image.alt || 'Verbo');
                image.replaceWith(document.importNode(svg, true));
            } catch (error) {
                return;
            }
        }));
    }

    inlineVerboAssets().finally(function () {
        const mascotStages = document.querySelectorAll('[data-verbo-stage]');

        mascotStages.forEach(function (mascotStage) {
        const pupils = Array.from(mascotStage.querySelectorAll('.pupil-left, .pupil-right, .verbo-eye-left, .verbo-eye-right')).filter(Boolean);

        if (!pupils.length) return;

        const resetEyes = function () {
            pupils.forEach(function (pupil) {
                pupil.setAttribute('transform', 'translate(0 0)');
            });
        };

        const applyLook = function (targetX, targetY) {
            const rect = mascotStage.getBoundingClientRect();
            const centerX = rect.left + rect.width / 2;
            const centerY = rect.top + rect.height / 2;
            const dx = (targetX - centerX) / (window.innerWidth / 2 || 1);
            const dy = (targetY - centerY) / (window.innerHeight / 2 || 1);
            const offsetX = Math.max(-5, Math.min(5, dx * 5));
            const offsetY = Math.max(-4, Math.min(4, dy * 4));

            pupils.forEach(function (pupil) {
                pupil.setAttribute('transform', 'translate(' + offsetX + ' ' + offsetY + ')');
            });
        };

        const activeInputLook = function (event) {
            const target = event.target.closest('input, textarea, select');
            if (!target) return;
            const fieldRect = target.getBoundingClientRect();
            applyLook(fieldRect.left + fieldRect.width / 2, fieldRect.top + fieldRect.height / 2);
        };

        document.addEventListener('focusin', activeInputLook);
        document.addEventListener('focusout', function (event) {
            if (event.target.matches('input, textarea, select')) {
                const activeElement = document.activeElement;
                if (!activeElement || !activeElement.matches('input, textarea, select')) {
                    resetEyes();
                }
            }
        });

        document.addEventListener('pointermove', function (event) {
            applyLook(event.clientX, event.clientY);
        });
        });
    });

    const dashboardMenu = document.querySelector('[data-dashboard-menu]');
    const dashboardSidebar = document.querySelector('#dashboard-sidebar');
    dashboardMenu?.addEventListener('click', function () {
        const isOpen = dashboardSidebar.classList.toggle('is-open');
        dashboardMenu.setAttribute('aria-expanded', String(isOpen));
    });

    document.querySelectorAll('[data-fill]').forEach(function (bar) {
        const value = Number(bar.dataset.fill || 0);
        const width = Math.max(0, Math.min(100, value));
        bar.style.width = width + '%';
    });

    document.querySelectorAll('[data-current-year]').forEach(function (element) {
        element.textContent = new Date().getFullYear();
    });
})();