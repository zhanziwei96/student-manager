<template>
  <div class="public-home">
    <!-- 顶部导航 -->
    <header class="header">
      <div class="header-content">
        <h1 class="logo">📚 班级管理系统</h1>
        <div class="header-actions">
          <el-button type="primary" @click="$router.push('/login')">
            教师登录
          </el-button>
        </div>
      </div>
    </header>

    <!-- 主内容区 -->
    <main class="main-content">
      <div class="container">
        <!-- 分数排行榜 -->
        <div class="ranking-section">
          <div class="section-header">
            <h2>🏆 分数排行榜 TOP 10</h2>
            <el-button text @click="loadData" :loading="loading">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
          
          <el-card class="ranking-card" shadow="hover">
            <el-table 
              :data="topStudents" 
              stripe
              style="width: 100%"
              :header-cell-style="{ background: '#fafafa', fontWeight: 600 }"
              v-loading="loading"
            >
              <el-table-column label="排名" width="100" align="center">
                <template #default="{ $index }">
                  <div class="rank-cell">
                    <span v-if="$index === 0" class="rank-medal gold">🥇</span>
                    <span v-else-if="$index === 1" class="rank-medal silver">🥈</span>
                    <span v-else-if="$index === 2" class="rank-medal bronze">🥉</span>
                    <span v-else class="rank-number">{{ $index + 1 }}</span>
                  </div>
                </template>
              </el-table-column>
              
              <el-table-column prop="name" label="姓名" min-width="120">
                <template #default="{ row }">
                  <span class="student-name">{{ row.name }}</span>
                </template>
              </el-table-column>
              
              <el-table-column prop="class_name" label="班级" min-width="180">
                <template #default="{ row }">
                  <el-tag size="small" effect="plain">{{ row.class_name }}</el-tag>
                </template>
              </el-table-column>
              
              <el-table-column prop="score" label="分数" width="120" align="center">
                <template #default="{ row }">
                  <span 
                    class="score-value" 
                    :class="{ 'high': row.score >= 80, 'medium': row.score >= 60 && row.score < 80, 'low': row.score < 60 }"
                  >
                    {{ row.score }}
                  </span>
                </template>
              </el-table-column>
            </el-table>
            
            <el-empty v-if="!loading && topStudents.length === 0" description="暂无数据" />
          </el-card>
        </div>

        <!-- 统计概览 -->
        <div class="stats-section">
          <el-row :gutter="16">
            <el-col :span="8">
              <div class="stat-item">
                <div class="stat-icon blue">📚</div>
                <div class="stat-info">
                  <div class="stat-value">{{ stats.classCount }}</div>
                  <div class="stat-label">班级数量</div>
                </div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="stat-item">
                <div class="stat-icon green">👨‍🎓</div>
                <div class="stat-info">
                  <div class="stat-value">{{ stats.studentCount }}</div>
                  <div class="stat-label">学生总数</div>
                </div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="stat-item">
                <div class="stat-icon orange">📊</div>
                <div class="stat-info">
                  <div class="stat-value">{{ stats.avgScore }}</div>
                  <div class="stat-label">平均分数</div>
                </div>
              </div>
            </el-col>
          </el-row>
        </div>
      </div>
    </main>

    <!-- 底部 -->
    <footer class="footer">
      <p>班级管理系统 © 2025 | 技术支持请联系管理员</p>
    </footer>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import * as api from '../api'

const loading = ref(false)
const topStudents = ref([])
const stats = ref({
  classCount: 0,
  studentCount: 0,
  avgScore: 0
})

const loadData = async () => {
  loading.value = true
  try {
    const res = await api.getStats()
    if (res.success) {
      topStudents.value = res.data.top_students || []
      stats.value = {
        classCount: res.data.class_count || 0,
        studentCount: res.data.student_count || 0,
        avgScore: res.data.avg_score || 0
      }
    }
  } catch (error) {
    console.error('加载数据失败:', error)
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.public-home {
  min-height: 100vh;
  background: #f5f7fa;
  display: flex;
  flex-direction: column;
}

/* 顶部导航 */
.header {
  background: linear-gradient(135deg, #1890ff 0%, #36cfc9 100%);
  padding: 0 24px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.logo {
  color: white;
  font-size: 20px;
  font-weight: 600;
  margin: 0;
}

/* 主内容区 */
.main-content {
  flex: 1;
  padding: 24px;
}

.container {
  max-width: 900px;
  margin: 0 auto;
}

/* 排行榜区域 */
.ranking-section {
  margin-bottom: 24px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-header h2 {
  margin: 0;
  font-size: 20px;
  color: #262626;
}

.ranking-card {
  border-radius: 12px;
}

.rank-cell {
  display: flex;
  align-items: center;
  justify-content: center;
}

.rank-medal {
  font-size: 24px;
}

.rank-number {
  font-size: 16px;
  font-weight: 600;
  color: #595959;
}

.student-name {
  font-weight: 500;
  color: #262626;
}

.score-value {
  font-size: 18px;
  font-weight: 700;
  padding: 4px 12px;
  border-radius: 12px;
}

.score-value.high {
  color: #52c41a;
  background: #f6ffed;
}

.score-value.medium {
  color: #faad14;
  background: #fffbe6;
}

.score-value.low {
  color: #f5222d;
  background: #fff1f0;
}

/* 统计区域 */
.stats-section {
  margin-top: 24px;
}

.stat-item {
  background: white;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.stat-icon {
  font-size: 32px;
  margin-right: 16px;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #262626;
}

.stat-label {
  font-size: 14px;
  color: #8c8c8c;
}

/* 底部 */
.footer {
  background: white;
  padding: 20px;
  text-align: center;
  border-top: 1px solid #f0f0f0;
}

.footer p {
  margin: 0;
  color: #8c8c8c;
  font-size: 14px;
}

/* 响应式 */
@media (max-width: 768px) {
  .header-content {
    padding: 0 16px;
  }
  
  .main-content {
    padding: 16px;
  }
  
  .stats-section .el-col {
    margin-bottom: 12px;
  }
}
</style>
