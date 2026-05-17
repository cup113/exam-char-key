import io
import json


class TestAdminAuth:
    def test_redirects_when_unauth(self, client):
        resp = client.get("/admin/", follow_redirects=False)
        assert resp.status_code == 302
        assert "/admin/login" in resp.headers["location"]

    def test_allows_admin_user(self, client, admin_token):
        resp = client.get(
            "/admin/",
            headers={"Cookie": f"auth_token={admin_token}"},
            follow_redirects=False,
        )
        assert resp.status_code == 200

    def test_rejects_non_admin_user(self, client, user_token):
        resp = client.get(
            "/admin/",
            headers={"Cookie": f"auth_token={user_token}"},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert "/admin/login" in resp.headers["location"]


class TestAdminModels:
    MODEL_NAMES = [
        "Dict Cache",
        "Daily Usage",
        "Query History",
        "Usage Log",
        "Corpus",
    ]

    def test_dashboard_contains_all_model_names(self, client, admin_token):
        resp = client.get(
            "/admin/",
            headers={"Cookie": f"auth_token={admin_token}"},
        )
        assert resp.status_code == 200
        for name in self.MODEL_NAMES:
            assert name in resp.text

    def test_corpus_list_page(self, client, admin_token):
        resp = client.get(
            "/admin/corpus/list",
            headers={"Cookie": f"auth_token={admin_token}"},
        )
        assert resp.status_code == 200


class TestAdminApi:
    BASE = "/api/admin"

    def test_check_admin(self, client, admin_token, user_token):
        resp = client.get(
            f"{self.BASE}/check",
            headers={"Cookie": f"auth_token={admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json() == {"admin": True}

    def test_check_non_admin(self, client, user_token):
        resp = client.get(
            f"{self.BASE}/check",
            headers={"Cookie": f"auth_token={user_token}"},
        )
        assert resp.status_code == 200
        assert resp.json() == {"admin": False}

    def test_check_unauth(self, client):
        resp = client.get(f"{self.BASE}/check")
        assert resp.status_code == 200
        assert resp.json() == {"admin": False}

    def test_import_success(self, client, admin_token):
        lines = [
            json.dumps(
                {
                    "word": "之",
                    "notes": [
                        {"context": "知之者", "detail": "代词", "name_passage": ""}
                    ],
                }
            ),
            json.dumps(
                {
                    "word": "乎",
                    "notes": [
                        {
                            "context": "不亦说乎",
                            "detail": "语气词",
                            "name_passage": "论语",
                        }
                    ],
                }
            ),
        ]
        content = "\n".join(lines)
        resp = client.post(
            f"{self.BASE}/import-corpus",
            headers={"Cookie": f"auth_token={admin_token}"},
            files={"file": ("test.jsonl", io.BytesIO(content.encode("utf-8")))},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["count"] == 2

    def test_import_invalid_json(self, client, admin_token):
        resp = client.post(
            f"{self.BASE}/import-corpus",
            headers={"Cookie": f"auth_token={admin_token}"},
            files={"file": ("bad.jsonl", io.BytesIO(b"not valid json"))},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["count"] == 0

    def test_import_no_file(self, client, admin_token):
        resp = client.post(
            f"{self.BASE}/import-corpus",
            headers={"Cookie": f"auth_token={admin_token}"},
        )
        assert resp.status_code == 400

    def test_import_unauth(self, client):
        resp = client.post(
            f"{self.BASE}/import-corpus",
            files={"file": ("test.jsonl", io.BytesIO(b""))},
        )
        assert resp.status_code == 401

    def test_import_non_admin(self, client, user_token):
        resp = client.post(
            f"{self.BASE}/import-corpus",
            headers={"Cookie": f"auth_token={user_token}"},
            files={"file": ("test.jsonl", io.BytesIO(b""))},
        )
        assert resp.status_code == 403

    def test_auth_me_includes_is_admin(self, client, admin_token, user_token):
        resp = client.get(
            "/api/auth/me",
            headers={"Cookie": f"auth_token={admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["is_admin"] is True

        resp = client.get(
            "/api/auth/me",
            headers={"Cookie": f"auth_token={user_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["is_admin"] is False
