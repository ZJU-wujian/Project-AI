// pages/index/index.js - 发现页逻辑
const api = require('../../utils/api.js');

Page({
  data: {
    activeTab: 'trending',
    papers: [],
    page: 1,
    pageSize: 15,
    total: 0,
    loading: false,
    hasMore: true
  },

  onLoad() {
    this.loadPapers();
  },

  onShow() {
    // 页面显示时，如果是最新Tab，刷新一次
    if (this.data.activeTab === 'latest' && this.data.papers.length === 0) {
      this.loadPapers();
    }
  },

  onPullDownRefresh() {
    this.setData({ page: 1, papers: [], hasMore: true });
    this.loadPapers().then(() => {
      wx.stopPullDownRefresh();
    });
  },

  // 切换 Tab
  switchTab(e) {
    const tab = e.currentTarget.dataset.tab;
    if (tab === this.data.activeTab) return;
    this.setData({
      activeTab: tab,
      papers: [],
      page: 1,
      hasMore: true
    });
    this.loadPapers();
  },

  // 加载论文
  async loadPapers() {
    if (this.data.loading) return;
    this.setData({ loading: true });

    try {
      let response;
      if (this.data.activeTab === 'trending') {
        response = await api.getTrendingPapers(this.data.pageSize);
      } else {
        response = await api.getPapers(this.data.page, this.data.pageSize);
      }

      const processedPapers = this.processPapers(response.papers);
      const newPapers = this.data.page === 1 ? processedPapers : [...this.data.papers, ...processedPapers];
      
      this.setData({
        papers: newPapers,
        total: response.total || processedPapers.length,
        hasMore: newPapers.length < (response.total || 0)
      });
    } catch (err) {
      console.error('加载论文失败:', err);
      // 加载失败时显示空状态
      if (this.data.page === 1) {
        this.setData({ papers: [], hasMore: false });
      }
    } finally {
      this.setData({ loading: false });
    }
  },

  // 处理论文数据
  processPapers(papers) {
    return papers.map(p => {
      const journalName = p.journal ? p.journal.name : (p.journal_id ? '期刊' : '未分类');
      const volume = p.journal ? p.journal.volume : null;
      return {
        id: p.id,
        title: p.title,
        abstract: p.abstract ? this.truncateText(p.abstract, 120) : '',
        authors: p.authors ? this.truncateText(p.authors, 50) : '',
        journal_name: journalName,
        volume: volume,
        citation_count: p.citation_count || 0,
        date_display: api.formatDate(p.publication_date || p.created_at),
        color: api.getJournalColor(journalName),
        cover_image_url: p.cover_image_url
      };
    });
  },

  // 截断文本
  truncateText(text, maxLength) {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  },

  // 加载更多
  loadMore() {
    if (this.data.loading || !this.data.hasMore) return;
    this.setData({ page: this.data.page + 1 });
    this.loadPapers();
  },

  // 跳转到论文详情
  goToPaper(e) {
    const paperId = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: '/pages/paper/paper?id=' + paperId
    });
  },

  // 跳转到搜索页
  goToSearch() {
    wx.switchTab({
      url: '/pages/search/search'
    });
  },

  // 分享
  onShareAppMessage() {
    return {
      title: 'TopScholar - 发现最新学术论文',
      path: '/pages/index/index'
    };
  },

  onShareTimeline() {
    return {
      title: 'TopScholar - 发现最新学术论文'
    };
  }
});