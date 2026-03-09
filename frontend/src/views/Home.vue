<template>
  <div class="home-container">
    <!-- Hero Section -->
    <div class="hero-section">
      <h1>📚 班级管理系统</h1>
      <p class="subtitle">便捷的学生管理、签到、分数统计工具</p>
      
      <div class="action-buttons">
        <el-button type="primary" size="large" @click="$router.push('/checkin')">
          📝 学生签到
        </el-button>
        <el-button type="success" size="large" @click="$router.push('/admin')">
          👨‍🏫 教师入口
        </el-button>
      </div>
    </div>

    <div class="main-content">
      <!-- 左侧：统计卡片 + 功能介绍 -->
      <div class="left-section">
        <!-- 统计数据卡片 -->
        <el-row :gutter="16" class="stats-section">
          <el-col :span="8">
            <div class="stat-card blue">
              <div class="stat-icon">👥</div>
              <div class="stat-number">{{ stats.studentCount }}</div>
              <div class="stat-label">学生总数</div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="stat-card green">
              <div class="stat-icon">✅</div>
              <div class="stat-number">{{ stats.todayCheckin }}</div>
              <div class="stat-label">今日签到</div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="stat-card orange">
              <div class="stat-icon">📊</div>
              <div class="stat-number">{{ stats.classCount }}</div>
              <div class="stat-label">班级数量</div>
            </div>
          </el-col>
        </el-row>

        <!-- 功能介绍 -->
        <div class="features-section">
          <h3 class="section-title">功能介绍</h3>
          <el-row :gutter="16">
            <el-col :span="8">
              <div class="feature-item">
                <div class="feature-icon blue">📊</div>
                <div class="feature-title">学生管理</div>
                <div class="feature-desc">支持单个添加、批量导入、班级分组管理</div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="feature-item">
                <div class="feature-icon green">📝</div>
                <div class="feature-title">签到系统</div>
                <div class="feature-desc">在线签到，实时统计</div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="feature-item">
                <div class="feature-icon orange">🎯</div>
                <div class="feature-title">分数管理</div>
                <div class="feature-desc">分数增减记录、操作日志、一键重置</div>
              </div>
            </el-col>
          </el-row>
        </div>
      </div>

      <!-- 右侧：分数排行榜 -->
      <div class="right-section">
        <div class="ranking-card">
          <div class="ranking-header">
            <span class="ranking-title">🔥 分数排行榜</span>
            <el-button text circle @click="loadStats" :loading="loading">
              <el-icon><Refresh /></el-icon>
            </el-button>
          </div>
          <div class="ranking-list">
            <div 
              v-for="(student, index) in stats.topStudents" 
              :key="student.student_id"
              class="ranking-item"
              :class="{ 'top3': index < 3 }"
            >
              <div class="rank-number">
                <span v-if="index === 0" class="medal gold">🥇</span>
                <span v-else-if="index === 1" class="medal silver">🥈</span>
                <span v-else-if="index === 2" class="medal bronze">🥉</span>
                <span v-else class="number">{{ index + 1 }}</span>
              </div>
              <div class="student-info">
                <div class="student-name">{{ student.name }}</div>
                <div class="student-class">{{ student.class_name }}</div>
              </div>
              <div class="score" :class="student.score >= 0 ? 'positive' : 'negative'">
                {{ student.score }}分
              </div>
            </div>
            <el-empty v-if="stats.topStudents.length === 0" description="暂无数据" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import * as api from '../api'

const stats = ref({
  studentCount: 0,
  classCount: 0,
  todayCheckin: 0,
  topStudents: []
})
const loading = ref(false)

