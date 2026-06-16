// pages/profile/profile.js - 个人中心
const app = getApp();
const api = require('../../utils/api.js');

Page({
  data: {
    userInfo: null,
    loggedIn: false,
    avatarLetter: 'T',
    userInfoInitial: 'T',
    showLoginForm: false,
    loginMode: 'login',
    formLoading: false,
    formData: {
      username: '',
      email: '',
      password: ''
    }
  },

  onLoad() {
    this.checkLogin();
  },

  onShow() {
    this.checkLogin();
  },

  // 检查登录状态
  checkLogin() {
    const token = wx.getStorageSync('token');
    const userInfo = wx.getStorageSync('userInfo');
    
    if (token && userInfo) {
      this.setData({
        userInfo: userInfo,
        loggedIn: true,
        userInfoInitial: userInfo.username ? userInfo.username[0].toUpperCase() : 'T'
      });
    } else {
      this.setData({ loggedIn: false, userInfo: null });
    }
  },

  // 显示登录表单
  showLogin() {
    this.setData({
      showLoginForm: true,
      loginMode: 'login'
    });
  },

  // 显示注册表单
  showRegister() {
    this.setData({
      showLoginForm: true,
      loginMode: 'register'
    });
  },

  // 切换登录/注册模式
  switchMode() {
    this.setData({
      loginMode: this.data.loginMode === 'login' ? 'register' : 'login'
    });
  },

  // 隐藏登录表单
  hideLoginForm() {
    this.setData({
      showLoginForm: false,
      formData: { username: '', email: '', password: '' }
    });
  },

  // 表单输入
  onInputUsername(e) {
    this.setData({ 'formData.username': e.detail.value });
  },

  onInputEmail(e) {
    this.setData({ 'formData.email': e.detail.value });
  },

  onInputPassword(e) {
    this.setData({ 'formData.password': e.detail.value });
  },

  // 提交登录/注册
  async submitAuth() {
    const { email, password, username } = this.data.formData;
    
    if (!email || !password) {
      wx.showToast({ title: '请填写邮箱和密码', icon: 'none' });
      return;
    }

    if (this.data.loginMode === 'register' && !username) {
      wx.showToast({ title: '请填写用户名', icon: 'none' });
      return;
    }

    this.setData({ formLoading: true });

    try {
      if (this.data.loginMode === 'login') {
        const result = await api.login(email, password);
        // 登录成功后获取用户信息
        const userInfo = { 
          username: email.split('@')[0],
          email: email,
          token: result.access_token
        };
        app.saveAuth(result.access_token || 'logged-in', userInfo);
        this.setData({
          loggedIn: true,
          userInfo: userInfo,
          userInfoInitial: userInfo.username[0].toUpperCase(),
          showLoginForm: false
        });
        wx.showToast({ title: '登录成功', icon: 'success' });
      } else {
        await api.register(email, password, username);
        wx.showToast({ title: '注册成功，请登录', icon: 'success' });
        this.setData({ loginMode: 'login' });
      }
    } catch (err) {
      console.error('认证失败:', err);
      wx.showToast({ title: '操作失败，请检查信息', icon: 'none' });
    } finally {
      this.setData({ formLoading: false });
    }
  },

  // 退出登录
  logout() {
    wx.showModal({
      title: '确认退出',
      content: '确定要退出登录吗？',
      success: (res) => {
        if (res.confirm) {
          app.clearAuth();
          this.setData({
            loggedIn: false,
            userInfo: null
          });
          wx.showToast({ title: '已退出登录', icon: 'success' });
        }
      }
    });
  },

  // 跳转到收藏
  goToFavorites() {
    if (!this.data.loggedIn) {
      wx.showToast({ title: '请先登录', icon: 'none' });
      this.setData({ showLoginForm: true, loginMode: 'login' });
      return;
    }
    wx.showToast({ title: '功能开发中', icon: 'none' });
  },

  // 跳转到我的期刊
  goToMyJournals() {
    if (!this.data.loggedIn) {
      wx.showToast({ title: '请先登录', icon: 'none' });
      this.setData({ showLoginForm: true, loginMode: 'login' });
      return;
    }
    wx.switchTab({ url: '/pages/journals/journals' });
  },

  // 关于
  showAbout() {
    wx.showModal({
      title: '关于 TopScholar',
      content: 'TopScholar 是一个学术社交与论文发现平台，帮助你发现最新的学术研究成果。',
      showCancel: false
    });
  },

  // 分享应用
  shareApp() {
    wx.showShareMenu({
      withShareTicket: true
    });
  },

  onShareAppMessage() {
    return {
      title: 'TopScholar - 发现最新学术论文',
      path: '/pages/index/index'
    };
  }
});