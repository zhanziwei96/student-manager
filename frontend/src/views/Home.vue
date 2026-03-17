<template>
  <div class="home-page">
    <!-- 顶部导航 -->
    <nav class="nav-bar">
      <div class="nav-brand" @click="$router.push('/')">
        <div class="brand-logo">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 2L2 7l10 5 10-5-10-5z"/>
            <path d="M2 17l10 5 10-5"/>
          </svg>
        </div>
        <span class="brand-text">ClassHub</span>
      </div>
      
      <div class="nav-links">
        <button class="nav-link" @click="$router.push('/checkin')">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
          </svg>
          <span>学生签到</span>
        </button>
        
        <button class="nav-link primary" @click="$router.push('/login')">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/>
            <polyline points="10 17 15 12 10 7"/>
          </svg>
          <span>教师入口</span>
        </button>
      </div>
    </nav>

    <!-- 主内容 -->
    <main class="main-content">
      <!-- Hero 区域 -->
      <section class="hero-section">
        <div class="hero-text">
          <h1>数据概览</h1>
          <p>实时掌握班级动态，洞察学习趋势</p>
        </div>
        
        <button class="refresh-btn" @click="loadStats" :class="{ 'spinning': loading }">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="23 4 23 10 17 10"/>
            <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
          </svg>
          <span>刷新数据</span>
        </button>
      </section>

      <!-- 统计卡片 -->
      <section class="stats-section">
        <div class="stat-card" v-for="(stat, index) in mainStats" :key="index">
          <div class="stat-bg-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
              <path v-if="stat.icon === 'users'" d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
              <circle v-if="stat.icon === 'users'" cx="9" cy="7" r="4"/>
              <path v-if="stat.icon === 'users'" d="M23 21v-2a4 4 0 0 0-3-3.87"/>
              
              <path v-if="stat.icon === 'check'" d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
              <polyline v-if="stat.icon === 'check'" points="22 4 12 14.01 9 11.01"/>
              
              <path v-if="stat.icon === 'grid'" d="M3 3h7v7H3zM14 3h7v7h-7zM14 14h7v7h-7zM3 14h7v7H3z"/>
            </svg>
          </div>
          
          <div class="stat-content">
            <div class="stat-header">
              <span class="stat-label">{{ stat.label }}</span>
              <div class="stat-trend" v-if="stat.trend">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>
                  <polyline points="17 6 23 6 23 12"/>
                </svg>
              </div>
            </div>
            
            <div class="stat-value">
              <span class="number" ref="countUp">{{ stat.value }}</span>
              <span class="unit" v-if="stat.unit">{{ stat.unit }}</span>
            </div>
          </div>
          
          <div class="stat-glow" :class="stat.color"></div>
        </div>
      </section>

      <!-- 学生查询 -->
      <section class="search-section">
        <div class="dashboard-card search-card">
          <div class="card-header">
            <div class="header-title">
              <div class="title-icon search">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="11" cy="11" r="8"/>
                  <path d="M21 21l-4.35-4.35"/>
                </svg>
              </div>
              <h3>学生查询</h3>
            </div>
          </div>
          
          <div class="search-form">
            <div class="search-inputs">
              <div class="input-group">
                <label>学号</label>
                <input 
                  v-model="searchForm.student_id" 
                  type="text" 
                  placeholder="请输入学号"
                  @keyup.enter="handleSearch"
                />
              </div>
              <div class="input-group">
                <label>姓名</label>
                <input 
                  v-model="searchForm.name" 
                  type="text" 
                  placeholder="请输入姓名"
                  @keyup.enter="handleSearch"
                />
              </div>
              <button class="search-btn" @click="handleSearch" :disabled="searchLoading">
                <svg v-if="!searchLoading" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="11" cy="11" r="8"/>
                  <path d="M21 21l-4.35-4.35"/>
                </svg>
                <span v-else class="spinner"></span>
                <span>查询</span>
              </button>
            </div>
          </div>
          
          <!-- 查询结果 -->
          <div v-if="searchResult" class="search-result">
            <div class="result-header">
              <div class="student-info">
                <div class="student-avatar-large">{{ searchResult.student.name.charAt(0) }}</div>
                <div class="student-detail">
                  <div class="student-name">{{ searchResult.student.name }}</div>
                  <div class="student-class">{{ searchResult.student.class_name }}</div>
                </div>
              </div>
              <div class="score-display">
                <div class="current-score">{{ searchResult.student.score }}</div>
                <div class="score-label">当前分数</div>
              </div>
            </div>
            
            <div class="rank-info">
              <div class="rank-item">
                <div class="rank-value">{{ searchResult.rank }}</div>
                <div class="rank-label">全校排名</div>
              </div>
              <div class="rank-item">
                <div class="rank-value">{{ searchResult.total_count }}</div>
                <div class="rank-label">总人数</div>
              </div>
              <div class="rank-item">
                <div class="rank-value">{{ ((searchResult.total_count - searchResult.rank + 1) / searchResult.total_count * 100).toFixed(1) }}%</div>
                <div class="rank-label">超过比例</div>
              </div>
            </div>
            
            <!-- 分数变更记录 -->
            <div class="score-logs" v-if="searchResult.score_logs && searchResult.score_logs.length > 0">
              <h4>分数变更记录</h4>
              <div class="logs-list">
                <div 
                  v-for="(log, index) in searchResult.score_logs" 
                  :key="log.log_id"
                  class="log-item"
                  :class="{ 'positive': log.score_change > 0, 'negative': log.score_change < 0 }"
                >
                  <div class="log-change">
                    <span class="change-value">{{ log.score_change > 0 ? '+' : '' }}{{ log.score_change }}</span>
                  </div>
                  <div class="log-reason">{{ log.reason || '无备注' }}</div>
                  <div class="log-time">{{ formatTime(log.operation_time) }}</div>
                </div>
              </div>
            </div>
            <div v-else class="no-logs">
              <p>暂无分数变更记录</p>
            </div>
          </div>
          
          <div v-if="searchError" class="search-error">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <line x1="12" y1="8" x2="12" y2="12"/>
              <line x1="12" y1="16" x2="12.01" y2="16"/>
            </svg>
            <p>{{ searchError }}</p>
          </div>
        </div>
      </section>

      <!-- 排行榜与今日签到 -->
      <section class="dashboard-grid">
        <!-- 分数排行榜 -->
        <div class="dashboard-card ranking-card">
          <div class="card-header">
            <div class="header-title">
              <div class="title-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
                </svg>
              </div>
              <h3>分数排行榜</h3>
            </div>
            
            <span class="header-badge">Top {{ topStudents.length }}</span>
          </div>
          
          <div class="ranking-list">
            <transition-group name="list">
              <div 
                v-for="(student, index) in topStudents" 
                :key="student.student_id"
                class="ranking-item"
                :class="{ 'top-3': index < 3 }"
              >
                <div class="rank-badge" :class="`rank-${index + 1}`">
                  <span v-if="index < 3">
                    <svg viewBox="0 0 24 24" fill="currentColor">
                      <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
                    </svg>
                  </span>
                  <span v-else>{{ index + 1 }}</span>
                </div>
                
                <div class="student-avatar">
                  {{ student.name.charAt(0) }}
                </div>
                
                <div class="student-info">
                  <div class="student-name">{{ student.name }}</div>
                  <div class="student-class">{{ student.class_name }}</div>
                </div>
                
                <div class="student-score">
                  <span class="score-value">{{ student.score }}</span>
                  <span class="score-label">分</span>
                </div>
              </div>
            </transition-group>
            
            <div v-if="topStudents.length === 0" class="empty-state">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <circle cx="12" cy="12" r="10"/>
                <path d="M12 6v6l4 2"/>
              </svg>
              <p>暂无数据</p>
            </div>
          </div>
        </div>

        <!-- 今日签到 -->
        <div class="dashboard-card checkin-card">
          <div class="card-header">
            <div class="header-title">
              <div class="title-icon success">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
              </div>
              <h3>今日签到</h3>
            </div>
            
            <span class="header-badge success">实时</span>
          </div>
          
          <div class="checkin-stats">
            <div class="progress-ring">
              <svg viewBox="0 0 100 100">
                <circle class="ring-bg" cx="50" cy="50" r="42"/>
                <circle 
                  class="ring-progress" 
                  cx="50" 
                  cy="50" 
                  r="42"
                  :style="{ strokeDashoffset: ringOffset }"
                />
              </svg>
              
              <div class="ring-content">
                <span class="ring-value">{{ checkinRate }}</span>
                <span class="ring-label">签到率</span>
              </div>
            </div>
            
            <div class="checkin-detail">
              <div class="detail-item">
                <div class="detail-icon success">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                </div>
                <div class="detail-info">
                  <span class="detail-value">{{ todayCheckin }}</span>
                  <span class="detail-label">已签到</span>
                </div>
              </div>
              
              <div class="detail-item">
                <div class="detail-icon pending">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"/>
                    <polyline points="12 6 12 12 16 14"/>
                  </svg>
                </div>
                <div class="detail-info">
                  <span class="detail-value">{{ totalStudents - todayCheckin }}</span>
                  <span class="detail-label">未签到</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getStats, queryStudent } from '../api'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const totalStudents = ref(0)
