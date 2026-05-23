class TestCreateDocument:
    def test_requires_auth(self, client):
        resp = client.post("/api/documents", json={"title": "t", "source_text": "s", "tracked_words": []})
        assert resp.status_code == 401
        assert "请先登录" in resp.text

    def test_create_success(self, client, user_token):
        resp = client.post(
            "/api/documents",
            json={"title": "论语选段", "source_text": "子曰学而时习之", "tracked_words": []},
            headers={"Cookie": f"auth_token={user_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "论语选段"
        assert "id" in data

    def test_create_public(self, client, user_token):
        resp = client.post(
            "/api/documents",
            json={"title": "公开文档", "source_text": "公开内容", "tracked_words": [], "is_public": True},
            headers={"Cookie": f"auth_token={user_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "公开文档"


class TestListDocuments:
    def test_requires_auth(self, client):
        resp = client.get("/api/documents")
        assert resp.status_code == 401

    def test_list_empty(self, client, user_token_b):
        resp = client.get("/api/documents", headers={"Cookie": f"auth_token={user_token_b}"})
        assert resp.status_code == 200
        assert resp.json() == {"documents": []}

    def test_list_with_docs(self, client, user_token_b):
        client.post(
            "/api/documents",
            json={"title": "doc1", "source_text": "a", "tracked_words": []},
            headers={"Cookie": f"auth_token={user_token_b}"},
        )
        client.post(
            "/api/documents",
            json={"title": "doc2", "source_text": "b", "tracked_words": []},
            headers={"Cookie": f"auth_token={user_token_b}"},
        )
        resp = client.get("/api/documents", headers={"Cookie": f"auth_token={user_token_b}"})
        docs = resp.json()["documents"]
        assert len(docs) == 2
        titles = {d["title"] for d in docs}
        assert titles == {"doc1", "doc2"}


class TestReadDocument:
    def test_requires_auth(self, client):
        resp = client.get("/api/documents/1")
        assert resp.status_code == 401

    def test_read_own_doc(self, client, user_token):
        create_resp = client.post(
            "/api/documents",
            json={"title": "我的文档", "source_text": "内容", "tracked_words": []},
            headers={"Cookie": f"auth_token={user_token}"},
        )
        doc_id = create_resp.json()["id"]
        resp = client.get(f"/api/documents/{doc_id}", headers={"Cookie": f"auth_token={user_token}"})
        assert resp.status_code == 200
        assert resp.json()["title"] == "我的文档"

    def test_read_nonexistent(self, client, user_token):
        resp = client.get("/api/documents/999", headers={"Cookie": f"auth_token={user_token}"})
        assert resp.status_code == 404

    def test_cannot_read_others_doc(self, client, user_token, admin_token):
        create_resp = client.post(
            "/api/documents",
            json={"title": "用户文档", "source_text": "x", "tracked_words": []},
            headers={"Cookie": f"auth_token={user_token}"},
        )
        doc_id = create_resp.json()["id"]
        resp = client.get(f"/api/documents/{doc_id}", headers={"Cookie": f"auth_token={admin_token}"})
        assert resp.status_code == 404


class TestUpdateDocument:
    def test_requires_auth(self, client):
        resp = client.patch("/api/documents/1", json={"title": "新标题"})
        assert resp.status_code == 401

    def test_update_title(self, client, user_token):
        create_resp = client.post(
            "/api/documents",
            json={"title": "旧标题", "source_text": "x", "tracked_words": []},
            headers={"Cookie": f"auth_token={user_token}"},
        )
        doc_id = create_resp.json()["id"]
        resp = client.patch(
            f"/api/documents/{doc_id}",
            json={"title": "新标题"},
            headers={"Cookie": f"auth_token={user_token}"},
        )
        assert resp.status_code == 200

    def test_make_public_creates_uuid(self, client, user_token):
        create_resp = client.post(
            "/api/documents",
            json={"title": "t", "source_text": "s", "tracked_words": []},
            headers={"Cookie": f"auth_token={user_token}"},
        )
        doc_id = create_resp.json()["id"]
        resp = client.patch(
            f"/api/documents/{doc_id}",
            json={"is_public": True},
            headers={"Cookie": f"auth_token={user_token}"},
        )
        assert resp.status_code == 200
        doc = client.get(f"/api/documents/{doc_id}", headers={"Cookie": f"auth_token={user_token}"}).json()
        assert doc["is_public"] == 1
        assert doc["public_uuid"] is not None

    def test_update_nonexistent(self, client, user_token):
        resp = client.patch(
            "/api/documents/999",
            json={"title": "新标题"},
            headers={"Cookie": f"auth_token={user_token}"},
        )
        assert resp.status_code == 404


class TestDeleteDocument:
    def test_requires_auth(self, client):
        resp = client.delete("/api/documents/1")
        assert resp.status_code == 401

    def test_delete_own_doc(self, client, user_token):
        create_resp = client.post(
            "/api/documents",
            json={"title": "待删", "source_text": "x", "tracked_words": []},
            headers={"Cookie": f"auth_token={user_token}"},
        )
        doc_id = create_resp.json()["id"]
        resp = client.delete(f"/api/documents/{doc_id}", headers={"Cookie": f"auth_token={user_token}"})
        assert resp.status_code == 200
        get_resp = client.get(f"/api/documents/{doc_id}", headers={"Cookie": f"auth_token={user_token}"})
        assert get_resp.status_code == 404

    def test_delete_nonexistent(self, client, user_token):
        resp = client.delete("/api/documents/999", headers={"Cookie": f"auth_token={user_token}"})
        assert resp.status_code == 404


class TestPublicDocument:
    def test_get_public_doc(self, client, user_token):
        create_resp = client.post(
            "/api/documents",
            json={"title": "公开文档", "source_text": "公开内容", "tracked_words": [], "is_public": True},
            headers={"Cookie": f"auth_token={user_token}"},
        )
        doc_id = create_resp.json()["id"]
        doc = client.get(f"/api/documents/{doc_id}", headers={"Cookie": f"auth_token={user_token}"}).json()
        uuid = doc["public_uuid"]
        resp = client.get(f"/api/documents/public/{uuid}")
        assert resp.status_code == 200
        assert resp.json()["title"] == "公开文档"

    def test_get_public_doc_invalid_uuid(self, client):
        resp = client.get("/api/documents/public/nonexistent-uuid")
        assert resp.status_code == 404
