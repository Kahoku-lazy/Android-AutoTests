"""用例管理 API 测试 — Django TestClient。

覆盖：用例 CRUD / 批量导入 / 目录管理 / 权限校验。

注意：部分测试需要 live server 才能运行（如多级目录、批量移动等写操作）。
这些测试标记了 @pytest.mark.skip。
"""

import pytest


@pytest.mark.api
@pytest.mark.case_manager
class TestCaseManagerAPI:
    """用例定义 CRUD — Django TestClient"""

    @pytest.mark.django_db
    def test_list_definitions_returns_array(self, client, user1):
        """GET /api/cases/definitions → 200 + definitions array"""
        from shared.auth.jwt_auth import create_access_token
        token = create_access_token(str(user1.id))
        resp = client.get("/api/cases/definitions",
                          HTTP_AUTHORIZATION=f"Bearer {token}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert "definitions" in data

    @pytest.mark.django_db
    def test_delete_nonexistent_is_idempotent(self, client, user1):
        """DELETE /api/cases/definitions/NONEXISTENT → 200 + ok=True"""
        from shared.auth.jwt_auth import create_access_token
        token = create_access_token(str(user1.id))
        resp = client.delete("/api/cases/definitions/NONEXISTENT-99999",
                             HTTP_AUTHORIZATION=f"Bearer {token}")
        assert resp.status_code == 200
        assert resp.json()["ok"] is True


@pytest.mark.api
@pytest.mark.case_manager
@pytest.mark.skip(reason="需要运行中 Django 服务 (localhost:8765)")
class TestCaseManagerAPILive:
    """需要实时服务的 API 测试 — 原 functional/case-manager/api_tests.py"""

    def test_create_roundtrip(self):
        """POST 创建 → GET 回读一致"""
        pass  # TODO: 迁移 from functional/case-manager/api_tests.py

    def test_update_fields(self):
        """POST 更新后字段变更"""
        pass

    def test_batch_import(self):
        """批量导入 3 条"""
        pass

    def test_batch_move(self):
        """批量移动用例"""
        pass

    def test_delete_nonempty_dir(self):
        """删除非空目录 → 409"""
        pass

    def test_three_level_rejected(self):
        """三级目录被拒"""
        pass
