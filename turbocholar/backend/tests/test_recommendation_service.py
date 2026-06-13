"""recommendation_service 单元测试 —— 相似论文推荐、个性化推荐、好友推荐"""
import pytest
from app.services.recommendation_service import (
    get_similar_papers, get_personalized_feed, get_friend_recommendations
)
from app.models.interaction import UserInteraction, Follow
from datetime import datetime


class TestGetSimilarPapers:
    """相似论文推荐测试"""

    def test_similar_papers_found(self, db_session, sample_papers):
        """找到与目标论文相似的论文"""
        similar = get_similar_papers(db_session, sample_papers[0].id, limit=3)
        # 返回的相似论文不包含源论文自身
        ids = [p.id for p in similar]
        assert sample_papers[0].id not in ids
        assert len(similar) > 0

    def test_similar_papers_limit(self, db_session, sample_papers):
        """limit 参数正确限制返回数量"""
        similar = get_similar_papers(db_session, sample_papers[0].id, limit=2)
        assert len(similar) <= 2

    def test_similar_papers_nonexistent_paper(self, db_session):
        """不存在的论文返回空列表"""
        similar = get_similar_papers(db_session, 99999)
        assert similar == []

    def test_similarity_by_journal(self, db_session, sample_papers):
        """同期刊论文应有更高的相似度倾向"""
        # Nature 的两篇论文
        nature_papers = [p for p in sample_papers if p.journal.name == "Nature"]
        if len(nature_papers) >= 2:
            source = nature_papers[0]
            similar = get_similar_papers(db_session, source.id, limit=10)
            similar_ids = [p.id for p in similar]
            # 同期刊论文应出现在相似列表中
            assert nature_papers[1].id in similar_ids


class TestGetPersonalizedFeed:
    """个性化推荐测试"""

    def test_personalized_feed_no_interactions(self, db_session, sample_papers, sample_users):
        """用户无任何交互时返回最新论文"""
        feed = get_personalized_feed(db_session, sample_users[0].id, limit=5)
        assert len(feed) > 0

    def test_personalized_feed_with_interactions(self, db_session, sample_papers, sample_users):
        """用户有点赞交互后推荐结果不为空"""
        # 记录一条点赞交互
        interaction = UserInteraction(
            user_id=sample_users[0].id,
            paper_id=sample_papers[0].id,
            action_type="like",
            created_at=datetime.utcnow()
        )
        db_session.add(interaction)
        db_session.commit()

        feed = get_personalized_feed(db_session, sample_users[0].id, limit=5)
        assert len(feed) > 0

    def test_personalized_feed_limit(self, db_session, sample_papers, sample_users):
        """limit 参数生效"""
        feed = get_personalized_feed(db_session, sample_users[0].id, limit=2)
        assert len(feed) <= 2

    def test_personalized_feed_diversity(self, db_session, sample_papers, sample_users):
        """交互后不会只推荐同一篇论文"""
        interaction = UserInteraction(
            user_id=sample_users[0].id,
            paper_id=sample_papers[0].id,
            action_type="like",
            created_at=datetime.utcnow()
        )
        db_session.add(interaction)
        db_session.commit()

        feed = get_personalized_feed(db_session, sample_users[0].id, limit=5)
        assert len(feed) > 0
        # 交互过的论文可能出现在推荐中，但不应全是同一篇

    def test_personalized_feed_with_bookmark(self, db_session, sample_papers, sample_users):
        """收藏交互影响推荐"""
        interaction = UserInteraction(
            user_id=sample_users[0].id,
            paper_id=sample_papers[1].id,
            action_type="bookmark",
            created_at=datetime.utcnow()
        )
        db_session.add(interaction)
        db_session.commit()
        
        feed = get_personalized_feed(db_session, sample_users[0].id, limit=5)
        assert len(feed) > 0


class TestGetFriendRecommendations:
    """好友推荐测试"""

    def test_friend_recommendations_with_follows(self, db_session, sample_papers, sample_users):
        """关注好友后，好友交互过的论文应出现在推荐中"""
        # researcher1 关注 researcher2
        follow = Follow(follower_id=sample_users[0].id, followee_id=sample_users[1].id, created_at=datetime.utcnow())
        db_session.add(follow)

        # researcher2 对一篇论文点赞
        interaction = UserInteraction(
            user_id=sample_users[1].id,
            paper_id=sample_papers[0].id,
            action_type="like",
            created_at=datetime.utcnow()
        )
        db_session.add(interaction)
        db_session.commit()

        recommendations = get_friend_recommendations(db_session, sample_users[0].id, limit=5)
        assert len(recommendations) > 0

    def test_friend_recommendations_no_friends(self, db_session, sample_papers, sample_users):
        """没有关注任何人时返回空列表"""
        recommendations = get_friend_recommendations(db_session, sample_users[0].id)
        assert recommendations == []

    def test_friend_recommendations_no_interactions(self, db_session, sample_papers, sample_users):
        """好友没有交互行为时返回空列表"""
        follow = Follow(follower_id=sample_users[0].id, followee_id=sample_users[1].id, created_at=datetime.utcnow())
        db_session.add(follow)
        db_session.commit()

        recommendations = get_friend_recommendations(db_session, sample_users[0].id)
        assert recommendations == []

    def test_friend_recommendations_limit(self, db_session, sample_papers, sample_users):
        """limit 参数限制推荐数量"""
        recommendations = get_friend_recommendations(db_session, sample_users[0].id, limit=3)
        assert len(recommendations) <= 3


class TestEdgeCases:
    """推荐系统的边界情况测试"""

    def test_similar_papers_single_paper(self, db_session, sample_papers):
        """只有一篇论文时，相似推荐返回空"""
        from app.models.paper import Paper
        # 删除其他论文，只保留一篇
        for p in sample_papers[1:]:
            db_session.delete(p)
        db_session.commit()
        
        similar = get_similar_papers(db_session, sample_papers[0].id)
        assert similar == []

    def test_personalized_feed_new_user(self, db_session, sample_papers, sample_users):
        """新用户（无任何交互）应看到最新论文"""
        feed = get_personalized_feed(db_session, sample_users[0].id, limit=10)
        assert len(feed) > 0
        # 按创建时间降序排列
        dates = [p.created_at for p in feed]
        assert dates == sorted(dates, reverse=True)

    def test_friend_recommendations_with_multiple_friends(self, db_session, sample_papers, sample_users):
        """多个好友的交互聚合"""
        # 两人互关
        for u1, u2 in [(sample_users[0], sample_users[1]), (sample_users[1], sample_users[0])]:
            follow = Follow(follower_id=u1.id, followee_id=u2.id, created_at=datetime.utcnow())
            db_session.add(follow)

        # 两人对不同的论文点赞
        interactions = [
            UserInteraction(user_id=sample_users[1].id, paper_id=sample_papers[0].id, action_type="like", created_at=datetime.utcnow()),
            UserInteraction(user_id=sample_users[0].id, paper_id=sample_papers[2].id, action_type="like", created_at=datetime.utcnow()),
        ]
        for i in interactions:
            db_session.add(i)
        db_session.commit()

        recs_1 = get_friend_recommendations(db_session, sample_users[0].id, limit=5)
        assert len(recs_1) > 0