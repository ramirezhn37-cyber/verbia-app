# Código fuente del acceso de Verbai

Este documento reúne el template de acceso, el template base, las funciones JavaScript que usa esa vista, los estilos del formulario y la ruta Flask de inicio de sesión/registro. Se recopila del código del proyecto; no incluye secretos ni credenciales.

> Para ejecutar esta vista se necesitan Flask/Jinja, la aplicación y base de datos del proyecto, `static/css/styles.css`, `static/js/main.js` y los recursos estáticos. Este archivo es una copia de referencia para compartir, no reemplaza esos componentes. El botón de Google depende además del flujo OAuth definido en la aplicación.

## `templates/login.html`
```html
{% extends "base.html" %}

{% block title %}Verbai | Acceso{% endblock %}

{% block content %}
<main class="auth-page">
    <div class="auth-decoration auth-decoration-top" aria-hidden="true"></div>
    <div class="auth-decoration auth-decoration-bottom" aria-hidden="true"></div>
    <a class="auth-brand" href="{{ url_for('landing') }}" aria-label="Volver al inicio de Verbai">
        <img src="{{ url_for('static', filename='img/logo.svg') }}" alt="Verbai">
    </a>
    <a class="auth-back" href="{{ url_for('landing') }}"><span aria-hidden="true">â†</span> Volver al inicio</a>

    <section class="auth-layout" aria-labelledby="auth-title">
        <div class="auth-card reveal">
            <div class="auth-heading">
                <p class="eyebrow"><span class="eyebrow-dot"></span> Tu espacio de practica</p>
                <h1 id="auth-title" data-auth-title>Bienvenido de vuelta.</h1>
                <p data-auth-subtitle>Continua entrenando tu voz con Verbai.</p>
            </div>

            <div class="auth-tabs" role="tablist" aria-label="Tipo de acceso">
                <button class="auth-tab is-active" type="button" role="tab" aria-selected="true" data-auth-tab="login">Iniciar sesion</button>
                <button class="auth-tab" type="button" role="tab" aria-selected="false" data-auth-tab="register">Crear cuenta</button>
            </div>

            <div class="auth-social">
                <a class="button button-outline button-google" href="{{ url_for('login_google') }}" aria-label="Iniciar sesion con Google">
                    <span class="google-icon" aria-hidden="true">G</span>
                    Continuar con Google
                </a>
            </div>

            <div class="auth-divider" aria-hidden="true"><span>o</span></div>

            <form class="auth-form" data-auth-form action="{{ url_for('login') }}" method="post">
                <input type="hidden" name="mode" value="{{ auth_mode|default('login') }}" data-auth-mode>
                <div class="field field-name" hidden>
                    <label for="name">Nombre</label>
                    <input id="name" name="name" type="text" autocomplete="name" placeholder="Tu nombre">
                </div>
                <div class="field">
                    <label for="email">Correo electronico</label>
                    <input id="email" name="email" type="email" autocomplete="email" placeholder="tu@correo.com" required>
                </div>
                <div class="field">
                    <div class="field-label-row">
                        <label for="password">Contrasena</label>
                        <a href="{{ url_for('forgot_password') }}" data-login-only>Â¿La olvidaste?</a>
                    </div>
                    <input id="password" name="password" type="password" autocomplete="current-password" placeholder="Minimo 8 caracteres" minlength="8" required>
                </div>
                <label class="check-row" data-register-only hidden>
                    <input type="checkbox" required>
                    <span>Acepto crear mi espacio de practica en Verbai.</span>
                </label>
                <button class="button button-coral auth-submit" type="submit" data-auth-submit>Entrar a Verbai <span aria-hidden="true">â†—</span></button>
                {% with messages = get_flashed_messages(with_categories=true) %}
                    {% if messages %}
                        {% for category, message in messages %}<p class="auth-status auth-status-{{ category }}" role="status">{{ message }}</p>{% endfor %}
                    {% else %}<p class="auth-status" data-auth-status role="status" aria-live="polite"></p>{% endif %}
                {% endwith %}
            </form>

            <p class="auth-switch" data-auth-switch-copy>Â¿Todavia no tienes cuenta? <button type="button" data-auth-switch>Crear una cuenta</button></p>
        </div>

        <aside class="auth-companion reveal reveal-delay" aria-label="Verbo, asistente de Verbai">
            <div class="companion-kicker"><span class="live-dot"></span> Tu asistente de practica</div>
            <div class="companion-message">Hola, me alegra<br><em>verte por aqui.</em></div>
            <div class="companion-verbo" data-verbo-stage>
                <img class="verbo-image" src="{{ url_for('static', filename='img/verbo.svg') }}" alt="Verbo saludando">
                <svg class="verbo-image verbo-legacy" aria-hidden="true" viewBox="0 0 800 800" xmlns="http://www.w3.org/2000/svg">
                    <defs>
                        <filter id="soft-shadow" x="-30%" y="-30%" width="160%" height="160%"><feDropShadow dx="0" dy="10" stdDeviation="12" flood-color="#1E1B4B" flood-opacity="0.15"/></filter>
                        <filter id="eye-shadow" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="0" dy="4" stdDeviation="5" flood-color="#1E1B4B" flood-opacity="0.10"/></filter>
                    </defs>
                    <g id="verbai-mascot">
                        <path d="M 215 420 Q 180 435 190 465 Q 205 480 225 450 Z" fill="#FF6B6B" filter="url(#soft-shadow)"/>
                        <path d="M 585 410 C 625 365 650 380 635 415 C 620 445 575 440 575 430 Z" fill="#FF6B6B" filter="url(#soft-shadow)"/>
                        <circle cx="400" cy="400" r="190" fill="#FF6B6B" filter="url(#soft-shadow)"/>
                        <path d="M 220 440 A 190 190 0 0 0 580 440 A 190 190 0 0 1 220 440 Z" fill="#1E1B4B" opacity="0.08"/>
                        <path d="M 264 267 Q 396 204 542 258 L 535 279 Q 398 230 272 286 Z" fill="#F4B544" stroke="#1E1B4B" stroke-width="9" stroke-linejoin="round"/>
                        <g transform="rotate(-14 401 195)" filter="url(#soft-shadow)">
                            <path d="M 290 184 L 452 128 L 478 220 L 310 246 Z" fill="#FF873F" stroke="#1E1B4B" stroke-width="11" stroke-linejoin="round"/>
                            <path d="M 290 184 L 353 163 L 369 237 L 310 246 Z" fill="#F5A24C" stroke="#1E1B4B" stroke-width="7"/>
                            <path d="M 301 187 L 350 170 M 306 199 L 353 183 M 310 213 L 356 197 M 314 228 L 359 212" fill="none" stroke="#E45E2D" stroke-width="5"/>
                            <ellipse cx="466" cy="174" rx="19" ry="48" fill="#F16E35" stroke="#1E1B4B" stroke-width="10"/>
                            <ellipse cx="465" cy="174" rx="10" ry="33" fill="#FFF1DD" stroke="#1E1B4B" stroke-width="5"/>
                            <path d="M 326 238 L 318 269 Q 319 279 330 274 L 349 245 Z" fill="#E96532" stroke="#1E1B4B" stroke-width="8" stroke-linejoin="round"/>
                            <path d="M 303 181 L 351 164 L 356 178 L 307 195 Z" fill="#FFC078" opacity=".8" stroke="none"/>
                        </g>
                        <circle class="eye eye-left" cx="335" cy="375" r="62" fill="#FFFFFF" filter="url(#eye-shadow)"/>
                        <circle class="pupil pupil-left" cx="348" cy="375" r="26" fill="#1E1B4B"/><circle cx="340" cy="363" r="9" fill="#FFFFFF"/><circle cx="356" cy="383" r="4" fill="#FFFFFF"/>
                        <circle class="eye eye-right" cx="465" cy="375" r="62" fill="#FFFFFF" filter="url(#eye-shadow)"/>
                        <circle class="pupil pupil-right" cx="452" cy="375" r="26" fill="#1E1B4B"/><circle cx="444" cy="363" r="9" fill="#FFFFFF"/><circle cx="460" cy="383" r="4" fill="#FFFFFF"/>
                        <path d="M 378 455 Q 400 482 422 455" fill="none" stroke="#1E1B4B" stroke-width="11" stroke-linecap="round"/>
                    </g>
                </svg>
                <div class="verbo-shadow"></div>
            </div>
            <p class="companion-tip">Cada practica empieza<br>con un primer intento.</p>
        </aside>
    </section>
</main>
{% endblock %}
```