const todayCheckin = ref(0)
const classCount = ref(0)
const topStudents = ref([])

const mainStats = computed(() => [
  {
    label: '学生总数',
    value: totalStudents.value,
    icon: 'users',
    color: 'purple',
    trend: true
  },
  {
    label: '今日签到',
    value: todayCheckin.value,
    icon: 'check',
    color: 'cyan',
    trend: true
  },
  {
    label: '班级数量',
    value: classCount.value,
    icon: 'grid',
    color: 'amber'
  }
])

const checkinRate = computed(() => {
  if (totalStudents.value === 0) return '0%'
  return Math.round((todayCheckin.value / totalStudents.value) * 100) + '%'
})

const ringOffset = computed(() => {
  const circumference = 2 * Math.PI * 42
  const rate = totalStudents.value > 0 ? todayCheckin.value / totalStudents.value : 0
  return circumference - (circumference * rate)
})

// 学生查询
const searchForm = ref({
  student_id: '',
  name: ''
})
const searchLoading = ref(false)
const searchResult = ref(null)
const searchError = ref('')

const handleSearch = async () => {
  if (!searchForm.value.student_id || !searchForm.value.name) {
    ElMessage.warning('请输入学号和姓名')
    return
  }
  
  searchLoading.value = true
  searchError.value = ''
  searchResult.value = null
  
  try {
    const res = await queryStudent({
      student_id: searchForm.value.student_id,
      name: searchForm.value.name
    })
    
    if (res.success) {
      searchResult.value = res.data
    } else {
      searchError.value = res.message || '查询失败'
    }
  } catch (error) {
    searchError.value = '查询失败，请稍后重试'
  } finally {
    searchLoading.value = false
  }
}

