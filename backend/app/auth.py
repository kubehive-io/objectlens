from pathlib import Path
from typing import Annotated

import yaml
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel

from .config import get_settings

security = HTTPBasic(auto_error=False)


class User(BaseModel):
    username: str
    password: str
    roles: list[str] = ["viewer"]
    buckets: list[str] | None = None

    def has_role(self, role: str) -> bool:
        if "admin" in self.roles:
            return True
        return role in self.roles


def load_users() -> dict[str, User]:
    settings = get_settings()
    users_path = Path(settings.users_config_dir)

    # Ensure directory exists
    users_path.mkdir(parents=True, exist_ok=True)

    # Check if there are any user YAML manifests
    yaml_files = list(users_path.glob("*.yaml")) + list(users_path.glob("*.yml"))

    # If no user manifests are found yet, automatically create the defaults
    if not yaml_files:
        default_admin = {
            "username": "admin",
            "password": "adminpassword",
            "roles": ["admin"],
        }
        default_viewer = {
            "username": "viewer",
            "password": "viewerpassword",
            "roles": ["viewer"],
        }
        try:
            with open(users_path / "admin.yaml", "w") as f:
                yaml.safe_dump(default_admin, f)
            with open(users_path / "viewer.yaml", "w") as f:
                yaml.safe_dump(default_viewer, f)
        except Exception as e:
            print(f"Failed to write default user configurations: {e}")

    users = {}
    for file in users_path.glob("*.yaml"):
        try:
            with open(file) as f:
                data = yaml.safe_load(f)
                if data and "username" in data and "password" in data:
                    user = User.model_validate(data)
                    users[user.username] = user
        except Exception as e:
            print(f"Error loading user manifest {file}: {e}")

    for file in users_path.glob("*.yml"):
        try:
            with open(file) as f:
                data = yaml.safe_load(f)
                if data and "username" in data and "password" in data:
                    user = User.model_validate(data)
                    users[user.username] = user
        except Exception as e:
            print(f"Error loading user manifest {file}: {e}")

    return users


def get_current_user(
    credentials: Annotated[HTTPBasicCredentials | None, Depends(security)] = None,
) -> User:
    settings = get_settings()
    if settings.auth_type == "none":
        return User(username="anonymous", password="", roles=["admin"])

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials not provided",
            headers={"WWW-Authenticate": "Basic realm='ObjectLens'"},
        )

    users = load_users()
    user = users.get(credentials.username)
    if not user or user.password != credentials.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic realm='ObjectLens'"},
        )

    return user


def require_role(role: str):
    def dependency(user: Annotated[User, Depends(get_current_user)]):
        if not user.has_role(role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires '{role}' role privilege.",
            )
        return user

    return dependency
