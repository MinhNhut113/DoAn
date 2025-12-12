from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required
from utils import get_current_user_id
from models import db, User
from datetime import datetime, timezone
from datetime import datetime, timezone, timedelta
import random

bp = Blueprint('auth', __name__)

@bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        full_name = data.get('full_name')
        
        if not all([username, email, password, full_name]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Username already exists'}), 400
        
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already exists'}), 400
        
        user = User(
            username=username,
            email=email,
            full_name=full_name,
            role='student'
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # FIX: Cast user_id to string for JWT identity
        access_token = create_access_token(identity=str(user.user_id))
        
        return jsonify({
            'message': 'User registered successfully',
            'access_token': access_token,
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        
        user = User.query.filter_by(username=username).first()
        
        if not user or not user.check_password(password):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        if not user.is_active:
            return jsonify({'error': 'Account is deactivated'}), 403
        
        # FIX: Cast user_id to string for JWT identity
        access_token = create_access_token(identity=str(user.user_id))
        
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    try:
        user_id = get_current_user_id()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify(user.to_dict()), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    try:
        user_id = get_current_user_id()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        if 'full_name' in data:
            user.full_name = data['full_name']
        if 'email' in data:
            user.email = data['email']
        if 'avatar_url' in data:
            user.avatar_url = data['avatar_url']
        if 'learning_goal' in data:
            user.learning_goal = data['learning_goal']
        
        user.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    try:
        user_id = get_current_user_id()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        
        if not old_password or not new_password:
            return jsonify({'error': 'Missing password fields'}), 400
        
        if not user.check_password(old_password):
            return jsonify({'error': 'Invalid current password'}), 401
        
        user.set_password(new_password)
        user.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        return jsonify({
            'message': 'Password changed successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ----------------- Forgot / Reset Password -----------------
@bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    try:
        data = request.get_json() or {}
        email = data.get('email')
        if not email:
            return jsonify({'error': 'Email is required'}), 400

        user = User.query.filter_by(email=email).first()
        if not user:
            # Don't reveal whether email exists; respond success for privacy
            return jsonify({'message': 'If the email exists, a reset token has been sent'}), 200

        # generate 6-digit token
        token = f"{random.randint(0, 999999):06d}"
        expiry = datetime.utcnow() + timedelta(minutes=15)

        user.reset_token = token
        user.reset_token_expiry = expiry
        db.session.commit()

        # Print token to server console (no SMTP configured)
        print(f'RESET TOKEN FOR {email}: {token}')

        return jsonify({'message': 'If the email exists, a reset token has been sent'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/reset-password', methods=['POST'])
def reset_password():
    try:
        data = request.get_json() or {}
        email = data.get('email')
        token = data.get('token')
        new_password = data.get('new_password')

        if not all([email, token, new_password]):
            return jsonify({'error': 'email, token and new_password are required'}), 400

        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'error': 'Invalid token or email'}), 400

        if not user.reset_token or not user.reset_token_expiry:
            return jsonify({'error': 'No reset requested for this account'}), 400

        now = datetime.utcnow()
        if user.reset_token != str(token) or user.reset_token_expiry < now:
            return jsonify({'error': 'Invalid or expired token'}), 400

        # Set new password and clear token
        user.set_password(new_password)
        user.reset_token = None
        user.reset_token_expiry = None
        user.updated_at = datetime.now(timezone.utc)
        db.session.commit()

        return jsonify({'message': 'Password reset successful'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500