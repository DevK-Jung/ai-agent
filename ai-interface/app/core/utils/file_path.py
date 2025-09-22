import os


def find_project_root(path: str = None) -> str | None:
    """프로젝트 루트를 찾습니다."""
    if path is None:
        path = os.path.dirname(__file__)

    current_dir = path
    while True:
        if os.path.exists(os.path.join(current_dir, 'pyproject.toml')):
            return current_dir
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:
            return None
        current_dir = parent_dir