## `templates/base.html` (envoltura y recursos compartidos)
```html
<!doctype html>
<html lang="es" data-theme="light">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="description" content="Verbai: practica tu expresion oral y habla con mas confianza.">
    <title>{% block title %}Verbai | Habla con confianza{% endblock %}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Poppins:wght@600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/styles.css') }}">
    {% block head %}{% endblock %}
</head>
<body>
    {% block content %}{% endblock %}
    <script src="{{ url_for('static', filename='js/main.js') }}" defer></script>
    {% block scripts %}{% endblock %}
</body>
</html>
```

## `static/js/main.js` (tema compartido en la página de acceso)
```javascript
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
```

## `static/js/main.js` (cambio entre iniciar sesión y crear cuenta)
```javascript
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
        if (authSubmit) authSubmit.innerHTML = isRegister ? 'Crear mi cuenta <span aria-hidden="true">â†—</span>' : 'Entrar a Verbai <span aria-hidden="true">â†—</span>';
        authSwitch.innerHTML = isRegister ? 'Â¿Ya tienes cuenta? <button type="button" data-auth-switch>Iniciar sesion</button>' : 'Â¿Todavia no tienes cuenta? <button type="button" data-auth-switch>Crear una cuenta</button>';
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

```

## `static/js/main.js` (carga e interacción del asistente Verbo)
```javascript
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

```

