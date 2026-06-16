// pages/search/search.js - 搜索页逻辑
const api = require('../../utils/api.js');

Page({
  data: {
    keyword: '',
    papers: [],
    page: 1,
    pageSize: 20,
    total: 0,
    loading: false,
    searched: false,
    history: [],
    autoFocus: true,
    journalId: null,
    journalName: ''
  },

  onLoad(options) {
    // 从期刊页跳过来时，加载该期刊的论文
    if (options.journal_id) {
      this.setData({
        journalId: parseInt(options.journal_id),
        journalName: decodeURIComponent(options.journal_name || ''),
        autoFocus: false
      });
      // 直接加载该期刊下的论文
      this.loadJournalPapers();
    }

    // 恢复搜索历史
    try {
      const history = wx.getStorageSync('search_history') || [];
      this.setData({ history });
    } catch (e) {
      console.log('恢复搜索历史失败:', e);
    }
  },

  // 输入关键词
  onInput(e) {
    this.setData({ keyword: e.detail.value });
  },

  // 清空关键词
  clearKeyword() {
    this.setData({ keyword: '', papers: [], searched: false });
  },

  // 搜索
  onSearch() {
    if (!this.data.keyword.trim()) return;
    this.setData({ page: 1, papers: [] });
    this.doSearch();
  },

  // 从历史记录搜索
  searchFromHistory(e) {
    const keyword = e.currentTarget.dataset.keyword;
    this.setData({ keyword, page: 1, papers: [] });
    this.doSearch();
  },

  // 清空历史
  clearHistory() {
    wx.showModal({
      title: '确认清空',
      content: '确定要清空搜索历史吗？',
      success: (res) => {
        if (res.confirm) {
          this.setData({ history: [] });
          wx.removeStorageSync('search_history');
        }
      }
    });
  },

  // 保存搜索历史
  saveHistory(keyword) {
    if (!keyword) return;
    let history = this.data.history.filter(h => h !== keyword);
    history.unshift(keyword);
    history = history.slice(0, 10); // 最多保留10条
    this.setData({ history });
    wx.setStorageSync('search_history', history);
  },

  // 加载指定期刊下的论文
  async loadJournalPapers() {
    if (this.data.loading) return;
    this.setData({ loading: true });

    try {
      const response = await api.getPapers(1, 20, this.data.journalId);
      const processed = this.processPapers(response.papers);
      this.setData({
        papers: processed,
        total: response.total || processed.length,
        searched: true
      });
    } catch (err) {
      console.error('加载期刊论文失败:', err);
    } finally {
      this.setData({ loading: false });
    }
  },

  // 执行搜索
  async doSearch() {
    const keyword = this.data.keyword.trim();
    if (!keyword) return;
    if (this.data.loading) return;

    this.setData({ loading: true });
    this.saveHistory(keyword);

    try {
      const response = await api.searchPapers(keyword, this.data.page, this.data.pageSize);
      const processed = this.processPapers(response.papers);
      
      this.setData({
        papers: processed,
        total: response.total || processed.length,
        searched: true
      });
    } catch (err) {
      console.error('搜索失败:', err);
      this.setData({ searched: true });
    } finally {
      this.setData({ loading: false });
    }
  },

  // 处理论文数据
  processPapers(papers) {
    return papers.map(p => {
      const journalName = p.journal ? p.journal.name : (p.journal_id ? '期刊' : '未分类');
      return {
        id: p.id,
        title: p.title,
        abstract: p.abstract ? this.truncateText(p.abstract, 100) : '',
        authors: p.authors ? this.truncateText(p.authors, 40) : '',
        journal_name: journalName,
        citation_count: p.citation_count || 0,
        date_display: api.formatDate(p.publication_date || p.created_at),
        color: api.getJournalColor(journalName)
      };
    });
  },

  // 截断文本
  truncateText(text, maxLength) {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  },

  // 跳转到论文详情
  goToPaper(e) {
    const paperId = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: '/pages/paper/paper?id=' + paperId
    });
  },

  onShareAppMessage() {
    return {
      title: 'TopScholar - 搜索学术论文',
      path: '/pages/search/search'
    };
  }
});