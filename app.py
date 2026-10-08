import hashlib
import json
import logging
import os
import re
import secrets
import smtplib
import sqlite3
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from functools import wraps

from dotenv import load_dotenv
from flask import (
    Flask, abort, flash, g, jsonify, redirect,
    render_template, request, send_from_directory, session, url_for,
)
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
from groq import Groq
from werkzeug.security import check_password_hash, generate_password_hash

load_dotenv()

# ---------------------------------------------------------------- Configuración
app = Flask(__name__)

secret_key = os.environ.get("VERBAI_SECRET_KEY") or os.environ.get("SECRET_KEY")
if not secret_key:
    secret_key = secrets.token_hex(32)
    os.environ["VERBAI_SECRET_KEY"] = secret_key

IS_PRODUCTION = os.environ.get("FLASK_ENV") == "production"

app.config.update(
    SECRET_KEY=secret_key,
    DATABASE_URL=os.environ.get("DATABASE_URL", "sqlite:///verbai.db"),
    HOST=os.environ.get("HOST", "0.0.0.0"),
    PORT=int(os.environ.get("PORT", "5000")),
    PUBLIC_BASE_URL=os.environ.get("PUBLIC_BASE_URL", "http://localhost:5000"),
    GOOGLE_CLIENT_ID=os.environ.get("GOOGLE_CLIENT_ID"),
    GOOGLE_CLIENT_SECRET=os.environ.get("GOOGLE_CLIENT_SECRET"),
    GROQ_API_KEY=os.environ.get("GROQ_API_KEY"),
    SMTP_HOST=os.environ.get("SMTP_HOST"),
    SMTP_PORT=int(os.environ.get("SMTP_PORT", "587")),
    SMTP_USER=os.environ.get("SMTP_USER"),
    SMTP_PASSWORD=os.environ.get("SMTP_PASSWORD"),
    SMTP_FROM=os.environ.get("SMTP_FROM", os.environ.get("SMTP_USER")),
    MAX_CONTENT_LENGTH=30 * 1024 * 1024,          # 30 MB
    SESSION_COOKIE_SECURE=IS_PRODUCTION,          # requiere HTTPS en prod
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    PERMANENT_SESSION_LIFETIME=timedelta(days=7),
)

app.config["GOOGLE_REDIRECT_URI"] = os.environ.get(
    "GOOGLE_REDIRECT_URI",
    f"{app.config['PUBLIC_BASE_URL']}/auth/google/callback",
)

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

csrf = CSRFProtect(app)
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=[],
    storage_uri=os.environ.get("RATELIMIT_STORAGE_URI", "memory://"),
)

