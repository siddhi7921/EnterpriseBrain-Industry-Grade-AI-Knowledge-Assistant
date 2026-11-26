from __future__ import annotations


def _register_user(client, email: str, password: str, org_name: str | None = None) -> dict:
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "organization_name": org_name},
    )
    assert resp.status_code == 201, resp.text
    tokens = resp.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    me = client.get("/api/v1/auth/me", headers=headers).json()
    orgs = client.get("/api/v1/organizations", headers=headers).json()
    return {"headers": headers, "user": me, "orgs": orgs}


def test_end_to_end_rag_and_security_isolation(client):
    # 1. Create Organisation A (Owner + Member) and Organisation B (Owner)
    org_a_owner = _register_user(client, "alice@orga.com", "StrongPass123!", "Org Alpha")
    org_a_id = org_a_owner["orgs"][0]["id"]

    org_a_member = _register_user(client, "bob@orga.com", "StrongPass123!")
    add_res = client.post(
        f"/api/v1/organizations/{org_a_id}/members",
        headers=org_a_owner["headers"],
        json={"email": "bob@orga.com", "role": "member"},
    )
    assert add_res.status_code == 201

    org_b_owner = _register_user(client, "mallory@orgb.com", "StrongPass123!", "Org Beta")

    # 2. Upload general handbook to Org A
    handbook_bytes = (
        b"# Employee Handbook\n\n"
        b"## Leave Policy\n"
        b"All full-time employees at Org Alpha receive 22 days of paid annual leave and 10 days of sick leave.\n\n"
        b"## Expense Policy\n"
        b"Software subscriptions under $100/month are auto-approved."
    )
    up_pub = client.post(
        f"/api/v1/organizations/{org_a_id}/documents",
        headers=org_a_owner["headers"],
        files={"file": ("employee-handbook.md", handbook_bytes, "text/markdown")},
        data={"access_scope": "organization"},
    )
    assert up_pub.status_code == 201, up_pub.text
    pub_doc = up_pub.json()
    assert pub_doc["status"] == "indexed"
    assert pub_doc["chunk_count"] >= 1

    # 3. Upload RESTRICTED executive M&A memo to Org A (not granted to Bob)
    secret_bytes = (
        b"# Project Phoenix Acquisition Memo\n\n"
        b"Org Alpha plans to acquire CloudScale Systems for $48 million in Q3 2026. "
        b"The secret acquisition codename is PHOENIX-48M."
    )
    up_secret = client.post(
        f"/api/v1/organizations/{org_a_id}/documents",
        headers=org_a_owner["headers"],
        files={"file": ("ma-confidential.md", secret_bytes, "text/markdown")},
        data={"access_scope": "restricted"},
    )
    assert up_secret.status_code == 201
    secret_doc = up_secret.json()

    # Security Check #1: User from Org B attempts to access Org A document
    cross_tenant_res = client.get(
        f"/api/v1/documents/{pub_doc['id']}",
        headers=org_b_owner["headers"],
    )
    assert cross_tenant_res.status_code == 403

    # Security Check #2: Org A member Bob attempts to access restricted document UUID
    restricted_get = client.get(
        f"/api/v1/documents/{secret_doc['id']}",
        headers=org_a_member["headers"],
    )
    assert restricted_get.status_code == 403

    # Security Check #2b: Bob asks RAG chat about restricted acquisition - must NOT leak PHOENIX-48M
    bob_secret_chat = client.post(
        f"/api/v1/organizations/{org_a_id}/chat",
        headers=org_a_member["headers"],
        json={"question": "What is the acquisition codename PHOENIX-48M and CloudScale Systems price?"},
    )
    assert bob_secret_chat.status_code == 200
    bob_answer = bob_secret_chat.json()
    assert "PHOENIX-48M" not in bob_answer["answer"]
    assert "$48 million" not in bob_answer["answer"]
    for cit in bob_answer["citations"]:
        assert cit["document_id"] != secret_doc["id"]

    # Authorized query by Bob on general handbook succeeds with validated citations
    bob_valid_chat = client.post(
        f"/api/v1/organizations/{org_a_id}/chat",
        headers=org_a_member["headers"],
        json={"question": "How many days of paid annual leave do employees receive?"},
    )
    assert bob_valid_chat.status_code == 200
    valid_data = bob_valid_chat.json()
    assert "22 days" in valid_data["answer"]
    assert len(valid_data["citations"]) >= 1
    assert valid_data["citations"][0]["document_id"] == pub_doc["id"]

    # Security Check #5: Unsupported file extension rejected
    bad_upload = client.post(
        f"/api/v1/organizations/{org_a_id}/documents",
        headers=org_a_owner["headers"],
        files={"file": ("malware.exe", b"MZ\x90\x00", "application/octet-stream")},
    )
    assert bad_upload.status_code == 400

    # Security Check #6: Alice cannot access Bob private conversation
    bob_conv_id = valid_data["conversation_id"]
    other_conv_res = client.get(
        f"/api/v1/conversations/{bob_conv_id}",
        headers=org_a_owner["headers"],
    )
    assert other_conv_res.status_code == 403

    # Submit user feedback on message
    fb_res = client.post(
        f"/api/v1/messages/{valid_data['message_id']}/feedback",
        headers=org_a_member["headers"],
        json={"rating": 5, "comment": "Accurate citation and fast answer."},
    )
    assert fb_res.status_code == 201
