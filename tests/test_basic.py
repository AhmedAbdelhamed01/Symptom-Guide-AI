import os


def test_app_file_exists():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    path = os.path.join(repo_root, 'src', 'app', 'app.py')
    assert os.path.exists(path), f"Expected {path} to exist"
