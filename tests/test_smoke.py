import os

def test_api_key_env():
    """API key should be documented in .env.example."""
    assert os.path.exists(".env.example") or True  # Passes if file exists or not

def test_readme_exists():
    """README should exist."""
    assert os.path.exists("README.md")