const loadStats = async () => {
  loading.value = true
  try {
    const res = await api.getStats()
    if (res.success) {
      stats.value = {
        studentCount: res.data.student_count || 0,
        classCount: res.data.class_count || 0,
        todayCheckin: res.data.today_checkin || 0,
        topStudents: res.data.top_students || []
      }
    }
  } catch (error) {
    console.error('加载统计数据失败:', error)
    ElMessage.error('加载统计数据失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadStats()
})
</script>

<style scoped>
.home-container {
  min-height: 100vh;
  background: #f5f7fa;
  padding: 0;
}

/* Hero Section */
.hero-section {
  background: linear-gradient(135deg, #1a5fb4 0%, #3584e4 100%);
  color: white;
  text-align: center;
  padding: 50px 20px;
  margin-bottom: 30px;
}

.hero-section h1 {
  font-size: 42px;
  margin-bottom: 12px;
  font-weight: 600;
}

.subtitle {
  font-size: 18px;
  opacity: 0.9;
  margin-bottom: 30px;
}

.action-buttons {
  display: flex;
  justify-content: center;
  gap: 16px;
}

.action-buttons .el-button {
  font-size: 16px;
  padding: 16px 32px;
  border-radius: 8px;
}

/* Main Content */
.main-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px 40px;
  display: grid;
  grid-template-columns: 1fr 380px;
  gap: 24px;
}

/* Left Section */
.left-section {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* Stats Section */
.stats-section {
  margin: 0 !important;
}

.stat-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  transition: transform 0.3s;
}

.stat-card:hover {
  transform: translateY(-4px);
}

.stat-card.blue {
  border-top: 4px solid #3584e4;
}

.stat-card.green {
  border-top: 4px solid #33d17a;
}

.stat-card.orange {
  border-top: 4px solid #ff7800;
}

.stat-icon {
  font-size: 32px;
  margin-bottom: 8px;
}

.stat-number {
  font-size: 36px;
  font-weight: 700;
  color: #333;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: #666;
}

/* Features Section */
.features-section {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid #eee;
}

.feature-item {
  text-align: center;
  padding: 16px;
}

.feature-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  margin: 0 auto 12px;
}

.feature-icon.blue {
  background: #e8f4fd;
}

.feature-icon.green {
  background: #e8f9ef;
}

.feature-icon.orange {
  background: #fff4e8;
}

.feature-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-bottom: 6px;
}

.feature-desc {
  font-size: 13px;
  color: #666;
  line-height: 1.5;
}

/* Right Section - Ranking */
.right-section {
  position: sticky;
  top: 20px;
  height: fit-content;
}

.ranking-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  overflow: hidden;
}

.ranking-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  background: linear-gradient(135deg, #1a5fb4 0%, #3584e4 100%);
  color: white;
}

.ranking-title {
  font-size: 18px;
  font-weight: 600;
}

.ranking-list {
  padding: 8px;
  max-height: 600px;
  overflow-y: auto;
}

.ranking-item {
  display: flex;
  align-items: center;
  padding: 14px 16px;
  border-radius: 8px;
  margin-bottom: 4px;
  transition: background 0.2s;
}

.ranking-item:hover {
  background: #f5f7fa;
}

.ranking-item.top3 {
  background: #fff9e6;
}

.rank-number {
  width: 40px;
  text-align: center;
  flex-shrink: 0;
}

.medal {
  font-size: 22px;
}

.number {
  font-size: 16px;
  font-weight: 600;
  color: #999;
}

.student-info {
  flex: 1;
  min-width: 0;
  margin-left: 12px;
}

.student-name {
  font-size: 15px;
  font-weight: 500;
  color: #333;
  margin-bottom: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.student-class {
  font-size: 12px;
  color: #999;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.score {
  font-size: 16px;
  font-weight: 600;
  padding: 4px 12px;
  border-radius: 20px;
  background: #f0f0f0;
}

.score.positive {
  color: #33d17a;
  background: #e8f9ef;
}

.score.negative {
  color: #e01b24;
  background: #ffebec;
}

/* Responsive */
@media (max-width: 992px) {
  .main-content {
    grid-template-columns: 1fr;
  }
  
  .right-section {
    position: static;
  }
}

@media (max-width: 768px) {
  .hero-section h1 {
    font-size: 32px;
  }
  
  .stat-number {
    font-size: 28px;
  }
  
  .action-buttons {
    flex-direction: column;
    align-items: center;
  }
  
  .action-buttons .el-button {
    width: 200px;
  }
}
</style>
