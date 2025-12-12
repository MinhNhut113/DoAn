#!/usr/bin/env python3
"""Test script for AI recommendations API"""
import requests
import json
from backend.models import db, User
from backend import app

BASE_URL = 'http://localhost:5000/api'

def setup_test_user():
    """Create a test student user if it doesn't exist"""
    with app.app_context():
        u = User.query.filter_by(username='student_test').first()
        if not u:
            u = User(username='student_test', email='student_test@example.com', full_name='Student Test', role='student')
            u.set_password('password123')
            db.session.add(u)
            db.session.commit()
            print('✅ Created test student user')
        else:
            # Reset password just in case
            u.set_password('password123')
            db.session.commit()
            print('✅ Test student user exists, password reset')

def test_recommendations():
    # First setup test user
    setup_test_user()

    # Login as student
    login_data = {
        'username': 'student_test',
        'password': 'password123'
    }

    try:
        # Login
        response = requests.post(f'{BASE_URL}/auth/login', json=login_data)
        if response.status_code != 200:
            print(f"Login failed: {response.status_code} - {response.text}")
            return

        token = response.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}

        print("✅ Login successful")

        # Test recommendations
        response = requests.get(f'{BASE_URL}/ai/recommendations', headers=headers)
        print(f"Recommendations status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Got {data.get('total_recommendations', 0)} recommendations")
            recommendations = data.get('recommendations', [])
            if recommendations:
                print("Sample recommendation:")
                print(json.dumps(recommendations[0], indent=2, ensure_ascii=False))
            else:
                print("ℹ️  No recommendations (this is normal if no quiz data exists)")
        else:
            print(f"❌ Error: {response.text}")

    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == '__main__':
    test_recommendations()