const formatTime = (time) => {
  if (!time) return ''
  const utcTime = time.endsWith('Z') ? time : time + 'Z'
  return new Date(utcTime).toLocaleString('zh-CN', { 
    month: 'short', 
    day: 'numeric',
    hour: '2-digit', 
    minute: '2-digit' 
  })
}

const loadStats = async () => {
  loading.value = true
  try {
    const res = await getStats()
    if (res.data) {
      totalStudents.value = res.data.student_count || 0
      todayCheckin.value = res.data.today_checkin || 0
      classCount.value = res.data.class_count || 0
      topStudents.value = (res.data.top_students || []).slice(0, 10)
    }
  } catch (error) {
    ElMessage.error('获取统计数据失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadStats()
})
</script>

<style scoped>
.home-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #0a0a0f 0%, #12121a 100%);
}

/* 导航 */
.nav-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 32px;
  background: rgba(15, 15, 25, 0.8);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  position: sticky;
  top: 0;
  z-index: 100;
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  transition: opacity 0.3s ease;
}

.nav-brand:hover {
  opacity: 0.8;
}

.brand-logo {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border-radius: 10px;
  color: white;
}

.brand-logo svg {
  width: 20px;
  height: 20px;
}

.brand-text {
  font-family: 'Orbitron', sans-serif;
  font-size: 1.25rem;
  font-weight: 700;
  color: white;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 12px;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.nav-link:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.2);
  color: white;
}

