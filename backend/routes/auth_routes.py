"""
Authentication routes - Login, Register, Logout, Profile
"""

from flask import Blueprint, request, session, jsonify
from functools import wraps
from models import db
from models.user import User

auth_bp = Blueprint('auth', __name__)


def login_required(f):
    """Decorator to require login for routes - returns JSON for API calls"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            # Return JSON for API routes
            return jsonify({'error': 'Authentication required. Please log in.'}), 401
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to require admin role for routes - returns JSON for API calls"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required. Please log in.'}), 401
        
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin():
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function


@auth_bp.route('/register', methods=['POST'])
def register():
    """API endpoint for user registration"""
    data = request.get_json()
    
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '').strip()
    
    # Validation
    if not username or not email or not password:
        return jsonify({'success': False, 'error': 'All fields are required'}), 400
    
    if len(password) < 6:
        return jsonify({'success': False, 'error': 'Password must be at least 6 characters long'}), 400
    
    # Check if user already exists
    if User.query.filter_by(username=username).first():
        return jsonify({'success': False, 'error': 'Username already exists'}), 400
    
    if User.query.filter_by(email=email).first():
        return jsonify({'success': False, 'error': 'Email already registered'}), 400
    
    # Create new user
    user = User(username=username, email=email, role='user')
    user.set_password(password)
    
    try:
        db.session.add(user)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Registration successful',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_admin': user.is_admin()
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Registration failed'}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """API endpoint for user login"""
    data = request.get_json()
    
    # Accept both 'email' and 'username' fields from frontend
    username_or_email = data.get('email', data.get('username', '')).strip()
    password = data.get('password', '').strip()
    
    if not username_or_email or not password:
        return jsonify({'success': False, 'error': 'Email/username and password are required'}), 400
    
    # Find user by username or email
    user = User.query.filter(
        (User.username == username_or_email) | (User.email == username_or_email)
    ).first()
    
    if user and user.check_password(password):
        session['user_id'] = user.id
        session['username'] = user.username
        session['role'] = user.role
        session['email'] = user.email
        
        import logging
        logging.info(f"User {user.username} logged in successfully. Session: {dict(session)}")
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_admin': user.is_admin()
            }
        }), 200
    else:
        return jsonify({'success': False, 'error': 'Invalid username or password'}), 401


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """API endpoint for user logout"""
    session.clear()
    return jsonify({'success': True, 'message': 'Logout successful'}), 200


@auth_bp.route('/session', methods=['GET'])
def check_session():
    """Check if user is logged in and return user info"""
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            return jsonify({
                'authenticated': True,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'is_admin': user.is_admin()
                }
            }), 200
    
    return jsonify({'authenticated': False}), 200
