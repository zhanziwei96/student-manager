<template>
  <div class="dashboard-container">
    <!-- 顶部数据看板 -->
    <div class="stats-row">
      <div class="stat-card blue">
        <div class="stat-icon">📚</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.classCount }}</div>
          <div class="stat-label">班级数量</div>
        </div>
      </div>
      <div class="stat-card cyan">
        <div class="stat-icon">👨‍🎓</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.studentCount }}</div>
          <div class="stat-label">学生总数</div>
        </div>
      </div>
      <div class="stat-card green">
        <div class="stat-icon">✅</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.todayCheckinRate }}%</div>
          <div class="stat-label">今日签到率</div>
        </div>
        <div class="stat-trend">
          <span class="trend-value">{{ stats.todayCheckin }}/{{ stats.studentCount }}</span>
        </div>
      </div>
      <div class="stat-card orange">
        <div class="stat-icon">📊</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.avgScore }}</div>
          <div class="stat-label">平均分数</div>
        </div>
      </div>
    </div>

    <!-- 快捷操作入口 -->
    <div class="quick-actions">
      <el-button type="primary" size="large" @click="$router.push('/checkin')">
        <el-icon><EditPen /></el-icon>
        学生签到
      </el-button>
      <el-button type="success" size="large" @click="$router.push('/admin')">
        <el-icon><User /></el-icon>
        教师管理
      </el-button>
      <el-button type="warning" size="large" @click="showImportDialog = true">
        <el-icon><Upload /></el-icon>
        批量导入
      </el-button>
    </div>

    <!-- 主内容区：左侧班级 + 右侧学生列表 -->
    <div class="main-content">
      <!-- 左侧班级树形导航 -->
      <div class="class-sidebar">
        <div class="sidebar-header">
          <span class="title">班级列表</span>
          <el-button text @click="loadData" :loading="loading">
            <el-icon><Refresh /></el-icon>
          </el-button>
        </div>
        <div class="class-list">
          <div 
            v-for="cls in classList" 
            :key="cls.className"
            class="class-item"
            :class="{ active: selectedClass === cls.className }"
            @click="selectClass(cls.className)"
          >
            <div class="class-name">{{ cls.className }}</div>
            <div class="class-meta">
              <span class="student-count">{{ cls.studentCount }}人</span>
              <span class="checkin-count" :class="{ 'checked': cls.checkinCount > 0 }">
                {{ cls.checkinCount }}人已签
              </span>
            </div>
            <div class="checkin-rate">
              <el-progress 
                :percentage="Math.round(cls.checkinCount / cls.studentCount * 100)" 
                :stroke-width="4"
                :show-text="false"
                :color="cls.checkinCount / cls.studentCount >= 0.8 ? '#52c41a' : cls.checkinCount / cls.studentCount >= 0.5 ? '#faad14' : '#f5222d'"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧学生列表 -->
      <div class="student-main">
        <!-- 筛选工具栏 -->
        <div class="filter-bar">
          <el-input 
            v-model="searchKeyword" 
            placeholder="搜索姓名或学号" 
            clearable
            style="width: 200px"
            :prefix-icon="Search"
          />
          <el-slider 
            v-model="scoreRange" 
            range 
            :max="100" 
            :min="0"
            style="width: 200px; margin: 0 16px"
          />
          <span class="score-label">分数: {{ scoreRange[0] }}-{{ scoreRange[1] }}</span>
          <el-radio-group v-model="filterCheckin" size="small">
            <el-radio-button label="all">全部</el-radio-button>
            <el-radio-button label="checked">已签到</el-radio-button>
            <el-radio-button label="unchecked">未签到</el-radio-button>
          </el-radio-group>
        </div>

        <!-- 学生表格 -->
        <el-table 
          :data="filteredStudents" 
          stripe
          style="width: 100%"
          :header-cell-style="{ background: '#fafafa' }"
          v-loading="loading"
        >
          <el-table-column type="selection" width="50" />
          <el-table-column prop="student_id" label="学号" width="120" sortable />
          <el-table-column prop="name" label="姓名" width="100" sortable />
          <el-table-column prop="class_name" label="班级" />
          <el-table-column prop="score" label="分数" width="120" sortable>
            <template #default="{ row }">
              <div class="score-cell">
                <el-button 
                  circle 
                  size="small" 
                  type="danger"
                  @click="quickScore(row, -1)"
                >-</el-button>
                <span class="score-value" :class="{ 'positive': row.score >= 70, 'negative': row.score < 60 }">
                  {{ row.score }}
                </span>
                <el-button 
                  circle 
                  size="small" 
                  type="success"
                  @click="quickScore(row, 1)"
                >+</el-button>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="签到状态" width="100">
            <template #default="{ row }">
              <el-tag 
                :type="row.checked_in ? 'success' : 'info'"
                size="small"
              >
                {{ row.checked_in ? '已签到' : '未签到' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="handleCheckin(row)">
                签到
              </el-button>
              <el-button link type="primary" @click="openScoreDialog(row)">
                分数
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <!-- 分页器 -->
        <div class="pagination-bar">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[20, 50, 100]"
            layout="total, sizes, prev, pager, next"
            :total="totalStudents"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { EditPen, User, Upload, Refresh, Search } from '@element-plus/icons-vue'
import * as api from '../api'

// 统计数据
const stats = ref({
  classCount: 0,
  studentCount: 0,
  todayCheckin: 0,
  todayCheckinRate: 0,
  avgScore: 0
})

// 班级列表
const classList = ref([])
const selectedClass = ref('')
const allStudents = ref([])
const loading = ref(false)

// 筛选
const searchKeyword = ref('')
const scoreRange = ref([0, 100])
const filterCheckin = ref('all')

// 分页
const currentPage = ref(1)
const pageSize = ref(20)
const totalStudents = ref(0)

// 计算属性：筛选后的学生
const filteredStudents = computed(() => {
  let result = allStudents.value
  
  // 按班级筛选
  if (selectedClass.value) {
    result = result.filter(s => s.class_name === selectedClass.value)
  }
  
  // 按关键词筛选
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(s => 
      s.name.toLowerCase().includes(keyword) ||
      s.student_id.toLowerCase().includes(keyword)
    )
  }
  
  // 按分数筛选
  result = result.filter(s => 
    s.score >= scoreRange.value[0] && s.score <= scoreRange.value[1]
  )
  
  // 按签到状态筛选
  if (filterCheckin.value === 'checked') {
    result = result.filter(s => s.checked_in)
  } else if (filterCheckin.value === 'unchecked') {
    result = result.filter(s => !s.checked_in)
  }
  
  return result.slice((currentPage.value - 1) * pageSize.value, currentPage.value * pageSize.value)
})

// 加载数据
const loadData = async () => {
  loading.value = true
  try {
    // 加载统计数据
    const statsRes = await api.getStats()
    if (statsRes.success) {
      stats.value = {
        classCount: statsRes.data.class_count || 0,
        studentCount: statsRes.data.student_count || 0,
        todayCheckin: statsRes.data.today_checkin || 0,
        todayCheckinRate: statsRes.data.today_checkin_rate || 0,
        avgScore: statsRes.data.avg_score || 70
      }
      
      // 使用 API 返回的班级统计
      if (statsRes.data.class_stats) {
        classList.value = statsRes.data.class_stats.map(c => ({
          className: c.class_name,
          studentCount: c.student_count,
          checkinCount: c.checkin_count
        }))
      }
    }
    
    // 加载所有学生（包含签到状态）
    const studentsRes = await api.getStudentsWithCheckin()
    if (studentsRes.success) {
      allStudents.value = studentsRes.data
      totalStudents.value = studentsRes.data.length
    }
  } catch (error) {
    console.error('加载数据失败:', error)
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

// 选择班级
const selectClass = (className) => {
  selectedClass.value = selectedClass.value === className ? '' : className
  currentPage.value = 1
}

// 快速修改分数
const quickScore = async (student, delta) => {
  try {
    const res = await api.updateScore(student.student_id, {
      score_change: delta,
      reason: delta > 0 ? '加分' : '扣分'
    })
    if (res.success) {
      student.score += delta
      ElMessage.success(res.message)
    }
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

// 处理签到
const handleCheckin = async (student) => {
  try {
    const res = await api.teacherCheckin({ student_id: student.student_id })
    if (res.success) {
      student.checked_in = true
      ElMessage.success(`${student.name} 签到成功`)
    }
  } catch (error) {
    ElMessage.error('签到失败')
  }
}

// 打开分数对话框
const openScoreDialog = (student) => {
  ElMessageBox.prompt('请输入分数变更（正数加分，负数扣分）', '修改分数', {
    confirmButtonText: '确认',
    cancelButtonText: '取消',
    inputPattern: /^-?\d+$/,
    inputErrorMessage: '请输入有效的数字'
  }).then(({ value }) => {
    quickScore(student, parseInt(value))
  }).catch(() => {})
}

// 分页处理
const handleSizeChange = (size) => {
  pageSize.value = size
  currentPage.value = 1
}

const handleCurrentChange = (page) => {
  currentPage.value = page
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.dashboard-container {
  min-height: 100vh;
  background: #f0f2f5;
  padding: 20px;
}

/* 顶部数据看板 */
.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}

.stat-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  display: flex;
  align-items: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  position: relative;
  overflow: hidden;
}

.stat-card::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
}

.stat-card.blue::before { background: #1890ff; }
.stat-card.cyan::before { background: #13c2c2; }
.stat-card.green::before { background: #52c41a; }
.stat-card.orange::before { background: #fa8c16; }

.stat-icon {
  font-size: 36px;
  margin-right: 16px;
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  background: #f0f5ff;
}

.stat-card.blue .stat-icon { background: #e6f7ff; }
.stat-card.cyan .stat-icon { background: #e6fffb; }
.stat-card.green .stat-icon { background: #f6ffed; }
.stat-card.orange .stat-icon { background: #fff7e6; }

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #262626;
  line-height: 1;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: #8c8c8c;
}

.stat-trend {
  position: absolute;
  right: 16px;
  bottom: 16px;
}

.trend-value {
  font-size: 12px;
  color: #8c8c8c;
}

/* 快捷操作 */
.quick-actions {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.quick-actions .el-button {
  padding: 12px 24px;
}

/* 主内容区 */
.main-content {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 16px;
}

/* 左侧班级栏 */
.class-sidebar {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  overflow: hidden;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.sidebar-header .title {
  font-size: 16px;
  font-weight: 600;
  color: #262626;
}

.class-list {
  max-height: calc(100vh - 300px);
  overflow-y: auto;
}

.class-item {
  padding: 12px 16px;
  cursor: pointer;
  border-bottom: 1px solid #f5f5f5;
  transition: all 0.3s;
}

.class-item:hover {
  background: #f5f5f5;
}

.class-item.active {
  background: #e6f7ff;
  border-left: 3px solid #1890ff;
}

.class-name {
  font-size: 14px;
  font-weight: 500;
  color: #262626;
  margin-bottom: 4px;
}

.class-meta {
  display: flex;
  gap: 8px;
  font-size: 12px;
  color: #8c8c8c;
  margin-bottom: 8px;
}

.checkin-count {
  color: #faad14;
}

.checkin-count.checked {
  color: #52c41a;
}

.checkin-rate {
  margin-top: 4px;
}

/* 右侧学生列表 */
.student-main {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  padding: 16px;
}

.filter-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.score-label {
  font-size: 12px;
  color: #8c8c8c;
  white-space: nowrap;
}

.score-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.score-value {
  font-weight: 600;
  min-width: 40px;
  text-align: center;
}

.score-value.positive {
  color: #52c41a;
}

.score-value.negative {
  color: #f5222d;
}

.pagination-bar {
  display: flex;
  justify-content: flex-end;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
  margin-top: 16px;
}

/* 响应式 */
@media (max-width: 1200px) {
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .main-content {
    grid-template-columns: 1fr;
  }
  
  .class-sidebar {
    display: none;
  }
  
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