.nav-link.primary {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border-color: transparent;
  color: white;
}

.nav-link.primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(99, 102, 241, 0.4);
}

.nav-link svg {
  width: 18px;
  height: 18px;
}

/* 主内容 */
.main-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 32px;
}

/* Hero */
.hero-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
}

.hero-text h1 {
  font-size: 1.75rem;
  font-weight: 700;
  color: white;
  margin-bottom: 4px;
}

.hero-text p {
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.95rem;
}

.refresh-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.refresh-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.2);
  color: white;
}

.refresh-btn.spinning svg {
  animation: spin 1s linear infinite;
}

.refresh-btn svg {
  width: 18px;
  height: 18px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 统计卡片 */
.stats-section {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-bottom: 32px;
}

.stat-card {
  position: relative;
  padding: 24px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  overflow: hidden;
  transition: all 0.3s ease;
}

.stat-card:hover {
  background: rgba(255, 255, 255, 0.06);
  border-color: rgba(99, 102, 241, 0.3);
  transform: translateY(-4px);
}

.stat-bg-icon {
  position: absolute;
  right: -20px;
  bottom: -20px;
  width: 120px;
  height: 120px;
  opacity: 0.05;
  color: white;
}

.stat-bg-icon svg {
  width: 100%;
  height: 100%;
}

.stat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.stat-label {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.5);
}

.stat-trend {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 245, 212, 0.1);
  border-radius: 8px;
  color: #00f5d4;
}

.stat-trend svg {
  width: 16px;
  height: 16px;
}

.stat-value {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.stat-value .number {
  font-family: 'Orbitron', monospace;
  font-size: 2.25rem;
  font-weight: 700;
  color: white;
}

.stat-value .unit {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.4);
}

.stat-glow {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 3px;
}

.stat-glow.purple {
  background: linear-gradient(90deg, #6366f1, #8b5cf6);
}

.stat-glow.cyan {
  background: linear-gradient(90deg, #00f5d4, #00bbf9);
}

.stat-glow.amber {
  background: linear-gradient(90deg, #fbbf24, #f59e0b);
}

/* Dashboard Grid */
.dashboard-grid {
  display: grid;
  grid-template-columns: 1.5fr 1fr;
  gap: 24px;
}

.dashboard-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 20px;
  overflow: hidden;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.header-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(251, 191, 36, 0.2), rgba(251, 191, 36, 0.1));
  border-radius: 10px;
  color: #fbbf24;
}

.title-icon.success {
  background: linear-gradient(135deg, rgba(0, 217, 163, 0.2), rgba(0, 217, 163, 0.1));
  color: #00d9a3;
}

.title-icon svg {
  width: 20px;
  height: 20px;
}

.header-title h3 {
  font-size: 1.1rem;
  font-weight: 600;
  color: white;
}

.header-badge {
  padding: 4px 12px;
  background: rgba(251, 191, 36, 0.1);
  border: 1px solid rgba(251, 191, 36, 0.2);
  border-radius: 20px;
  font-size: 0.8rem;
  color: #fbbf24;
}

.header-badge.success {
  background: rgba(0, 217, 163, 0.1);
  border-color: rgba(0, 217, 163, 0.2);
  color: #00d9a3;
}

/* 排行榜 */
.ranking-list {
  padding: 16px;
  max-height: 480px;
  overflow-y: auto;
}

.ranking-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  margin-bottom: 8px;
  transition: all 0.3s ease;
}

