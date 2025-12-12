#!/usr/bin/env python3
import requests

# Test the API
login_data = {'username': 'student_test', 'password': 'password123'}
response = requests.post('http://localhost:5000/api/auth/login', json=login_data)
if response.status_code == 200:
    token = response.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}

    # Test lesson quiz API
    response = requests.get('http://localhost:5000/api/lessons/1003/quiz', headers=headers)
    print(f'Status: {response.status_code}')
    print(f'Response: {response.json()}')
else:
    print(f'Login failed: {response.status_code}')
    print(response.text)