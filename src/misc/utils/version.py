import tomllib

from django.conf import settings


def get_app_version() -> str:
    """Return the application version from pyproject.toml."""
    pyproject = settings.BASE_DIR / "pyproject.toml"
    if pyproject.is_file():
        with pyproject.open("rb") as fp:
            data = tomllib.load(fp)
        version = data.get("project", {}).get("version")
        if version:
            return version
    raise RuntimeError("Project version not found in pyproject.toml")
