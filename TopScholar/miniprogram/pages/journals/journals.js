// pages/journals/journals.js - 期刊库逻辑
const api = require('../../utils/api.js');

Page({
  data: {
    journals: [],
    loading: false
  },

  onLoad() {
    this.loadJournals();
  },

  onShow() {
    if (this.data.journals.length === 0) {
      this.loadJournals();
    }
  },

  onPullDownRefresh() {
    this.loadJournals().then(() => {
      wx.stopPullDownRefresh();
    });
  },

  // 加载期刊列表
  async loadJournals() {
    if (this.data.loading) return;
    this.setData({ loading: true });

    try {
      const journals = await api.getJournals(true);
      const processedJournals = journals.map(j => {
        const color = api.getJournalColor(j.name);
        const coverImage = api.getCoverImage(j.name);
        // 生成期刊简称
        let shortName = j.name;
        if (j.name.length > 20) {
          // 取前两个单词的首字母
          const words = j.name.split(' ');
          shortName = words.slice(0, 2).map(w => w[0]).join('').toUpperCase();
        }
        return {
          id: j.id,
          name: j.name,
          impact_factor: j.impact_factor,
          paper_count: j.paper_count || 0,
          volume: j.volume,
          issue: j.issue,
          color: color,
          color_dark: this.darkenColor(color, 0.3),
          cover_image: coverImage,
          short_name: shortName
        };
      });

      this.setData({ journals: processedJournals });
    } catch (err) {
      console.error('加载期刊失败:', err);
    } finally {
      this.setData({ loading: false });
    }
  },

  // 加深颜色
  darkenColor(hex, amount) {
    // hex to rgb
    let r = parseInt(hex.slice(1, 3), 16);
    let g = parseInt(hex.slice(3, 5), 16);
    let b = parseInt(hex.slice(5, 7), 16);
    
    // darken
    r = Math.max(0, Math.floor(r * (1 - amount)));
    g = Math.max(0, Math.floor(g * (1 - amount)));
    b = Math.max(0, Math.floor(b * (1 - amount)));
    
    // rgb to hex
    return '#' + [r, g, b].map(x => x.toString(16).padStart(2, '0')).join('');
  },

  // 选择期刊 - 显示该期刊下的论文
  selectJournal(e) {
    const { id, name } = e.currentTarget.dataset;
    wx.navigateTo({
      url: '/pages/search/search?journal_id=' + id + '&journal_name=' + encodeURIComponent(name)
    });
  },

  // 分享
  onShareAppMessage() {
    return {
      title: 'TopScholar - 学术期刊库',
      path: '/pages/journals/journals'
    };
  }
});