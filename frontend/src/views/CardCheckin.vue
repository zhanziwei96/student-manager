<template>
  <div class="checkin-container">
    <!-- 顶部导航 -->
    <div class="checkin-header">
      <div class="header-left">
        <h2>📝 学生签到</h2>
        <p class="subtitle">选择班级查看学生签到状态</p>
      </div>
      <div class="header-actions">
        <el-select v-model="selectedClass" placeholder="选择班级" clearable style="width: 180px">
          <el-option 
            v-for="cls in classList" 
            :key="cls.className" 
            :label="cls.className" 
            :value="cls.className"
          />
        </el-select>
        <el-button type="primary" @click="showScanDialog = true">
          <el-icon><Camera /></el-icon>
          扫码签到
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-bar">
      <div class="stat-item">
        <span class="stat-label">总人数</span>
        <span class="stat-value">{{ filteredStudents.length }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">已签到</span>
        <span class="stat-value success">{{ checkedInCount }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">未签到</span>
        <span class="stat-value warning">{{ uncheckedCount }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">签到率</span>
        <span class="stat-value primary">{{ checkinRate }}%</span>
      </div>
    </div>

    <!-- 筛选标签 -->
    <div class="filter-tabs">
      <el-radio-group v-model="filterStatus" size="large">
        <el-radio-button label="all">全部</el-radio-button>
        <el-radio-button label="unchecked">未签到</el-radio-button>
        <el-radio-button label="checked">已签到</el-radio-button>
      </el-radio-group>
      <el-input 
        v-model="searchKeyword" 
        placeholder="搜索姓名或学号" 
        clearable
        style="width: 200px"
        :prefix-icon="Search"
      />
    </div>

    <!-- 学生卡片网格 -->
    <div class="students-grid">
      <div 
        v-for="student in displayStudents" 
        :key="student.student_id"
        class="student-card"
        :class="{ 'checked': student.checked_in, 'unchecked': !student.checked_in }"
      >
        <div class="card-header">
          <div class="avatar">
            {{ student.name.charAt(0) }}
          </div>
          <div class="header-info">
            <div class="student-name">{{ student.name }}</div>
            <div class="student-id">{{ student.student_id }}</div>
          </div>
          <el-tag 
            :type="student.checked_in ? 'success' : 'info'"
            size="small"
            effect="dark"
          >
            {{ student.checked_in ? '已签到' : '未签到' }}
          </el-tag>
        </div>
        
        <div class="card-body">
          <div class="info-row">
            <span class="label">班级</span>
            <span class="value">{{ student.class_name }}</span>
          </div>
          <div class="info-row">
            <span class="label">当前分数</span>
            <span class="score" :class="{ 'high': student.score >= 70, 'low': student.score < 60 }">
              {{ student.score }}分
            </span>
          </div>
          <div v-if="student.checkin_time" class="info-row">
            <span class="label">签到时间</span>
            <span class="value">{{ formatTime(student.checkin_time) }}</span>
          </div>
        </div>
        
        <div class="card-footer">
          <el-button 
            v-if="!student.checked_in"
            type="primary" 
            size="large"
            class="checkin-btn"
            @click="handleCheckin(student)"
            :loading="student.loading"
          >
            立即签到
          </el-button>
          <el-button 
            v-else
            type="success" 
            size="large"
            class="checkin-btn"
            disabled
          >
            <el-icon><Check /></el-icon>
            已完成
          </el-button>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <el-empty v-if="displayStudents.length === 0" description="暂无学生数据" />

    <!-- 扫码签到对话框 -->
    <el-dialog v-model="showScanDialog" title="扫码签到" width="400px" center>
      <div class="scan-container">
        <div class="scan-placeholder">
          <el-icon :size="64"><Camera /></el-icon>
          <p>相机功能开发中...</p>
          <p class="hint">请使用手动签到</p>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Camera, Search, Check } from '@element-plus/icons-vue'
import * as api from '../api'

// 数据
const classList = ref([])
const allStudents = ref([])
const selectedClass = ref('')
const filterStatus = ref('all')
const searchKeyword = ref('')
const showScanDialog = ref(false)
const loading = ref(false)

// 计算属性
const filteredStudents = computed(() => {
  let result = allStudents.value
  
  // 按班级筛选
  if (selectedClass.value) {
    result = result.filter(s => s.class_name === selectedClass.value)
  }
  
  // 按签到状态筛选
  if (filterStatus.value === 'checked') {
    result = result.filter(s => s.checked_in)
  } else if (filterStatus.value === 'unchecked') {
    result = result.filter(s => !s.checked_in)
  }
  
  // 按关键词搜索
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(s => 
      s.name.toLowerCase().includes(keyword) ||
      s.student_id.toLowerCase().includes(keyword)
    )
  }
  
  return result
})

const displayStudents = computed(() => filteredStudents.value)

const checkedInCount = computed(() => filteredStudents.value.filter(s => s.checked_in).length)
const uncheckedCount = computed(() => filteredStudents.value.filter(s => !s.checked_in).length)
const checkinRate = computed(() => {
  const total = filteredStudents.value.length
  return total > 0 ? Math.round(checkedInCount.value / total * 100) : 0
})

// 加载数据
const loadData = async () => {
  loading.value = true
  try {
    const [studentsRes, statsRes] = await Promise.all([
      api.getStudentsWithCheckin(),
      api.getStats()
    ])
    
    if (studentsRes.success) {
      allStudents.value = studentsRes.data.map(s => ({ ...s, loading: false }))
    }
    
    if (statsRes.success && statsRes.data.class_stats) {
      classList.value = statsRes.data.class_stats.map(c => ({
        className: c.class_name,
        studentCount: c.student_count
      }))
    }
  } catch (error) {
    console.error('加载数据失败:', error)
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

// 处理签到
const handleCheckin = async (student) => {
  student.loading = true
  try {
    const res = await api.teacherCheckin({ student_id: student.student_id })
    if (res.success) {
      student.checked_in = true
      student.checkin_time = new Date().toISOString()
      ElMessage.success(`${student.name} 签到成功`)
    }
  } catch (error) {
    ElMessage.error('签到失败')
  } finally {
    student.loading = false
  }
}

// 格式化时间
const formatTime = (time) => {
  if (!time) return ''
  const date = new Date(time)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.checkin-container {
  min-height: 100vh;
  background: #f5f7fa;
  padding: 24px;
}

/* 顶部导航 */
.checkin-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  background: white;
  padding: 20px 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.header-left h2 {
  margin: 0 0 4px 0;
  font-size: 24px;
  color: #262626;
}

.subtitle {
  margin: 0;
  color: #8c8c8c;
  font-size: 14px;
}

.header-actions {
  display: flex;
  gap: 12px;
}

/* 统计栏 */
.stats-bar {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
  background: white;
  padding: 16px 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0 24px;
  border-right: 1px solid #f0f0f0;
}

.stat-item:last-child {
  border-right: none;
}

.stat-label {
  font-size: 13px;
  color: #8c8c8c;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #262626;
}

.stat-value.success {
  color: #52c41a;
}

.stat-value.warning {
  color: #faad14;
}

.stat-value.primary {
  color: #1890ff;
}

/* 筛选标签 */
.filter-tabs {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

/* 学生卡片网格 */
.students-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.student-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  transition: all 0.3s;
  border: 2px solid transparent;
}

.student-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.12);
}

.student-card.checked {
  border-color: #52c41a;
  background: #f6ffed;
}

.student-card.unchecked {
  border-color: #d9d9d9;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(135deg, #1890ff 0%, #36cfc9 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 600;
}

.header-info {
  flex: 1;
  min-width: 0;
}

.student-name {
  font-size: 16px;
  font-weight: 600;
  color: #262626;
  margin-bottom: 2px;
}

.student-id {
  font-size: 13px;
  color: #8c8c8c;
}

.card-body {
  margin-bottom: 16px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #f5f5f5;
}

.info-row:last-child {
  border-bottom: none;
}

.label {
  font-size: 13px;
  color: #8c8c8c;
}

.value {
  font-size: 14px;
  color: #262626;
}

.score {
  font-size: 16px;
  font-weight: 600;
}

.score.high {
  color: #52c41a;
}

.score.low {
  color: #f5222d;
}

.card-footer {
  padding-top: 12px;
}

.checkin-btn {
  width: 100%;
  height: 44px;
  font-size: 15px;
}

/* 扫码容器 */
.scan-container {
  padding: 40px;
  text-align: center;
}

.scan-placeholder {
  color: #8c8c8c;
}

.scan-placeholder .hint {
  color: #bfbfbf;
  font-size: 13px;
}

/* 响应式 */
@media (max-width: 768px) {
  .checkin-container {
    padding: 12px;
  }
  
  .checkin-header {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }
  
  .stats-bar {
    flex-wrap: wrap;
  }
  
  .stat-item {
    flex: 1;
    min-width: 80px;
    padding: 0 12px;
  }
  
  .students-grid {
    grid-template-columns: 1fr;
  }
  
  .filter-tabs {
    flex-direction: column;
    gap: 12px;
  }
}
</style>
