"""API 集成测试 —— 论文搜索和推荐端点"""
import pytest


class TestSearchAPI:
    """论文搜索 API 测试"""

    def test_search_by_query(self, client, sample_papers):
        """按关键词搜索论文"""
        resp = client.get("/api/papers/search", params={"q": "deep learning"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert len(data["papers"]) > 0
        assert any("deep" in p["title"].lower() for p in data["papers"])

    def test_search_no_results(self, client, sample_papers):
        """搜索无匹配返回空结果"""
        resp = client.get("/api/papers/search", params={"q": "zzz_nonexistent_xxxx"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["papers"] == []

    def test_search_missing_query(self, client):
        """不传 q 参数应返回 422"""
        resp = client.get("/api/papers/search")
        assert resp.status_code == 422

    def test_search_empty_query(self, client, sample_papers):
        """空字符串搜索"""
        resp = client.get("/api/papers/search", params={"q": ""})
        # 空字符串也是有效参数，但不符合 min_length=1
        assert resp.status_code == 422

    def test_search_by_author(self, client, sample_papers):
        """按作者名搜索"""
        resp = client.get("/api/papers/search", params={"q": "Jennifer Chang"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1

    def test_search_pagination(self, client, sample_papers):
        """搜索时分页"""
        resp = client.get("/api/papers/search", params={"q": "Learning", "page": 1, "page_size": 1})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["papers"]) <= 1
        assert data["page"] == 1

    def test_search_invalid_page(self, client, sample_papers):
        """无效分页参数"""
        resp = client.get("/api/papers/search", params={"q": "test", "page": 0})
        assert resp.status_code == 422


class TestTrendingAPI:
    """热门论文 API 测试"""

    def test_trending_papers(self, client, sample_papers):
        """获取热门论文"""
        resp = client.get("/api/papers/recommendations/trending")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] > 0
        assert len(data["papers"]) > 0

    def test_trending_limit(self, client, sample_papers):
        """limit 参数控制返回数"""
        resp = client.get("/api/papers/recommendations/trending", params={"limit": 2})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["papers"]) <= 2

    def test_trending_order_by_citations(self, client, sample_papers):
        """热门论文按引用数降序"""
        resp = client.get("/api/papers/recommendations/trending", params={"limit": 5})
        data = resp.json()
        papers = data["papers"]
        citations = [p["citation_count"] for p in papers]
        assert citations == sorted(citations, reverse=True)


class TestPaperDetailAPI:
    """论文详情及引文 API 测试"""

    def test_get_paper_by_id(self, client, sample_papers):
        """获取单篇论文"""
        paper_id = sample_papers[0].id
        resp = client.get(f"/api/papers/{paper_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Deep Learning in Biomedical Imaging"
        assert "journal" in data
        assert data["journal"]["name"] == "Nature"

    def test_get_paper_not_found(self, client):
        """不存在的论文返回 404"""
        resp = client.get("/api/papers/99999")
        assert resp.status_code == 404

    def test_get_paper_citations(self, client, sample_papers):
        """获取论文引文图谱"""
        paper_id = sample_papers[0].id
        resp = client.get(f"/api/papers/{paper_id}/citations")
        assert resp.status_code == 200
        data = resp.json()
        assert "references" in data
        assert "cited_by" in data

    def test_get_paper_citations_not_found(self, client):
        """不存在的论文引文应返回 404"""
        resp = client.get("/api/papers/99999/citations")
        assert resp.status_code == 404


class TestPaperListAPI:
    """论文列表 API 测试"""

    def test_get_all_papers(self, client, sample_papers):
        """获取论文列表"""
        resp = client.get("/api/papers/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 5
        assert len(data["papers"]) == 5

    def test_papers_pagination(self, client, sample_papers):
        """分页参数"""
        resp = client.get("/api/papers/", params={"page": 1, "page_size": 2})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["papers"]) == 2
        assert data["page"] == 1

    def test_papers_invalid_page(self, client):
        """无效分页"""
        resp = client.get("/api/papers/", params={"page": 0})
        assert resp.status_code == 422


class TestRecommendationAPI:
    """推荐 API（需认证）测试"""

    def _get_token(self, client, db_session, sample_users):
        """辅助：获取认证 token"""
        resp = client.post("/api/auth/login", json={
            "email": sample_users[0].email,
            "password": "pass123"
        })
        assert resp.status_code == 200, f"Login failed: {resp.status_code} {resp.text}"
        return resp.json()["access_token"]

    def test_similar_papers_endpoint(self, client, db_session, sample_papers):
        """相似论文推荐"""
        paper_id = sample_papers[0].id
        resp = client.get(f"/api/papers/{paper_id}/recommendations", params={"limit": 3})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["papers"]) > 0
        # 不包含自己
        ids = [p["id"] for p in data["papers"]]
        assert paper_id not in ids

    def test_personalized_feed_requires_auth(self, client):
        """个性化推荐要求登录"""
        resp = client.get("/api/papers/recommendations/feed")
        assert resp.status_code == 401

    def test_personalized_feed_with_auth(self, client, db_session, sample_papers, sample_users):
        """已登录用户获得个性化推荐"""
        token = self._get_token(client, db_session, sample_users)
        # Verify token works for /auth/me first
        me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me_resp.status_code == 200, f"/auth/me failed: {me_resp.text}"
        resp = client.get(
            "/api/papers/recommendations/feed",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200, f"Feed failed: {resp.status_code} {resp.text}"

    def test_friend_recommendations_requires_auth(self, client):
        """好友推荐要求登录"""
        resp = client.get("/api/papers/recommendations/friends")
        assert resp.status_code == 401

    def test_friend_recommendations_with_auth(self, client, db_session, sample_papers, sample_users):
        """已登录用户获得好友推荐"""
        token = self._get_token(client, db_session, sample_users)
        resp = client.get(
            "/api/papers/recommendations/friends",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data["papers"], list)


class TestEdgeCaseAPI:
    """API 边界情况测试"""

    def test_invalid_paper_id_type(self, client):
        """非数字 paper_id"""
        resp = client.get("/api/papers/abc")
        assert resp.status_code == 422

    def test_missing_auth_header_format(self, client, db_session, sample_users):
        """无效的 Authorization 格式"""
        resp = client.get(
            "/api/papers/recommendations/feed",
            headers={"Authorization": "InvalidFormat token"}
        )
        assert resp.status_code == 401

    def test_expired_token(self, client):
        """过期或格式错误的 token"""
        resp = client.get(
            "/api/papers/recommendations/feed",
            headers={"Authorization": "Bearer invalid_token_here"}
        )
        assert resp.status_code == 401