UPLOAD_DIR = os.environ.get("UPLOAD_DIR", os.path.join(app.root_path, "uploads"))
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ---------------------------------------------------------------- Escenarios
SCENARIOS = {
    "entrevista": {
        "name": "Entrevista de trabajo",
        "category": "Laboral",
        "type": "entrevista",
        "title": "Cuéntame sobre ti.",
        "prompt": "Imagina que estás en una entrevista. Preséntate brevemente y cuéntame qué te motiva profesionalmente.",
    },
    "simulacion-profesional": {
        "name": "Simulación profesional",
        "category": "Laboral",
        "type": "entrevista",
        "title": "Resuelve una situación profesional.",
        "prompt": "Explica cómo responderías a un reto habitual en tu futuro trabajo y qué decisiones tomarías.",
    },
    "presentacion": {
        "name": "Presentación",
        "category": "Académica",
        "type": "presentacion",
        "title": "Presenta una idea con claridad.",
        "prompt": "Organiza una presentación breve: introduce tu idea, desarrolla sus puntos principales y cierra con una conclusión.",
    },
    "exposicion": {
        "name": "Exposición",
        "category": "Académica",
        "type": "exposicion",
        "title": "Explica un tema.",
        "prompt": "Explica un tema que conozcas como si estuvieras frente a tu clase, usando ejemplos sencillos.",
    },
    "preguntas": {
        "name": "Preguntas y respuestas",
        "category": "Académica",
        "type": "exposicion",
        "title": "Responde con seguridad.",
        "prompt": "Responde una pregunta difícil sobre tus estudios y explica paso a paso cómo construyes tu respuesta.",
    },
    "tema": {
        "name": "Explicación de tema",
        "category": "Académica",
        "type": "exposicion",
        "title": "Haz sencillo lo complejo.",
        "prompt": "Explica un concepto de tus estudios con tus propias palabras, como si se lo contaras a alguien que empieza.",
    },
    "general": {
        "name": "Comunicación general",
        "category": "Académica",
        "type": "exposicion",
        "title": "Comparte lo que piensas.",
        "prompt": "Habla durante un minuto sobre una idea, experiencia o tema que te interese.",
    },
}
SCENARIO_TYPES = {v["name"]: v["type"] for v in SCENARIOS.values()}
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ---------------------------------------------------------------- Base de datos
def get_db():
    if "db" not in g:
        database_url = app.config["DATABASE_URL"]
        if not database_url.startswith("sqlite:///"):
            raise RuntimeError(
                "DATABASE_URL requiere el adaptador PostgreSQL antes de usar una base externa."
            )
        g.db = sqlite3.connect(
            database_url.removeprefix("sqlite:///"),
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    connection = get_db()
    connection.execute(
        """CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            avatar_url TEXT,
            avatar_style TEXT NOT NULL DEFAULT 'default',
            status TEXT NOT NULL DEFAULT 'active',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )"""
    )
    user_columns = {
        row[1] for row in connection.execute("PRAGMA table_info(users)")
    }
    if "avatar_url" not in user_columns:
        connection.execute("ALTER TABLE users ADD COLUMN avatar_url TEXT")
    if "avatar_style" not in user_columns:
        connection.execute(
            "ALTER TABLE users ADD COLUMN avatar_style TEXT NOT NULL DEFAULT 'default'"
        )
    if "status" not in user_columns:
        connection.execute(
            "ALTER TABLE users ADD COLUMN status TEXT NOT NULL DEFAULT 'active'"
        )
    connection.execute(
        """CREATE TABLE IF NOT EXISTS practice_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            scenario TEXT NOT NULL,
            duration_seconds INTEGER NOT NULL DEFAULT 0,
            score INTEGER NOT NULL DEFAULT 0,
            audio_path TEXT,
            transcript TEXT,
            analysis_json TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )"""
    )
    connection.execute(
        """CREATE TABLE IF NOT EXISTS password_reset_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token_hash TEXT NOT NULL UNIQUE,
            expires_at TEXT NOT NULL,
            used_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )"""
    )
    columns = {row[1] for row in connection.execute("PRAGMA table_info(practice_sessions)")}
    if "transcript" not in columns:
        connection.execute("ALTER TABLE practice_sessions ADD COLUMN transcript TEXT")
    if "analysis_json" not in columns:
        connection.execute("ALTER TABLE practice_sessions ADD COLUMN analysis_json TEXT")
    connection.commit()


with app.app_context():
    init_db()


# ---------------------------------------------------------------- Helpers
def now_utc():
    return datetime.now(timezone.utc)


def parse_iso(value):
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def is_valid_email(value):
    return bool(EMAIL_RE.match(value or ""))


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            if request.path.startswith("/api/"):
                return jsonify(error="No autenticado"), 401
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped_view


# ---------------------------------------------------------------- Análisis de audio
def analyze_transcript(transcript, scenario):
    """Devuelve un análisis estable y persistente del texto transcrito."""
    normalized = (transcript or "").strip()
    words = re.findall(r"\b[\wÁÉÍÓÚÜÑáéíóúüñ'-]+\b", normalized, flags=re.UNICODE)
    word_count = len(words)
    sentence_count = len(re.findall(r"[.!?¿¡…]", normalized)) or (1 if word_count else 0)
    filler_matches = re.findall(
        r"\b(?:eh|uh|mm|mhm|ni|como|digamos|bueno|bueno)\b",
        normalized,
        flags=re.IGNORECASE,
    )
    filler_ratio = min(1.0, len(filler_matches) / max(1, word_count / 8))

    clarity = min(100, round(65 + min(word_count, 80) / 8 + min(sentence_count, 8) * 2))
    organization = min(100, round(72 + min(sentence_count, 8) * 2 - filler_ratio * 25))
    coherence = min(100, round(70 + min(sentence_count, 8) * 2 - filler_ratio * 20))
    vocabulary = min(100, round(55 + min(word_count, 120) / 5))
    fluency = min(100, round(70 + min(word_count, 100) / 10 - filler_ratio * 30))
    score = round(
        (clarity + organization + coherence + vocabulary + fluency) / 5
    )
    feedback = (
        "Tu respuesta tiene una base clara. Reducir repeticiones y mejorar la "
        "estructura puede fortalecerla aún más."
        if score >= 60
        else "Haz una respuesta más concreta y organiza las ideas en un hilo claro."
    )

    return {
        "transcript": normalized,
        "score": max(0, min(100, score)),
        "clarity": max(0, min(100, clarity)),
        "organization": max(0, min(100, organization)),
        "coherence": max(0, min(100, coherence)),
        "vocabulary": max(0, min(100, vocabulary)),
        "fluency": max(0, min(100, fluency)),
        "fillers": max(0, min(100, round(100 - filler_ratio * 100))),
        "feedback": feedback,
    }


def analyze_audio(audio_path, scenario):
    fallback = {
        "score": 0, "clarity": 0, "organization": 0, "coherence": 0,
        "vocabulary": 0, "fluency": 0, "fillers": 0,
        "feedback": "No se pudo completar el análisis de voz. Inténtalo de nuevo en unos segundos.",
    }
    if not app.config.get("GROQ_API_KEY"):
        fallback["feedback"] = (
            "El análisis de voz no está configurado. "
            "Contacta a quien administra Verbai."
        )
        return "", fallback

    transcript = ""
    try:
        client = Groq(api_key=app.config["GROQ_API_KEY"])
        with open(audio_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                file=(os.path.basename(audio_path), audio_file.read()),
                model="whisper-large-v3-turbo",
                language="es",
                response_format="json",
            )
        transcript = (transcription.text or "").strip()
        if not transcript:
            fallback["feedback"] = (
                "No se detectó voz clara en el audio. "
                "Revisa el micrófono e inténtalo otra vez."
            )
            return "", fallback

        analysis = analyze_transcript(transcript, scenario)
        try:
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                temperature=0.2,
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Eres un coach de comunicación en español. "
                            "Devuelve solo JSON válido con enteros de 0 a 100."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            "Analiza esta respuesta del escenario " + scenario + ". "
                            "Devuelve las claves score, clarity, organization, coherence, "
                            "vocabulary, fluency, fillers y feedback. "
                            "fillers es una puntuación: 100 significa pocas muletillas. "
                            "feedback debe ser una recomendación breve en español.\n\n"
                            + transcript
                        ),
                    },
                ],
            )
            remote_analysis = json.loads(response.choices[0].message.content)
            for key in fallback:
                if key != "feedback":
                    remote_analysis[key] = max(
                        0, min(100, int(remote_analysis.get(key, 0)))
                    )
            remote_analysis["feedback"] = str(
                remote_analysis.get("feedback", fallback["feedback"])
            )[:500]
            remote_analysis["transcript"] = transcript
            return transcript, remote_analysis
        except Exception:
            app.logger.exception(
                "El modelo de análisis no está disponible; se usa el análisis local"
            )
            return transcript, analysis
    except Exception:
        app.logger.exception(
            "Falló el análisis de audio de una sesión de práctica; se conserva la transcripción"
        )
        return transcript, fallback


