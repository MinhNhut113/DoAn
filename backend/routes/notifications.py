from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from utils import get_current_user_id
from models import db, Notification
from datetime import datetime

bp = Blueprint('notifications', __name__)

@bp.route('/', methods=['GET'])
@jwt_required()
def get_notifications():
    """Fetch all notifications for current user, ordered by created_at desc"""
    try:
        user_id = get_current_user_id()
        
        # Optional query params: unread=true to filter unread only
        unread_only = request.args.get('unread', 'false').lower() == 'true'
        
        query = Notification.query.filter_by(user_id=user_id)
        if unread_only:
            query = query.filter_by(is_read=False)
        
        notifications = query.order_by(Notification.created_at.desc()).limit(50).all()
        
        return jsonify([{
            'notification_id': n.notification_id,
            'title': n.title,
            'message': n.message,
            'notification_type': n.notification_type,
            'is_read': n.is_read,
            'created_at': n.created_at.isoformat() if n.created_at else None
        } for n in notifications]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/<int:notification_id>/read', methods=['POST'])
@jwt_required()
def mark_notification_read(notification_id):
    """Mark a notification as read"""
    try:
        user_id = get_current_user_id()
        notification = Notification.query.get(notification_id)
        
        if not notification:
            return jsonify({'error': 'Notification not found'}), 404
        
        # Ensure user owns this notification
        if notification.user_id != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        notification.is_read = True
        db.session.commit()
        
        return jsonify({'message': 'Notification marked as read'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