.ranking-item:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(99, 102, 241, 0.2);
  transform: translateX(4px);
}

.ranking-item.top-3 {
  background: linear-gradient(90deg, rgba(251, 191, 36, 0.05), transparent);
  border-color: rgba(251, 191, 36, 0.1);
}

.rank-badge {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  font-weight: 700;
  font-size: 0.9rem;
}

.rank-badge.rank-1 {
  background: linear-gradient(135deg, #ffd700, #ffb700);
  color: #000;
}

.rank-badge.rank-2 {
  background: linear-gradient(135deg, #c0c0c0, #a0a0a0);
  color: #000;
}

.rank-badge.rank-3 {
  background: linear-gradient(135deg, #cd7f32, #b87333);
  color: #fff;
}

.rank-badge:not(.rank-1):not(.rank-2):not(.rank-3) {
  background: rgba(255, 255, 255, 0.05);
  color: rgba(255, 255, 255, 0.5);
}

.rank-badge svg {
  width: 16px;
  height: 16px;
}

.student-avatar {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border-radius: 10px;
  font-weight: 600;
  color: white;
  font-size: 0.9rem;
}

.student-info {
  flex: 1;
}

.student-name {
  font-weight: 500;
  color: white;
  margin-bottom: 2px;
}

.student-class {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.4);
}

.student-score {
  display: flex;
  align-items: baseline;
  gap: 2px;
}

.score-value {
  font-family: 'Orbitron', monospace;
  font-size: 1.25rem;
  font-weight: 700;
  color: #00f5d4;
}

.score-label {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.4);
}

/* 今日签到 */
.checkin-stats {
  padding: 32px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 32px;
}

.progress-ring {
  position: relative;
  width: 160px;
  height: 160px;
}

.progress-ring svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.ring-bg {
  fill: none;
  stroke: rgba(255, 255, 255, 0.05);
  stroke-width: 8;
}

.ring-progress {
  fill: none;
  stroke: url(#gradient);
  stroke-width: 8;
  stroke-linecap: round;
  stroke-dasharray: 264;
  transition: stroke-dashoffset 0.6s ease;
}

.progress-ring::before {
  content: '';
  position: absolute;
  inset: 0;
  background: conic-gradient(from 0deg, #6366f1, #00f5d4, #6366f1);
  border-radius: 50%;
  opacity: 0.1;
  filter: blur(20px);
}

.ring-content {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}

.ring-value {
  display: block;
  font-family: 'Orbitron', monospace;
  font-size: 2.5rem;
  font-weight: 700;
  background: linear-gradient(135deg, #6366f1, #00f5d4);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.ring-label {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.5);
}

.checkin-detail {
  display: flex;
  gap: 32px;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.detail-icon {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
}

.detail-icon.success {
  background: linear-gradient(135deg, rgba(0, 217, 163, 0.2), rgba(0, 217, 163, 0.1));
  color: #00d9a3;
}

.detail-icon.pending {
  background: linear-gradient(135deg, rgba(251, 191, 36, 0.2), rgba(251, 191, 36, 0.1));
  color: #fbbf24;
}

.detail-icon svg {
  width: 22px;
  height: 22px;
}

.detail-info {
  display: flex;
  flex-direction: column;
}

.detail-value {
  font-family: 'Orbitron', monospace;
  font-size: 1.5rem;
  font-weight: 700;
  color: white;
}

.detail-label {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.4);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: rgba(255, 255, 255, 0.3);
}

.empty-state svg {
  width: 48px;
  height: 48px;
  margin-bottom: 16px;
  opacity: 0.5;
}

/* 列表动画 */
.list-enter-active,
.list-leave-active {
  transition: all 0.4s ease;
}

.list-enter-from {
  opacity: 0;
  transform: translateX(-20px);
}

.list-leave-to {
  opacity: 0;
  transform: translateX(20px);
}

/* 响应式 */
@media (max-width: 968px) {
  .stats-section {
    grid-template-columns: 1fr;
  }
  
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
  
  .nav-bar {
    padding: 16px;
  }
  
  .main-content {
    padding: 24px 16px;
  }
}

@media (max-width: 640px) {
  .nav-links .nav-link span {
    display: none;
  }
  
  .nav-links .nav-link {
    padding: 10px;
  }
  
  .hero-section {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }
  
  .checkin-detail {
    flex-direction: column;
    gap: 16px;
  }
}

/* SVG gradient for progress ring - defined in CSS */
.progress-ring {
  --gradient-start: #6366f1;
  --gradient-end: #00f5d4;
}

.ring-progress {
  stroke: url(#ringGradient);
}

/* 搜索区域 */
.search-section {
  margin-bottom: 32px;
}

.search-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 20px;
  overflow: hidden;
}

.title-icon.search {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(139, 92, 246, 0.1));
  color: #818cf8;
}

.search-form {
  padding: 24px;
}

.search-inputs {
  display: flex;
  gap: 16px;
  align-items: flex-end;
  flex-wrap: wrap;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 1;
  min-width: 150px;
}

.input-group label {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.5);
}

.input-group input {
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  color: white;
  font-size: 1rem;
  outline: none;
  transition: all 0.3s ease;
}

.input-group input:focus {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(99, 102, 241, 0.5);
}

.input-group input::placeholder {
  color: rgba(255, 255, 255, 0.3);
}

.search-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border: none;
  border-radius: 10px;
  color: white;
  font-size: 0.95rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.search-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(99, 102, 241, 0.4);
}

.search-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.search-btn svg {
  width: 18px;
  height: 18px;
}

.spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

/* 搜索结果 */
.search-result {
  padding: 0 24px 24px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 0;
}

.student-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.student-avatar-large {
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border-radius: 14px;
  font-size: 1.5rem;
  font-weight: 600;
  color: white;
}

.student-detail {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.student-name {
  font-size: 1.25rem;
  font-weight: 600;
  color: white;
}

.student-class {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.5);
}

.score-display {
  text-align: center;
}

.current-score {
  font-family: 'Orbitron', monospace;
  font-size: 2.5rem;
  font-weight: 700;
  background: linear-gradient(135deg, #00f5d4, #00bbf9);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.score-label {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.4);
}

.rank-info {
  display: flex;
  gap: 32px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12px;
  margin-bottom: 20px;
}

.rank-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  flex: 1;
}

.rank-value {
  font-family: 'Orbitron', monospace;
  font-size: 1.75rem;
  font-weight: 700;
  color: white;
}

.rank-label {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.4);
}