# ---------------------------------------------------------------- Email
def send_password_reset_email(recipient, reset_link):
    smtp_host = app.config.get("SMTP_HOST")
    smtp_user = app.config.get("SMTP_USER")
    smtp_password = app.config.get("SMTP_PASSWORD")
    smtp_from = app.config.get("SMTP_FROM")
    if not all((smtp_host, smtp_user, smtp_password, smtp_from)):
        return False

    message = EmailMessage()
    message["Subject"] = "Recupera tu acceso a Verbai"
    message["From"] = smtp_from
    message["To"] = recipient
    message.set_content(
        "Recibimos una solicitud para cambiar tu contraseña de Verbai.\n\n"
        f"Abre este enlace para continuar: {reset_link}\n\n"
        "El enlace expira en 30 minutos. "
        "Si no solicitaste este cambio, ignora este correo."
    )
    with smtplib.SMTP(smtp_host, app.config["SMTP_PORT"], timeout=15) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(message)
    return True


# ---------------------------------------------------------------- Rutas
@app.get("/")
def landing():
    return render_template("landing.html")


@app.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute", methods=["POST"])
def login():
    if request.method == "POST":
        mode = request.form.get("mode", "login")
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        name = request.form.get("name", "").strip()

        if not email or not password:
            flash("Completa tu correo y contraseña.", "error")
            return render_template("login.html", auth_mode=mode), 400

        if not is_valid_email(email):
            flash("Escribe un correo válido.", "error")
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
                flash("La contraseña debe tener al menos 8 caracteres.", "error")
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
            flash("Correo o contraseña incorrectos.", "error")
            return render_template("login.html", auth_mode=mode), 401

        session.clear()
        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        session.permanent = True
        return redirect(url_for("panel"))

    return render_template("login.html")


