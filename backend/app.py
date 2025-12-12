from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from models import db
import os
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Lấy đường dẫn root folder
ROOT_DIR = Path(__file__).parent.parent
FRONTEND_DIR = ROOT_DIR / 'frontend'

app = Flask(__name__, 
    static_folder=str(FRONTEND_DIR),
    static_url_path='',
    template_folder=str(FRONTEND_DIR))
app.config.from_object(Config)

# Do NOT log secret values. Only log presence/absence to avoid leaking secrets in logs.
if app.config.get('JWT_SECRET_KEY'):
    logger.info("[APP] JWT configured")
else:
    logger.warning("[APP] JWT_SECRET_KEY not set. Set JWT_SECRET_KEY env var for production.")

# Initialize database
db.init_app(app)

# Enable CORS
CORS(app)

# Initialize JWT
jwt = JWTManager(app)

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    logger.warning("[JWT] Token expired")
    return jsonify({'error': 'Token has expired'}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    # Log Authorization header for debugging when in debug mode
    if app.config.get('DEBUG'):
        auth_header = request.headers.get('Authorization')
        logger.warning(f"[JWT] Invalid token: {error} | Authorization header: {auth_header}")
    else:
        logger.warning(f"[JWT] Invalid token: {error}")
    return jsonify({'error': 'Invalid token'}), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    if app.config.get('DEBUG'):
        auth_header = request.headers.get('Authorization')
        logger.warning(f"[JWT] Missing token: {error} | Authorization header: {auth_header}")
    else:
        logger.warning("[JWT] Missing token")
    return jsonify({'error': 'Missing authorization token'}), 401


# Debug: log Authorization header on each request when DEBUG is enabled
@app.before_request
def log_auth_header():
    if app.config.get('DEBUG'):
        auth_header = request.headers.get('Authorization')
        if auth_header:
            logger.info(f"[DEBUG] Incoming Authorization header: {auth_header}")

# Import routes
from routes import auth, courses, lessons, quizzes, progress, admin, ai_recommendations, ai_chat, ai_questions, incorrect_answers, ai_compat, notifications, assignments
from routes import ai_lessons
# Register blueprints
app.register_blueprint(auth.bp, url_prefix='/api/auth')
app.register_blueprint(courses.bp, url_prefix='/api/courses')
app.register_blueprint(lessons.bp, url_prefix='/api/lessons')
app.register_blueprint(quizzes.bp, url_prefix='/api/quizzes')
app.register_blueprint(progress.bp, url_prefix='/api/progress')
app.register_blueprint(admin.bp, url_prefix='/api/admin')
app.register_blueprint(notifications.bp, url_prefix='/api/notifications')
app.register_blueprint(assignments.bp, url_prefix='/api/assignments')
app.register_blueprint(ai_recommendations.bp, url_prefix='/api/recommendations')
app.register_blueprint(ai_chat.bp, url_prefix='/api/ai')
app.register_blueprint(ai_questions.bp, url_prefix='/api/ai')
app.register_blueprint(ai_compat.bp, url_prefix='/api/ai')
app.register_blueprint(incorrect_answers.bp, url_prefix='')
app.register_blueprint(ai_lessons.bp, url_prefix='/api/ai')

# Sanity check for duplicate URL rules (warn only)
def _detect_duplicate_routes(application):
    seen = {}
    duplicates = []
    for rule in application.url_map.iter_rules():
        key = (str(rule), tuple(sorted(rule.methods)))
        if key in seen:
            duplicates.append((seen[key], rule))
        else:
            seen[key] = rule

    if duplicates:
        for a, b in duplicates:
            logger.warning(f"[ROUTES] Duplicate route detected: {a} <-> {b}")
    else:
        logger.info("[ROUTES] No duplicate routes detected")


_detect_duplicate_routes(app)

# Fail-fast in production if critical secrets are missing
if not app.config.get('DEBUG'):
    if not app.config.get('SECRET_KEY') or not app.config.get('JWT_SECRET_KEY'):
        logger.error("[APP] SECRET_KEY and JWT_SECRET_KEY must be set in environment for production.")
        raise RuntimeError("Missing critical secret configuration. Aborting startup.")

@app.route('/api/health', methods=['GET'])
def health_check():
    return {'status': 'ok', 'message': 'Server is running'}, 200

@app.route('/')
def index():
    return send_from_directory(str(FRONTEND_DIR), 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    file_path = FRONTEND_DIR / filename
    
    if file_path.exists() and file_path.is_file():
        return send_from_directory(str(FRONTEND_DIR), filename)
    
    return send_from_directory(str(FRONTEND_DIR), 'index.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
