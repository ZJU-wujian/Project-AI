// app.js - TopScholar 微信小程序全局逻辑
App({
  globalData: {
    apiBase: 'http://localhost:8000/api',
    token: '',
    userInfo: null,
    // 期刊封面图片映射（本地静态资源）
    coverImages: {
      'Nature': '/covers/nature.jpg',
      'Science': '/covers/science.jpg',
      'Cell': '/covers/cell.jpg',
      'The Lancet': '/covers/lancet.jpg',
      'Nature Neuroscience': '/covers/nature-neuroscience.jpg',
      'Nature Biotechnology': '/covers/nature-biotechnology.jpg',
      'arXiv': '/covers/arxiv.jpg'
    },
    // 期刊颜色映射（用于封面无图时显示）
    journalColors: {
      'Nature': '#3b82f6',
      'Science': '#8b5cf6',
      'Cell': '#ec4899',
      'The Lancet': '#10b981',
      'Nature Neuroscience': '#6366f1',
      'Nature Biotechnology': '#14b8a6',
      'arXiv': '#f59e0b'
    }
  },

  onLaunch() {
    // 启动时从本地存储恢复 token 和用户信息
    try {
      const token = wx.getStorageSync('token');
      const userInfo = wx.getStorageSync('userInfo');
      if (token) this.globalData.token = token;
      if (userInfo) this.globalData.userInfo = userInfo;
    } catch (e) {
      console.log('恢复用户信息失败:', e);
    }

    // 获取系统信息（用于适配刘海屏等）
    try {
      const sysInfo = wx.getWindowInfo ? wx.getWindowInfo() : wx.getSystemInfoSync();
      this.globalData.statusBarHeight = sysInfo.statusBarHeight || 20;
    } catch (e) {
      this.globalData.statusBarHeight = 20;
    }
  },

  onShow() {
    // 小程序显示时可以做状态检查
  },

  onHide() {
    // 小程序隐藏时
  },

  // 保存用户登录信息
  saveAuth(token, userInfo) {
    this.globalData.token = token;
    this.globalData.userInfo = userInfo;
    wx.setStorageSync('token', token);
    wx.setStorageSync('userInfo', userInfo);
  },

  // 清除用户信息（登出）
  clearAuth() {
    this.globalData.token = '';
    this.globalData.userInfo = null;
    wx.removeStorageSync('token');
    wx.removeStorageSync('userInfo');
  },

  // 检查是否已登录
  isLoggedIn() {
    return !!this.globalData.token;
  },

  // 获取期刊封面 URL
  getCoverUrl(journalName) {
    const coverPath = this.globalData.coverImages[journalName];
    if (coverPath) {
      return coverPath;
    }
    return null;
  },

  // 获取期刊颜色
  getJournalColor(journalName) {
    return this.globalData.journalColors[journalName] || '#64748b';
  }
});