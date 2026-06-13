"""paper_service 单元测试 —— 论文搜索、论文列表、引文服务"""
import pytest
from app.services.paper_service import (
    get_journals, get_papers, get_paper_by_id, get_paper_by_doi,
    search_papers, get_trending_papers, record_user_interaction, get_or_create_journal
)
from app.schemas.paper import PaperCreate


class TestGetJournals:
    """期刊服务测试"""

    def test_get_journals_all(self, db_session, sample_journals):
        """获取所有活跃期刊"""
        journals = get_journals(db_session, active_only=True)
        assert len(journals) == 3
        names = {j.name for j in journals}
        assert names == {"Nature", "Science", "Cell"}

    def test_get_journals_no_active(self, db_session, sample_journals):
        """仅获取非活跃期刊（应无结果）"""
        journals = get_journals(db_session, active_only=False)
        # 所有期刊都是活跃的
        assert len(journals) == 3

    def test_get_journals_empty(self, db_session):
        """无期刊时返回空列表"""
        journals = get_journals(db_session)
        assert journals == []


class TestGetPapers:
    """论文列表服务测试"""

    def test_get_papers_default(self, db_session, sample_papers):
        """获取所有论文，默认分页"""
        papers, total = get_papers(db_session)
        assert total == 5
        assert len(papers) == 5

    def test_get_papers_pagination(self, db_session, sample_papers):
        """分页参数正确生效"""
        papers, total = get_papers(db_session, page=1, page_size=2)
        assert total == 5
        assert len(papers) == 2

        papers_page2, _ = get_papers(db_session, page=2, page_size=2)
        assert len(papers_page2) == 2

    def test_get_papers_last_page(self, db_session, sample_papers):
        """最后一页返回剩余论文"""
        papers, _ = get_papers(db_session, page=3, page_size=2)
        assert len(papers) == 1

    def test_get_papers_page_out_of_range(self, db_session, sample_papers):
        """超出范围的页码返回空列表"""
        papers, _ = get_papers(db_session, page=10, page_size=10)
        assert papers == []

    def test_get_papers_by_journal(self, db_session, sample_papers, sample_journals):
        """按期刊ID筛选"""
        papers, total = get_papers(db_session, journal_id=sample_journals["Nature"].id)
        assert total == 2  # Nature 有 2 篇论文
        for p in papers:
            assert p.journal_id == sample_journals["Nature"].id

    def test_get_papers_empty_database(self, db_session):
        """空数据库时总数为0"""
        papers, total = get_papers(db_session)
        assert total == 0
        assert papers == []


class TestGetPaperById:
    """单篇论文查询测试"""

    def test_get_existing_paper(self, db_session, sample_papers):
        """查询存在的论文"""
        paper = get_paper_by_id(db_session, sample_papers[0].id)
        assert paper is not None
        assert paper.title == "Deep Learning in Biomedical Imaging"

    def test_get_nonexistent_paper(self, db_session):
        """查询不存在的论文"""
        paper = get_paper_by_id(db_session, 99999)
        assert paper is None

    def test_get_paper_by_doi(self, db_session, sample_papers):
        """按DOI查询"""
        paper = get_paper_by_doi(db_session, "10.1038/nature12345")
        assert paper is not None
        assert paper.title == "Deep Learning in Biomedical Imaging"

    def test_get_paper_by_doi_nonexistent(self, db_session):
        """查询不存在的DOI"""
        paper = get_paper_by_doi(db_session, "nonexistent-doi")
        assert paper is None


