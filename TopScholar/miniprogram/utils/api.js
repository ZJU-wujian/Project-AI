// utils/api.js - API 请求工具
const app = getApp();
const API_BASE = 'http://localhost:8000/api';

// 统一请求封装
function request(options) {
  return new Promise((resolve, reject) => {
    const token = wx.getStorageSync('token') || '';
    wx.request({
      url: API_BASE + options.url,
      method: options.method || 'GET',
      data: options.data || {},
      header: {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': 'Bearer ' + token } : {})
      },
      timeout: 15000,
      success(res) {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data);
        } else if (res.statusCode === 401) {
          // Token 失效，清除登录状态
          app.clearAuth && app.clearAuth();
          wx.showToast({ title: '请先登录', icon: 'none' });
          reject(new Error('Unauthorized'));
        } else {
          const msg = (res.data && res.data.detail) || '请求失败';
          wx.showToast({ title: msg, icon: 'none' });
          reject(new Error(msg));
        }
      },
      fail(err) {
        wx.showToast({ title: '网络连接失败', icon: 'none' });
        reject(err);
      }
    });
  });
}

// ========== 论文相关 API ==========

// 获取论文列表
function getPapers(page = 1, pageSize = 20, journalId = null) {
  const data = { page, page_size: pageSize };
  if (journalId) data.journal_id = journalId;
  return request({ url: '/papers/', method: 'GET', data });
}

// 获取单篇论文详情
function getPaper(paperId) {
  return request({ url: '/papers/' + paperId, method: 'GET' });
}

// 搜索论文
function searchPapers(keyword, page = 1, pageSize = 20) {
  return request({
    url: '/papers/search',
    method: 'GET',
    data: { q: keyword, page, page_size: pageSize }
  });
}

// 获取热门/趋势论文
function getTrendingPapers(limit = 10) {
  return request({
    url: '/papers/recommendations/trending',
    method: 'GET',
    data: { limit }
  });
}

// 获取相似论文
function getSimilarPapers(paperId, limit = 10) {
  return request({
    url: '/papers/' + paperId + '/recommendations',
    method: 'GET',
    data: { limit }
  });
}

// 获取论文相关动态/帖子
function getPaperPosts(paperId) {
  return request({
    url: '/papers/' + paperId + '/posts',
    method: 'GET'
  });
}

// 用户与论文交互 (点赞/收藏/阅读)
function interactWithPaper(paperId, actionType) {
  return request({
    url: '/papers/' + paperId + '/interact',
    method: 'POST',
    data: { action_type: actionType }
  });
}

// ========== 期刊相关 API ==========

// 获取期刊列表
function getJournals(activeOnly = true) {
  return request({
    url: '/papers/journals',
    method: 'GET',
    data: { active_only: activeOnly }
  });
}

// 获取用户订阅的期刊
function getUserJournals() {
  return request({
    url: '/papers/journals/user/mine',
    method: 'GET'
  });
}

// 保存用户期刊订阅
function saveUserJournals(journalIds) {
  return request({
    url: '/papers/journals/user/mine',
    method: 'POST',
    data: { journal_ids: journalIds }
  });
}

// ========== 用户认证 API ==========

// 注册
function register(email, password, username) {
  return request({
    url: '/auth/register',
    method: 'POST',
    data: { email, password, username }
  });
}

// 登录
function login(email, password) {
  return request({
    url: '/auth/login',
    method: 'POST',
    data: { email, password }
  });
}

// 获取当前用户信息
function getCurrentUser() {
  return request({
    url: '/auth/me',
    method: 'GET'
  });
}

// 更新用户资料
function updateProfile(data) {
  return request({
    url: '/auth/me',
    method: 'PUT',
    data
  });
}

// ========== 工具函数 ==========

// 格式化日期
function formatDate(dateStr) {
  if (!dateStr) return '';
  try {
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now - date;
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    
    if (days < 1) return '今天';
    if (days < 7) return days + '天前';
    if (days < 30) return Math.floor(days / 7) + '周前';
    if (days < 365) return Math.floor(days / 30) + '个月前';
    return Math.floor(days / 365) + '年前';
  } catch (e) {
    return dateStr;
  }
}

// 格式化完整日期
function formatFullDate(dateStr) {
  if (!dateStr) return '';
  try {
    const date = new Date(dateStr);
    return date.getFullYear() + '-' +
      String(date.getMonth() + 1).padStart(2, '0') + '-' +
      String(date.getDate()).padStart(2, '0');
  } catch (e) {
    return dateStr;
  }
}

// 截断文本
function truncate(text, maxLength) {
  if (!text) return '';
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
}

// 获取期刊颜色
function getJournalColor(journalName) {
  const colors = {
    'Nature': '#3b82f6',
    'Science': '#8b5cf6',
    'Cell': '#ec4899',
    'The Lancet': '#10b981',
    'Nature Neuroscience': '#6366f1',
    'Nature Biotechnology': '#14b8a6',
    'arXiv': '#f59e0b'
  };
  return colors[journalName] || '#64748b';
}

// 获取期刊封面
function getCoverImage(journalName) {
  const covers = {
    'Nature': '/covers/nature.jpg',
    'Science': '/covers/science.jpg',
    'Cell': '/covers/cell.jpg',
    'The Lancet': '/covers/lancet.jpg',
    'Nature Neuroscience': '/covers/nature-neuroscience.jpg',
    'Nature Biotechnology': '/covers/nature-biotechnology.jpg',
    'arXiv': '/covers/arxiv.jpg'
  };
  return covers[journalName] || null;
}

module.exports = {
  request,
  getPapers,
  getPaper,
  searchPapers,
  getTrendingPapers,
  getSimilarPapers,
  getPaperPosts,
  interactWithPaper,
  getJournals,
  getUserJournals,
  saveUserJournals,
  register,
  login,
  getCurrentUser,
  updateProfile,
  formatDate,
  formatFullDate,
  truncate,
  getJournalColor,
  getCoverImage,
  API_BASE
};