## `app.py` (validación de correo utilizada por el endpoint)
```python
def is_valid_email(value):
    return bool(EMAIL_RE.match(value or ""))


```

## `app.py` (inicio de sesión y registro)
```python
@app.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute", methods=["POST"])
def login():
    if request.method == "POST":
        mode = request.form.get("mode", "login")
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        name = request.form.get("name", "").strip()

        if not email or not password:
            flash("Completa tu correo y contraseÃ±a.", "error")
            return render_template("login.html", auth_mode=mode), 400

        if not is_valid_email(email):
            flash("Escribe un correo vÃ¡lido.", "error")
            return render_template("login.html", auth_mode=mode), 400

        connection = get_db()
        user = connection.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()

        if mode == "register":
            if not name:
                flash("Escribe tu nombre para crear la cuenta.", "error")
                return render_template("login.html", auth_mode=mode), 400
            if len(password) < 8:
                flash("La contraseÃ±a debe tener al menos 8 caracteres.", "error")
                return render_template("login.html", auth_mode=mode), 400
            if user:
                flash("Ese correo ya tiene una cuenta.", "error")
                return render_template("login.html", auth_mode=mode), 409

            cursor = connection.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                (name, email, generate_password_hash(password)),
            )
            connection.commit()
            user = connection.execute(
                "SELECT * FROM users WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()

        elif not user or not check_password_hash(user["password_hash"], password):
            flash("Correo o contraseÃ±a incorrectos.", "error")
            return render_template("login.html", auth_mode=mode), 401

        session.clear()
        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        session.permanent = True
        return redirect(url_for("panel"))

    return render_template("login.html")


```