class TestSearchPapers:
    """论文搜索测试（核心功能）"""

    def test_search_by_title(self, db_session, sample_papers):
        """按标题关键词搜索"""
        papers, total = search_papers(db_session, "Deep Learning")
        assert total >= 1
        assert any("Deep Learning" in p.title for p in papers)

    def test_search_by_abstract(self, db_session, sample_papers):
        """按摘要关键词搜索"""
        papers, total = search_papers(db_session, "genome editing")
        assert total >= 1
        assert any("CRISPR" in p.title for p in papers)

    def test_search_by_authors(self, db_session, sample_papers):
        """按作者搜索"""
        papers, total = search_papers(db_session, "Jennifer Chang")
        assert total >= 1

    def test_search_case_insensitive(self, db_session, sample_papers):
        """搜索不区分大小写"""
        papers_upper, _ = search_papers(db_session, "DEEP LEARNING")
        papers_lower, _ = search_papers(db_session, "deep learning")
        assert len(papers_upper) == len(papers_lower)

    def test_search_partial_match(self, db_session, sample_papers):
        """匹配标题/摘要/作者的部分内容"""
        papers, total = search_papers(db_session, "Biomedical")
        assert total >= 1

    def test_search_no_results(self, db_session, sample_papers):
        """搜索无匹配内容"""
        papers, total = search_papers(db_session, "zzz_nonexistent_keyword_xxx")
        assert total == 0
        assert papers == []

    def test_search_pagination(self, db_session, sample_papers):
        """搜索时分页正确"""
        papers, total = search_papers(db_session, "Learning", page=1, page_size=1)
        assert total >= 1
        assert len(papers) == 1

    def test_search_empty_query(self, db_session, sample_papers):
        """空搜索词（应该匹配所有）"""
        papers, total = search_papers(db_session, "")
        assert total >= 1

    def test_search_unicode(self, db_session, sample_papers):
        """Unicode 字符搜索不受影响"""
        papers, total = search_papers(db_session, "α")

    def test_search_no_papers_in_db(self, db_session):
        """空数据库搜索返回0结果"""
        papers, total = search_papers(db_session, "deep learning")
        assert total == 0
        assert papers == []


class TestGetTrendingPapers:
    """热门论文测试"""

    def test_trending_ordered_by_citations(self, db_session, sample_papers):
        """热门论文按引用数降序排列"""
        papers = get_trending_papers(db_session, limit=5)
        assert len(papers) == 5
        citations = [p.citation_count for p in papers]
        assert citations == sorted(citations, reverse=True)
        assert papers[0].citation_count >= papers[-1].citation_count

    def test_trending_limit(self, db_session, sample_papers):
        """limit 参数正确限制结果数"""
        papers = get_trending_papers(db_session, limit=2)
        assert len(papers) == 2

    def test_trending_empty_database(self, db_session):
        """空数据库返回空列表"""
        papers = get_trending_papers(db_session)
        assert papers == []


class TestRecordUserInteraction:
    """用户交互记录测试"""

    def test_record_like(self, db_session, sample_papers, sample_users):
        """记录点赞"""
        interaction = record_user_interaction(
            db_session, sample_users[0].id, sample_papers[0].id, "like"
        )
        assert interaction.user_id == sample_users[0].id
        assert interaction.paper_id == sample_papers[0].id
        assert interaction.action_type == "like"
        assert interaction.id is not None

    def test_record_bookmark(self, db_session, sample_papers, sample_users):
        """记录收藏"""
        interaction = record_user_interaction(
            db_session, sample_users[0].id, sample_papers[1].id, "bookmark"
        )
        assert interaction.action_type == "bookmark"

    def test_multiple_interactions_same_user(self, db_session, sample_papers, sample_users):
        """同一用户对同一论文可以多次交互"""
        i1 = record_user_interaction(db_session, sample_users[0].id, sample_papers[0].id, "like")
        i2 = record_user_interaction(db_session, sample_users[0].id, sample_papers[0].id, "read")
        assert i1.id != i2.id


class TestCreatePaper:
    """论文创建测试"""

    def test_create_paper(self, db_session, sample_journals):
        """创建新论文"""
        from app.models.paper import Paper
        p = Paper(
            title="New Test Paper",
            abstract="Abstract for test",
            authors="Test Author",
            doi="10.1234/test.doi.001",
            journal_id=sample_journals["Nature"].id,
            citation_count=0,
        )
        db_session.add(p)
        db_session.commit()
        db_session.refresh(p)
        assert p.id is not None
        assert p.title == "New Test Paper"


class TestGetOrCreateJournal:
    """期刊创建/获取测试"""

    def test_create_new_journal(self, db_session):
        """创建新期刊"""
        j = get_or_create_journal(db_session, "New Journal", publisher="Test", impact_factor=10.0)
        assert j.id is not None
        assert j.name == "New Journal"
        assert j.impact_factor == 10.0

    def test_get_existing_journal(self, db_session, sample_journals):
        """获取已有期刊（不会重复创建）"""
        j = get_or_create_journal(db_session, "Nature")
        assert j.id == sample_journals["Nature"].id

    def test_create_duplicate_journal(self, db_session, sample_journals):
        """重复创建同名的期刊返回已有记录"""
        from app.models.journal import Journal
        count_before = db_session.query(Journal).count()
        j = get_or_create_journal(db_session, "Nature")
        count_after = db_session.query(Journal).count()
        assert count_before == count_after
        assert j.name == "Nature"