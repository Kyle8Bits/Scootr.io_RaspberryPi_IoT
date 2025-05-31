# tests/conftest.py

import sys
import os
import pytest

# Add the path to where app.py is (inside the 'webpage' folder)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'webpage')))

from app import app as flask_app

@pytest.fixture
def app():
    flask_app.config['TESTING'] = True
    flask_app.config['WTF_CSRF_ENABLED'] = False  # if applicable
    yield flask_app

@pytest.fixture
def client(app):
    with app.test_client() as client:
        yield client

@pytest.fixture
def app_with_context(app):
    with app.app_context():
        yield app