## `static/css/styles.css` (estilos de la página de acceso)
```css
.auth-page { position: relative; display: grid; min-height: 100vh; place-items: center; overflow: hidden; background: var(--bg); }
.auth-page::before { position: absolute; inset: 0; background-image: linear-gradient(var(--line) 1px, transparent 1px), linear-gradient(90deg, var(--line) 1px, transparent 1px); background-size: 70px 70px; opacity: .3; content: ""; mask-image: linear-gradient(135deg, black, transparent 70%); }
.auth-brand, .auth-back { position: absolute; z-index: 2; top: 30px; }
.auth-brand { left: 34px; }
.auth-brand img { width: 125px; }
.auth-back { right: 34px; color: var(--ink-soft); font-size: 12px; font-weight: 600; }
.auth-back span { margin-right: 8px; color: var(--coral-deep); font-size: 18px; }
.auth-decoration { position: absolute; border-radius: 50%; border: 1px solid var(--coral); opacity: .25; }
.auth-decoration-top { top: -180px; right: -120px; width: 480px; height: 480px; }
.auth-decoration-bottom { bottom: -250px; left: -180px; width: 550px; height: 550px; border-color: var(--ink); }
.auth-layout { position: relative; z-index: 1; display: grid; grid-template-columns: minmax(330px, 430px) minmax(260px, 360px); align-items: center; gap: 90px; width: min(92%, 870px); padding: 95px 0 50px; }
.auth-card { padding: 42px; border: 1px solid var(--line); border-radius: 18px; background: var(--surface); box-shadow: var(--shadow); }
.auth-heading .eyebrow { margin-bottom: 18px; }
.auth-heading h1 { margin-bottom: 10px; font-size: clamp(29px, 4vw, 42px); line-height: 1.12; }
.auth-heading > p:last-child { margin-bottom: 30px; color: var(--ink-soft); font-size: 13px; }
.auth-tabs { display: grid; grid-template-columns: 1fr 1fr; gap: 5px; margin-bottom: 26px; padding: 5px; border-radius: 11px; background: var(--surface-soft); }
.auth-tab { min-height: 38px; border: 0; border-radius: 8px; background: transparent; color: var(--ink-soft); cursor: pointer; font-size: 12px; font-weight: 600; }
.auth-tab.is-active { background: var(--surface); color: var(--ink); box-shadow: 0 3px 9px rgba(30, 27, 75, .08); }
.auth-social { margin-bottom: 16px; }
.button-google { width: 100%; border-color: var(--line); background: var(--surface); color: var(--ink); }
.google-icon { display: inline-grid; width: 20px; height: 20px; place-items: center; border-radius: 50%; background: linear-gradient(135deg, #4285f4, #34a853 50%, #fbbc05 75%, #ea4335 100%); color: #fff; font-size: 10px; font-weight: 700; }
.auth-divider { position: relative; margin: 2px 0 18px; text-align: center; color: var(--ink-soft); font-size: 10px; letter-spacing: .12em; text-transform: uppercase; }
.auth-divider::before { content: ""; position: absolute; left: 0; right: 0; top: 50%; height: 1px; background: var(--line); }
.auth-divider span { position: relative; z-index: 1; display: inline-block; padding: 0 10px; background: var(--surface); }
.auth-form { display: grid; gap: 18px; }
.field { display: grid; gap: 8px; }
.field label, .field-label-row { color: var(--ink); font-size: 11px; font-weight: 600; }
.field-label-row { display: flex; justify-content: space-between; }
.field-label-row a { color: var(--coral-deep); font-weight: 500; }
.field input { width: 100%; min-height: 48px; padding: 0 14px; border: 1px solid var(--line); border-radius: 10px; outline: 0; background: var(--bg); color: var(--ink); font: 13px var(--font-body); transition: border .2s ease, box-shadow .2s ease; }
.field input::placeholder { color: var(--ink-soft); opacity: .65; }
.field input:focus { border-color: var(--coral); box-shadow: 0 0 0 4px var(--coral-soft); }
.check-row { display: flex; align-items: flex-start; gap: 9px; color: var(--ink-soft); font-size: 11px; line-height: 1.5; }
.check-row input { accent-color: var(--coral); margin-top: 2px; }
.auth-submit { width: 100%; margin-top: 3px; border: 0; cursor: pointer; }
.auth-status { min-height: 16px; margin: -5px 0 0; color: var(--coral-deep); font-size: 11px; text-align: center; }
.auth-switch { margin: 25px 0 0; color: var(--ink-soft); font-size: 11px; text-align: center; }
.auth-switch button { padding: 0; border: 0; background: none; color: var(--coral-deep); cursor: pointer; font-weight: 600; }
.auth-companion { position: relative; min-height: 440px; }
.companion-kicker { display: flex; align-items: center; gap: 10px; margin-bottom: 26px; color: var(--ink-soft); font-size: 10px; font-weight: 600; letter-spacing: .09em; text-transform: uppercase; }
.companion-message { margin-bottom: 28px; font: 600 clamp(25px, 4vw, 39px)/1.15 var(--font-display); letter-spacing: -.03em; }
.companion-message em { color: var(--coral-deep); font-style: normal; }
.companion-verbo { position: relative; display: grid; place-items: center; min-height: 220px; }
.verbo-image { display: block; width: min(72vw, 260px); max-width: 260px; height: auto; filter: drop-shadow(0 18px 28px rgba(125, 72, 77, .18)); cursor: pointer; }
.verbo-legacy { display: none; }
.verbo-hand-icon { position: absolute; top: 26px; right: 40px; color: var(--coral-deep); font-size: 28px; transform: rotate(15deg); animation: wave 1.8s ease-in-out infinite; }
.companion-verbo .verbo-shadow { position: absolute; left: 50%; bottom: -8px; width: 150px; height: 18px; border-radius: 50%; background: rgba(30, 27, 75, .12); filter: blur(8px); transform: translateX(-50%); }
[data-verbo-stage] { position: relative; display: grid; place-items: center; transition: transform .2s ease; }
[data-verbo-stage]:hover { transform: translateY(-2px); }
[data-verbo-stage] .pupil { transform-origin: center; transition: transform .12s ease-out; }
.panel-mascot-card { display: flex; align-items: center; justify-content: space-between; gap: 24px; max-width: 1060px; margin: 0 auto 52px; padding: 20px 28px; border: 1px solid var(--line); border-radius: 10px; background: linear-gradient(105deg, var(--surface-soft), var(--coral-soft)); }
.panel-mascot-copy { flex: 1; }
.panel-mascot-copy .eyebrow { margin-bottom: 12px; }
.panel-mascot-copy h2 { max-width: 620px; margin: 0 0 8px; font-size: clamp(20px, 2vw, 27px); line-height: 1.25; }
.panel-mascot-copy > span { color: var(--ink-soft); font-size: 12px; }
.panel-mascot-figure { display: grid; place-items: center; min-width: 140px; }
.panel-mascot-figure .verbo-image { width: 128px; max-width: 128px; }
.companion-tip { margin: 25px 0 0 35px; color: var(--ink-soft); font-size: 12px; line-height: 1.7; }

```
