import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import app as app_module
import auth as auth_module


class FakeConn:
    def commit(self):
        return None

    def rollback(self):
        return None


class FakeCursor:
    def __init__(self):
        self.users = {}
        self.files = {}
        self.file_access = set()
        self._result = None

    def execute(self, query, params=None):
        normalized = " ".join(query.split())
        params = params or ()

        if normalized.startswith("INSERT INTO users"):
            username, password = params
            if username in self.users:
                raise Exception("duplicate user")
            self.users[username] = password
            self._result = None
            return

        if normalized.startswith("SELECT username, password FROM users WHERE username=%s"):
            username = params[0]
            stored_password = self.users.get(username)
            self._result = (username, stored_password) if stored_password is not None else None
            return

        if normalized.startswith("UPDATE users SET password=%s WHERE username=%s"):
            password, username = params
            if username in self.users:
                self.users[username] = password
            self._result = None
            return

        if normalized.startswith("SELECT * FROM users WHERE username=%s"):
            username = params[0]
            stored_password = self.users.get(username)
            self._result = (username, stored_password) if stored_password is not None else None
            return

        if normalized.startswith("INSERT INTO files"):
            filename, owner, filepath, file_id = params
            self.files[file_id] = {
                "filename": filename,
                "owner": owner,
                "filepath": filepath,
                "file_id": file_id,
                "created_at": datetime(2026, 4, 10, 12, 0, 0),
            }
            self._result = None
            return

        if normalized.startswith("SELECT filename, filepath, created_at, file_id, owner FROM files WHERE file_id=%s AND ("):
            file_id, username, access_username = params
            file_record = self.files.get(file_id)
            if file_record and (
                file_record["owner"] == username or (file_id, access_username) in self.file_access
            ):
                self._result = (
                    file_record["filename"],
                    file_record["filepath"],
                    file_record["created_at"],
                    file_record["file_id"],
                    file_record["owner"],
                )
            else:
                self._result = None
            return

        if normalized.startswith("SELECT filename, filepath, created_at, file_id, owner FROM files WHERE file_id=%s AND owner=%s"):
            file_id, owner = params
            file_record = self.files.get(file_id)
            if file_record and file_record["owner"] == owner:
                self._result = (
                    file_record["filename"],
                    file_record["filepath"],
                    file_record["created_at"],
                    file_record["file_id"],
                    file_record["owner"],
                )
            else:
                self._result = None
            return

        if normalized.startswith("SELECT filename, filepath, created_at, file_id, owner FROM files WHERE file_id=%s"):
            file_id = params[0]
            file_record = self.files.get(file_id)
            if file_record:
                self._result = (
                    file_record["filename"],
                    file_record["filepath"],
                    file_record["created_at"],
                    file_record["file_id"],
                    file_record["owner"],
                )
            else:
                self._result = None
            return

        if normalized.startswith("SELECT filename, filepath, created_at, file_id, owner FROM files WHERE owner=%s OR file_id IN"):
            owner, shared_user = params
            rows = []
            for file_record in self.files.values():
                if file_record["owner"] == owner or (file_record["file_id"], shared_user) in self.file_access:
                    rows.append(
                        (
                            file_record["filename"],
                            file_record["filepath"],
                            file_record["created_at"],
                            file_record["file_id"],
                            file_record["owner"],
                        )
                    )
            self._result = rows
            return

        if normalized.startswith("SELECT * FROM file_access WHERE file_id=%s AND username=%s"):
            file_id, username = params
            self._result = (file_id, username) if (file_id, username) in self.file_access else None
            return

        if normalized.startswith("INSERT INTO file_access"):
            file_id, username = params
            self.file_access.add((file_id, username))
            self._result = None
            return

        if normalized.startswith("DELETE FROM file_access WHERE file_id=%s"):
            file_id = params[0]
            self.file_access = {
                access for access in self.file_access if access[0] != file_id
            }
            self._result = None
            return

        if normalized.startswith("DELETE FROM files WHERE file_id=%s"):
            file_id = params[0]
            self.files.pop(file_id, None)
            self._result = None
            return

        raise AssertionError(f"Unhandled query in test double: {normalized}")

    def fetchone(self):
        return self._result

    def fetchall(self):
        return self._result or []


class FakeDatabase:
    def __init__(self):
        self.cursor = FakeCursor()
        self.conn = FakeConn()

    def add_user(self, username, password):
        self.cursor.users[username] = password

    def add_file(self, *, file_id, filename, owner, filepath):
        self.cursor.files[file_id] = {
            "filename": filename,
            "owner": owner,
            "filepath": filepath,
            "file_id": file_id,
            "created_at": datetime(2026, 4, 10, 12, 0, 0),
        }

    def grant_access(self, file_id, username):
        self.cursor.file_access.add((file_id, username))


@pytest.fixture
def workspace_tmpdir():
    temp_root = Path.cwd() / "test_artifacts" / uuid4().hex
    temp_root.mkdir(parents=True, exist_ok=True)
    yield temp_root
    shutil.rmtree(temp_root, ignore_errors=True)


@pytest.fixture
def fake_db(monkeypatch, workspace_tmpdir):
    database = FakeDatabase()
    upload_root = workspace_tmpdir / "uploads"
    upload_root.mkdir()

    monkeypatch.setattr(app_module, "cursor", database.cursor)
    monkeypatch.setattr(app_module, "conn", database.conn)
    monkeypatch.setattr(auth_module, "cursor", database.cursor)
    monkeypatch.setattr(auth_module, "conn", database.conn)
    monkeypatch.setattr(app_module, "UPLOAD_FOLDER", str(upload_root))

    app_module.app.config["TESTING"] = True
    return database


@pytest.fixture
def client(fake_db):
    return app_module.app.test_client()
