import io
import os
import tempfile
import unittest
import uuid
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from PIL import Image

from api.v1.endpoints import auth
from services import avatar_service as avatars


def image_bytes(format="PNG"):
    output = io.BytesIO()
    Image.new("RGB", (80, 40), "red").save(output, format=format)
    return output.getvalue()


class AvatarImageTests(unittest.TestCase):
    def test_supported_images_are_normalized(self):
        for format in ("PNG", "JPEG", "WEBP"):
            with self.subTest(format=format):
                normalized = avatars.normalize_avatar(image_bytes(format))
                with Image.open(io.BytesIO(normalized)) as image:
                    self.assertEqual(image.size, (512, 512))
                    self.assertEqual(image.format, "JPEG")
                    self.assertFalse(image.getexif())

    def test_invalid_or_empty_file_rejected(self):
        for data in (b"", b"not-an-image", b"<svg></svg>"):
            with self.assertRaises(HTTPException) as error:
                avatars.normalize_avatar(data)
            self.assertEqual(error.exception.status_code, 422)

    def test_unsupported_image_rejected(self):
        with self.assertRaises(HTTPException) as error:
            avatars.normalize_avatar(image_bytes("GIF"))
        self.assertEqual(error.exception.status_code, 415)

    def test_file_size_limit(self):
        with self.assertRaises(HTTPException) as error:
            avatars.normalize_avatar(b"x" * (avatars.MAX_AVATAR_BYTES + 1))
        self.assertEqual(error.exception.status_code, 413)

    def test_pixel_limit(self):
        with patch.object(avatars, "MAX_AVATAR_PIXELS", 10):
            with self.assertRaises(HTTPException) as error:
                avatars.normalize_avatar(image_bytes())
        self.assertEqual(error.exception.status_code, 422)

    def test_cleanup_does_not_remove_another_users_file(self):
        with tempfile.TemporaryDirectory() as directory:
            other = Path(directory) / f"{uuid.uuid4()}-old.jpg"
            other.write_bytes(b"old")
            avatars.remove_owned_avatar(Path(directory), avatars.AVATAR_URL_PREFIX + other.name, uuid.uuid4())
            self.assertTrue(other.exists())


class AvatarUploadTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name)
        self.setting = patch.object(auth.settings, "avatar_upload_dir", self.path)
        self.setting.start()
        self.user = SimpleNamespace(id=uuid.uuid4(), full_name="Avatar fixture", email="avatar@example.test",
            avatar_url=None, phone_number=None, is_active=True, roles=[], student_profile=None,
            advisor_profile=None, lecturer_profile=None, created_at=datetime.now(timezone.utc))
        self.db = SimpleNamespace(add=Mock(), commit=AsyncMock(), refresh=AsyncMock(), rollback=AsyncMock())
        self.app = FastAPI()
        self.app.include_router(auth.router, prefix="/api/v1/auth")
        self.app.mount("/media/avatars", StaticFiles(directory=self.path))
        self.app.dependency_overrides[auth.get_current_user] = lambda: self.user
        self.app.dependency_overrides[auth.get_db] = lambda: self.db
        self.client = httpx.AsyncClient(transport=httpx.ASGITransport(app=self.app), base_url="http://test")

    async def asyncTearDown(self):
        await self.client.aclose()
        self.setting.stop()
        self.directory.cleanup()

    async def test_upload_serves_image_and_me_returns_new_url(self):
        response = await self.client.post("/api/v1/auth/profile/avatar",
            files={"file": ("../../unsafe.png", image_bytes(), "image/png")})
        self.assertEqual(response.status_code, 200, response.text)
        url = response.json()["avatar_url"]
        self.assertTrue(url.startswith(f"/media/avatars/{self.user.id}-"))
        image = await self.client.get(url)
        self.assertEqual(image.status_code, 200)
        self.assertEqual(image.headers["content-type"], "image/jpeg")
        me = await self.client.get("/api/v1/auth/me")
        self.assertEqual(me.json()["avatar_url"], url)
        self.db.commit.assert_awaited_once()

    async def test_replacing_avatar_removes_old_file_after_commit(self):
        old = self.path / f"{self.user.id}-old.jpg"
        old.write_bytes(image_bytes("JPEG"))
        self.user.avatar_url = avatars.AVATAR_URL_PREFIX + old.name
        response = await self.client.post("/api/v1/auth/profile/avatar",
            files={"file": ("new.png", image_bytes(), "image/png")})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertFalse(old.exists())
        self.assertEqual(len(list(self.path.iterdir())), 1)

    async def test_commit_failure_removes_new_file_and_preserves_old(self):
        old = self.path / f"{self.user.id}-old.jpg"
        old.write_bytes(image_bytes("JPEG"))
        self.user.avatar_url = avatars.AVATAR_URL_PREFIX + old.name
        self.db.commit.side_effect = RuntimeError("DB failure")
        response = await self.client.post("/api/v1/auth/profile/avatar",
            files={"file": ("new.png", image_bytes(), "image/png")})
        self.assertEqual(response.status_code, 500)
        self.assertEqual(list(self.path.iterdir()), [old])
        self.db.rollback.assert_awaited_once()

    async def test_forged_image_is_not_saved(self):
        response = await self.client.post("/api/v1/auth/profile/avatar",
            files={"file": ("fake.png", b"<html>not an image</html>", "image/png")})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(list(self.path.iterdir()), [])
        self.db.commit.assert_not_awaited()

    async def test_oversized_upload_is_not_saved(self):
        response = await self.client.post("/api/v1/auth/profile/avatar",
            files={"file": ("big.png", b"x" * (avatars.MAX_AVATAR_BYTES + 1), "image/png")})
        self.assertEqual(response.status_code, 413)
        self.db.commit.assert_not_awaited()

    async def test_authentication_required(self):
        del self.app.dependency_overrides[auth.get_current_user]
        response = await self.client.post("/api/v1/auth/profile/avatar",
            files={"file": ("new.png", image_bytes(), "image/png")})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(list(self.path.iterdir()), [])
        self.db.commit.assert_not_awaited()


@unittest.skipUnless(os.getenv("RUN_AVATAR_DB") == "1", "Opt in to rollback-only PostgreSQL verification")
class AvatarPersistenceTests(unittest.IsolatedAsyncioTestCase):
    async def test_avatar_is_persisted_for_authenticated_user(self):
        from sqlalchemy import select
        from sqlalchemy.ext.asyncio import AsyncSession
        from core.database import engine
        from core.security import create_access_token
        from models.user import User

        connection = await engine.connect()
        transaction = await connection.begin()
        db = AsyncSession(bind=connection, expire_on_commit=False, join_transaction_mode="create_savepoint")
        try:
            account = User(email=f"avatar-{uuid.uuid4().hex}@example.invalid",
                           full_name="Avatar rollback fixture", hashed_password="not-a-real-password")
            db.add(account)
            await db.flush()
            token = create_access_token({"sub": str(account.id)})
            with tempfile.TemporaryDirectory() as directory, patch.object(auth.settings, "avatar_upload_dir", Path(directory)):
                app = FastAPI()
                app.include_router(auth.router, prefix="/api/v1/auth")
                app.mount("/media/avatars", StaticFiles(directory=directory))
                async def get_fixture_db():
                    yield db
                app.dependency_overrides[auth.get_db] = get_fixture_db
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                    headers = {"Authorization": f"Bearer {token}"}
                    response = await client.post("/api/v1/auth/profile/avatar", headers=headers,
                        files={"file": ("avatar.png", image_bytes(), "image/png")})
                    self.assertEqual(response.status_code, 200, response.text)
                    url = response.json()["avatar_url"]
                    stored = (await db.execute(select(User.avatar_url).where(User.id == account.id))).scalar_one()
                    self.assertEqual(stored, url)
                    me = await client.get("/api/v1/auth/me", headers=headers)
                    self.assertEqual(me.status_code, 200, me.text)
                    self.assertEqual(me.json()["avatar_url"], url)
                    self.assertEqual((await client.get(url)).status_code, 200)
        finally:
            await db.close()
            await transaction.rollback()
            await connection.close()
            await engine.dispose()
