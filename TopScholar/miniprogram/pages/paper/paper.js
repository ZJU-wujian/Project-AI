// pages/paper/paper.js - 论文详情页
const api = require('../../utils/api.js');

Page({
  data: {
    paper: null,
    paperId: null,
    loading: false,
    similarPapers: [],
    similarLoading: false,
    journalColor: '#3b82f6',
    date_display: '',
    keywordList: []
  },

  onLoad(options) {
    if (!options.id) {
      wx.showToast({ title: '论文不存在', icon: 'none' });
      setTimeout(() => wx.navigateBack(), 1000);
      return;
    }
    this.setData({ paperId: parseInt(options.id) });
    this.loadPaper();
    this.loadSimilarPapers();
  },

  // 加载论文详情
  async loadPaper() {
    if (this.data.loading) return;
    this.setData({ loading: true });

    try {
      const paper = await api.getPaper(this.data.paperId);
      const journalName = paper.journal ? paper.journal.name : '未分类';
      
      // 解析关键词
      let keywordList = [];
      if (paper.keywords) {
        // 尝试按逗号、分号、空格等分隔关键词
        keywordList = paper.keywords.split(/[,;，；]/).map(k => k.trim()).filter(k => k).slice(0, 8);
      }

      this.setData({
        paper,
        journalColor: api.getJournalColor(journalName),
        date_display: api.formatFullDate(paper.publication_date || paper.created_at),
        keywordList
      });

      // 设置页面标题
      if (paper.title) {
        wx.setNavigationBarTitle({
          title: paper.title.length > 20 ? paper.title.substring(0, 17) + '...' : paper.title
        });
      }
    } catch (err) {
      console.error('加载论文失败:', err);
      wx.showToast({ title: '加载失败', icon: 'none' });
    } finally {
      this.setData({ loading: false });
    }
  },

  // 加载相似论文
  async loadSimilarPapers() {
    this.setData({ similarLoading: true });
    try {
      const response = await api.getSimilarPapers(this.data.paperId, 5);
      const papers = response.papers || [];
      const processed = papers.map(p => {
        const jName = p.journal ? p.journal.name : '期刊';
        return {
          id: p.id,
          title: p.title.length > 60 ? p.title.substring(0, 57) + '...' : p.title,
          journal_name: jName,
          date_display: api.formatDate(p.publication_date || p.created_at),
          citation_count: p.citation_count || 0,
          color: api.getJournalColor(jName)
        };
      });
      this.setData({ similarPapers: processed });
    } catch (err) {
      console.error('加载相似论文失败:', err);
    } finally {
      this.setData({ similarLoading: false });
    }
  },

  // 跳转到相似论文
  goToSimilar(e) {
    const paperId = e.currentTarget.dataset.id;
    wx.redirectTo({
      url: '/pages/paper/paper?id=' + paperId
    });
  },

  // 复制引用
  copyCitation() {
    if (!this.data.paper) return;
    const p = this.data.paper;
    const citation = [
      p.authors || 'Unknown Author',
      '(' + (new Date(p.publication_date || p.created_at).getFullYear()) + ')',
      p.title + '.',
      p.journal ? p.journal.name : 'Journal'
    ].join(' ');
    
    wx.setClipboardData({
      data: citation,
      success: () => {
        wx.showToast({ title: '已复制引用', icon: 'success' });
      }
    });
  },

  // 分享论文
  sharePaper() {
    if (!this.data.paper) return;
    wx.showShareMenu({
      withShareTicket: true,
      menus: ['shareAppMessage', 'shareTimeline']
    });
  },

  onShareAppMessage() {
    const p = this.data.paper;
    return {
      title: p ? p.title : 'TopScholar - 学术论文',
      path: '/pages/paper/paper?id=' + this.data.paperId
    };
  },

  onShareTimeline() {
    const p = this.data.paper;
    return {
      title: p ? p.title : 'TopScholar - 学术论文',
      query: 'id=' + this.data.paperId
    };
  }
});