@app.route("/forgot-password", methods=["GET", "POST"])
@limiter.limit("3 per hour", methods=["POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()

        if is_valid_email(email):
            connection = get_db()
            user = connection.execute(
                "SELECT id FROM users WHERE email = ?", (email,)
            ).fetchone()
            if user:
                raw_token = secrets.token_urlsafe(32)
                token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
                expires_at = (now_utc() + timedelta(minutes=30)).isoformat()
                connection.execute(
                    "INSERT INTO password_reset_tokens "
                    "(user_id, token_hash, expires_at) VALUES (?, ?, ?)",
                    (user["id"], token_hash, expires_at),
                )
                connection.commit()
                reset_link = url_for("reset_password", token=raw_token, _external=True)
                try:
                    email_sent = send_password_reset_email(email, reset_link)
                except (OSError, smtplib.SMTPException) as e:
                    app.logger.warning("Fallo al enviar email de recuperación: %s", e)
                    email_sent = False
                if not email_sent:
                    app.logger.warning(
                        "SMTP no configurado o no disponible para recuperación de contraseña."
                    )

        flash(
            "Si el correo existe, recibirás instrucciones para recuperar tu cuenta.",
            "success",
        )
    return render_template("forgot_password.html")


@app.route("/reset-password/<token>", methods=["GET", "POST"])
@limiter.limit("20 per hour", methods=["POST"])
def reset_password(token):
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    connection = get_db()
    reset_token = connection.execute(
        "SELECT id, user_id, expires_at, used_at "
        "FROM password_reset_tokens WHERE token_hash = ?",
        (token_hash,),
    ).fetchone()

    expires_at = parse_iso(reset_token["expires_at"]) if reset_token else None
    is_valid = (
        reset_token
        and not reset_token["used_at"]
        and expires_at
        and expires_at > now_utc()
    )

    if not is_valid:
        return render_template(
            "reset_password.html", invalid_token=True, token=token
        ), 400

    if request.method == "POST":
        password = request.form.get("password", "")
        confirmation = request.form.get("password_confirmation", "")
        if len(password) < 8 or password != confirmation:
            return render_template(
                "reset_password.html",
                invalid_token=False,
                token=token,
                form_error=(
                    "Las contraseñas deben coincidir y tener al menos 8 caracteres."
                ),
            ), 400

        connection.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (generate_password_hash(password), reset_token["user_id"]),
        )
        connection.execute(
            "UPDATE password_reset_tokens SET used_at = ? "
            "WHERE user_id = ? AND used_at IS NULL",
            (now_utc().isoformat(), reset_token["user_id"]),
        )
        connection.commit()

        flash("Tu contraseña fue actualizada. Ya puedes iniciar sesión.", "success")
        return redirect(url_for("login"))

    return render_template("reset_password.html", invalid_token=False, token=token)


@app.get("/login/google")
def login_google():
    client_id = app.config.get("GOOGLE_CLIENT_ID")
    if not client_id or not app.config.get("GOOGLE_CLIENT_SECRET"):
        flash("Google OAuth aún no está configurado.", "error")
        return redirect(url_for("login"))

    state = secrets.token_urlsafe(32)
    session["oauth_state"] = state

    params = {
        "client_id": client_id,
        "redirect_uri": app.config["GOOGLE_REDIRECT_URI"],
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "online",
        "prompt": "select_account",
        "state": state,
    }
    return redirect(
        "https://accounts.google.com/o/oauth2/v2/auth?"
        + urllib.parse.urlencode(params)
    )


@app.get("/auth/google/callback")
def google_callback():
    error = request.args.get("error")
    code = request.args.get("code")
    state = request.args.get("state")

    if state != session.pop("oauth_state", None):
        flash("Estado OAuth inválido. Intenta de nuevo.", "error")
        return redirect(url_for("login"))

    if error:
        flash("No se pudo iniciar sesión con Google.", "error")
        return redirect(url_for("login"))
    if not code:
        flash("Falta el código de autorización de Google.", "error")
        return redirect(url_for("login"))

    client_id = app.config.get("GOOGLE_CLIENT_ID")
    client_secret = app.config.get("GOOGLE_CLIENT_SECRET")
    redirect_uri = app.config.get("GOOGLE_REDIRECT_URI")

    if not client_id or not client_secret:
        flash("Google OAuth aún no está configurado.", "error")
        return redirect(url_for("login"))

    token_data = urllib.parse.urlencode({
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }).encode("utf-8")

    token_request = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=token_data,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    try:
        with urllib.request.urlopen(token_request, timeout=20) as response:
            token_payload = json.loads(response.read().decode("utf-8"))
    except Exception:
        app.logger.exception("Fallo el intercambio de token con Google")
        flash("No se pudo completar la autenticación con Google.", "error")
        return redirect(url_for("login"))

    access_token = token_payload.get("access_token")
    if not access_token:
        flash("Google no devolvió un token válido.", "error")
        return redirect(url_for("login"))

    user_request = urllib.request.Request(
        "https://openidconnect.googleapis.com/v1/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    try:
        with urllib.request.urlopen(user_request, timeout=20) as response:
            user_payload = json.loads(response.read().decode("utf-8"))
    except Exception:
        app.logger.exception("Fallo la obtención del perfil de Google")
        flash("No se pudo obtener tu perfil de Google.", "error")
        return redirect(url_for("login"))

    email = (user_payload.get("email") or "").strip().lower()
    email_verified = bool(user_payload.get("email_verified"))
    name = (
        user_payload.get("name")
        or user_payload.get("given_name")
        or (email.split("@", 1)[0] if email else "")
    ).strip()

    if not email or not is_valid_email(email):
        flash("Google no devolvió un correo válido.", "error")
        return redirect(url_for("login"))
    if not email_verified:
        flash("Tu correo de Google no está verificado.", "error")
        return redirect(url_for("login"))

    connection = get_db()
    user = connection.execute(
        "SELECT * FROM users WHERE email = ?", (email,)
    ).fetchone()

    if user is None:
        cursor = connection.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, generate_password_hash(os.urandom(32).hex())),
        )
        connection.commit()
        user = connection.execute(
            "SELECT * FROM users WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()

    session.clear()
    session["user_id"] = user["id"]
    session["user_name"] = user["name"]
    session.permanent = True
    return redirect(url_for("panel"))


@app.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


@app.get("/panel")
@login_required
def panel():
    user = get_db().execute(
        "SELECT name, avatar_url, avatar_style, status FROM users WHERE id = ?",
        (session["user_id"],),
    ).fetchone()
    return render_template("panel.html", user=user)


@app.get("/practice")
@login_required
def practice():
    slug = request.args.get("scenario", "entrevista")
    scenario = SCENARIOS.get(slug, SCENARIOS["entrevista"])
    return render_template("practice.html", scenario=scenario)


@app.get("/results")
@login_required
def results():
    session_id = request.args.get("session_id", type=int)
    practice_session = None
    analysis = {}
    if session_id:
        connection = get_db()
        practice_session = connection.execute(
            "SELECT * FROM practice_sessions WHERE id = ? AND user_id = ?",
            (session_id, session["user_id"]),
        ).fetchone()
        if practice_session and practice_session["analysis_json"]:
            try:
                analysis = json.loads(practice_session["analysis_json"])
            except json.JSONDecodeError:
                analysis = {}
    return render_template(
        "results.html", practice_session=practice_session, analysis=analysis
    )


@app.get("/history")
@login_required
def history():
    return render_template("history.html")


@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    connection = get_db()
    user = connection.execute(
        "SELECT name, email, avatar_url, avatar_style, status FROM users WHERE id = ?",
        (session["user_id"],),
    ).fetchone()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        password = request.form.get("password", "")
        avatar_url = request.form.get("avatar_url", "").strip()
        avatar_style = request.form.get("avatar_style", "default")
        status = request.form.get("status", "active")

        if not name:
            flash("Escribe un nombre para continuar.", "error")
        elif password and len(password) < 8:
            flash("La contraseña debe tener al menos 8 caracteres.", "error")
        elif avatar_style not in {"default", "sunset", "ocean", "forest"}:
            flash("Elige un personaje válido.", "error")
        elif status not in {"active", "inactive"}:
            flash("El estado debe ser activo o inactivo.", "error")
        else:
            updates = ["name = ?", "avatar_url = ?", "avatar_style = ?", "status = ?"]
            values = [name, avatar_url or None, avatar_style, status]
            if password:
                updates.append("password_hash = ?")
                values.append(generate_password_hash(password))
            values.append(session["user_id"])
            connection.execute(
                "UPDATE users SET " + ", ".join(updates) + " WHERE id = ?",
                values,
            )
            connection.commit()
            session["user_name"] = name
            flash("Tus ajustes se actualizaron.", "success")
            user = connection.execute(
                "SELECT name, email, avatar_url, avatar_style, status FROM users WHERE id = ?",
                (session["user_id"],),
            ).fetchone()

    return render_template("settings.html", user=user)


@app.get("/api/history")
@login_required
def history_data():
    connection = get_db()
    sessions = connection.execute(
        """SELECT id, scenario, duration_seconds, score, created_at
           FROM practice_sessions
           WHERE user_id = ?
           ORDER BY created_at DESC, id DESC""",
        (session["user_id"],),
    ).fetchall()

    now = now_utc()
    week_start = now - timedelta(days=41)
    weekly_scores = [[] for _ in range(6)]

    for practice_session in sessions:
        created_at = parse_iso(practice_session["created_at"])
        if not created_at or created_at < week_start:
            continue
        days_since_start = (created_at - week_start).days
        week_index = min(5, max(0, days_since_start // 7))
        weekly_scores[week_index].append(practice_session["score"])

    weekly_averages = [
        round(sum(scores) / len(scores)) if scores else 0 for scores in weekly_scores
    ]
    first_score = next(
        (practice_session["score"] for practice_session in reversed(sessions)), 0
    )
    latest_score = sessions[0]["score"] if sessions else 0

    return {
        "scores": weekly_averages,
        "change": latest_score - first_score if sessions else 0,
        "sessions": [
            {
                "id": practice_session["id"],
                "scenario": practice_session["scenario"],
                "type": SCENARIO_TYPES.get(practice_session["scenario"], "all"),
                "score": practice_session["score"],
                "duration": practice_session["duration_seconds"],
                "created_at": practice_session["created_at"],
            }
            for practice_session in sessions[:20]
        ],
    }


@app.post("/api/sessions")
@login_required
@limiter.limit("20 per hour")
def create_practice_session():
    scenario = request.form.get("scenario", "Entrevista de trabajo").strip()[:120]
    duration = max(0, request.form.get("duration_seconds", 0, type=int))
    audio = request.files.get("audio")

    if not audio or not audio.filename:
        return jsonify(error="Falta el audio de la práctica."), 400

    audio.seek(0, os.SEEK_END)
    size = audio.tell()
    audio.seek(0)
    if size == 0 or size > 25 * 1024 * 1024:
        return jsonify(error="El audio está vacío o es demasiado grande."), 413

    filename = f"session-{session['user_id']}-{secrets.token_hex(16)}.webm"
    audio_path = os.path.join(UPLOAD_DIR, filename)
    audio.save(audio_path)

    try:
        transcript, analysis = analyze_audio(audio_path, scenario)
    except Exception:
        app.logger.exception("Error analizando audio")
        transcript, analysis = "", {"score": 0}

    connection = get_db()
    cursor = connection.execute(
        """INSERT INTO practice_sessions
           (user_id, scenario, duration_seconds, score, audio_path, transcript, analysis_json)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            session["user_id"],
            scenario,
            duration,
            analysis.get("score", 0),
            filename,
            transcript,
            json.dumps(analysis, ensure_ascii=False),
        ),
    )
    connection.commit()
    session_id = cursor.lastrowid

    return {
        "session_id": session_id,
        "redirect": url_for("results", session_id=session_id),
    }


@app.get("/audio/<int:session_id>")
@login_required
def get_audio(session_id):
    connection = get_db()
    row = connection.execute(
        "SELECT audio_path FROM practice_sessions WHERE id = ? AND user_id = ?",
        (session_id, session["user_id"]),
    ).fetchone()
    if not row or not row["audio_path"]:
        abort(404)
    return send_from_directory(UPLOAD_DIR, os.path.basename(row["audio_path"]))


if __name__ == "__main__":
    app.run(
        host=app.config["HOST"],
        port=app.config["PORT"],
        debug=os.environ.get("FLASK_DEBUG", "0") == "1",
    )