/* 分数变更记录 */
.score-logs h4 {
  font-size: 1rem;
  font-weight: 600;
  color: white;
  margin-bottom: 16px;
}

.logs-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.log-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px 16px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 10px;
  border-left: 3px solid transparent;
}

.log-item.positive {
  border-left-color: #00d9a3;
}

.log-item.negative {
  border-left-color: #ef4444;
}

.log-change {
  min-width: 50px;
}

.change-value {
  font-family: 'Orbitron', monospace;
  font-size: 1.1rem;
  font-weight: 600;
}

.log-item.positive .change-value {
  color: #00d9a3;
}

.log-item.negative .change-value {
  color: #ef4444;
}

.log-reason {
  flex: 1;
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.7);
}

.log-time {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.4);
}

.no-logs {
  text-align: center;
  padding: 40px;
  color: rgba(255, 255, 255, 0.3);
}

.no-logs p {
  font-size: 0.9rem;
}

.search-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 40px;
  color: #ef4444;
}

.search-error svg {
  width: 48px;
  height: 48px;
}

.search-error p {
  font-size: 0.95rem;
}

@media (max-width: 640px) {
  .search-inputs {
    flex-direction: column;
    align-items: stretch;
  }
  
  .search-btn {
    justify-content: center;
  }
  
  .result-header {
    flex-direction: column;
    gap: 20px;
    text-align: center;
  }
  
  .rank-info {
    flex-direction: column;
    gap: 16px;
  }
  
  .log-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}
</style>
