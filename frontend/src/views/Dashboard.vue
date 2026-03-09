<template>
  <div class="dashboard-container">
    <!-- 顶部导航栏 -->
    <header class="top-header">
      <div class="header-left">
        <h2 class="page-title">📊 管理后台</h2>
      </div>
      <div class="header-right">
        <el-button text @click="$router.push('/')">
          <el-icon><Home /></el-icon>
          返回首页
        </el-button>
        <el-dropdown @command="handleCommand">
          <span class="user-info">
            👨‍🏫 {{ userName }}
            <el-icon><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="admin">系统管理</el-dropdown-item>
              <el-dropdown-item command="password">修改密码</el-dropdown-item>
              <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </header>
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
      <el-button text @click="refreshAllData" :loading="loading">
        <el-icon><Refresh /></el-icon>
        刷新数据
      </el-button>
    </div>

    <!-- 主内容区：左侧班级 + 右侧学生列表 -->
    <div class="main-content">
      <!-- 左侧班级树形导航 -->
      <div class="class-sidebar">
        <div class="sidebar-header">
          <span class="title">班级列表</span>
          <span class="count">{{ classList.length }}个班级</span>
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
            style="width: 220px"
            :prefix-icon="Search"
          />
          <el-slider 
            v-model="scoreRange" 
            range 
            :max="100" 
            :min="0"
            style="width: 200px; margin: 0 16px"
          />
          <span class="score-label">{{ scoreRange[0] }}-{{ scoreRange[1] }}分</span>
          <el-radio-group v-model="filterCheckin" size="small">
            <el-radio-button label="all">全部</el-radio-button>
            <el-radio-button label="checked">已签到</el-radio-button>
            <el-radio-button label="unchecked">未签到</el-radio-button>
          </el-radio-group>
          <el-tag v-if="filteredStudents.length !== allStudents.length" type="info" size="small">
            显示 {{ filteredStudents.length }}/{{ allStudents.length }} 人
          </el-tag>
        </div>

        <!-- 学生表格 -->
        <div class="table-container" v-loading="loading">
          <!-- 数据量小使用普通表格 -->
          <el-table 
            v-if="filteredStudents.length <= 100"
            :data="pagedStudents" 
            stripe
            style="width: 100%"
            :header-cell-style="{ background: '#fafafa' }"
            @sort-change="handleSortChange"
          >
            <el-table-column type="selection" width="50" />
            <el-table-column prop="student_id" label="学号" width="120" sortable />
            <el-table-column prop="name" label="姓名" width="100" sortable />
            <el-table-column prop="class_name" label="班级" sortable />
            <el-table-column prop="score" label="分数" width="140" sortable>
              <template #default="{ row }">
                <div class="score-cell">
                  <el-button 
                    circle 
                    size="small" 
                    type="danger"
                    :disabled="row._updating"
                    @click="quickScore(row, -1)"
                  >
                    <el-icon v-if="row._updating && row._pendingScore < 0" class="is-loading"><Loading /></el-icon>
                    <span v-else>-</span>
                  </el-button>
                  <span class="score-value" :class="{ 'positive': row.score >= 70, 'negative': row.score < 60, 'pending': row._pendingScore !== undefined }">
                    {{ row._pendingScore !== undefined ? row._pendingScore : row.score }}
                  </span>
                  <el-button 
                    circle 
                    size="small" 
                    type="success"
                    :disabled="row._updating"
                    @click="quickScore(row, 1)"
                  >
                    <el-icon v-if="row._updating && row._pendingScore > 0" class="is-loading"><Loading /></el-icon>
                    <span v-else>+</span>
                  </el-button>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="签到状态" width="100">
              <template #default="{ row }">
                <el-tag 
                  :type="row.checked_in ? 'success' : 'info'"
                  size="small"
                  :effect="row.checked_in ? 'dark' : 'plain'"
                >
                  {{ row.checked_in ? '已签到' : '未签到' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="180" fixed="right">
              <template #default="{ row }">
                <el-button 
                  v-if="!row.checked_in" 
                  link 
                  type="primary" 
                  :loading="row._checkingIn"
                  @click="handleCheckin(row)"
                >
                  签到
                </el-button>
                <el-button v-else link type="success" disabled>已签到</el-button>
                <el-button link type="primary" @click="openScoreDialog(row)">
                  分数
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <!-- 数据量大使用虚拟滚动 -->
          <div v-else class="virtual-table-container">
            <div class="virtual-table-header">
              <div class="th" style="width: 50px">
                <el-checkbox v-model="selectAll" @change="handleSelectAll" />
              </div>
              <div class="th" style="width: 120px">学号</div>
              <div class="th" style="width: 100px">姓名</div>
              <div class="th" style="flex: 1">班级</div>
              <div class="th" style="width: 140px">分数</div>
              <div class="th" style="width: 100px">签到状态</div>
              <div class="th" style="width: 180px">操作</div>
            </div>
            <VirtualList
              :data="filteredStudents"
              :item-height="60"
              key-prop="student_id"
              style="height: calc(100% - 50px)"
            >
              <template #default="{ item, index }">
                <div class="virtual-table-row">
                  <div class="td" style="width: 50px">
                    <el-checkbox v-model="item._selected" />
                  </div>
                  <div class="td" style="width: 120px">{{ item.student_id }}</div>
                  <div class="td" style="width: 100px">{{ item.name }}</div>
                  <div class="td" style="flex: 1">{{ item.class_name }}</div>
                  <div class="td" style="width: 140px">
                    <div class="score-cell">
                      <el-button circle size="small" type="danger" @click="quickScore(item, -1)">-</el-button>
                      <span class="score-value">{{ item.score }}</span>
                      <el-button circle size="small" type="success" @click="quickScore(item, 1)">+</el-button>
                    </div>
                  </div>
                  <div class="td" style="width: 100px">
                    <el-tag :type="item.checked_in ? 'success' : 'info'" size="small">
                      {{ item.checked_in ? '已签到' : '未签到' }}
                    </el-tag>
                  </div>
                  <div class="td" style="width: 180px">
                    <el-button v-if="!item.checked_in" link type="primary" @click="handleCheckin(item)">签到</el-button>
                    <el-button link type="primary" @click="openScoreDialog(item)">分数</el-button>
                  </div>
                </div>
              </template>
            </VirtualList>
          </div>
        </div>

        <!-- 分页器 -->
        <div class="pagination-bar" v-if="filteredStudents.length <= 100">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            :total="filteredStudents.length"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
        <div v-else class="virtual-scroll-hint">
          <el-alert type="info" :closable="false" show-icon>
            <template #title>
              数据量较大，已启用虚拟滚动，支持流畅展示 {{ filteredStudents.length }} 条数据
            </template>
          </el-alert>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { EditPen, User, Upload, Refresh, Search, Loading, Home, ArrowDown } from '@element-plus/icons-vue'
import Cookies from 'js-cookie'
import VirtualList from '../components/VirtualList.vue'
import { cache, CACHE_KEYS } from '../utils/cache'
import { debounce } from '../utils'
import * as api from '../api'

const router = useRouter()

// 用户名称
const userName = ref(Cookies.get('name') || '教师')

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
const sortConfig = ref({ prop: '', order: '' })

// 分页
const currentPage = ref(1)
const pageSize = ref(20)
const selectAll = ref(false)

// 计算属性：筛选后的学生
const filteredStudents = computed(() => {
  let result = [...allStudents.value]
  
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
  
  // 排序
  if (sortConfig.value.prop && sortConfig.value.order) {
    const { prop, order } = sortConfig.value
    result.sort((a, b) => {
      let comparison = 0
      if (typeof a[prop] === 'string') {
        comparison = a[prop].localeCompare(b[prop])
      } else {
        comparison = a[prop] - b[prop]
      }
      return order === 'ascending' ? comparison : -comparison
    })
  }
  
  return result
})

// 分页后的数据
const pagedStudents = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredStudents.value.slice(start, start + pageSize.value)
})

// 加载数据（带缓存）
const loadData = async (forceRefresh = false) => {
  loading.value = true
  
  try {
    // 尝试从缓存读取
    if (!forceRefresh) {
      const cachedStats = cache.get(CACHE_KEYS.STATS)
      const cachedStudents = cache.get(CACHE_KEYS.STUDENTS)
      
      if (cachedStats && cachedStudents) {
        stats.value = cachedStats
        classList.value = cachedStats.classStats || []
        allStudents.value = cachedStudents
        loading.value = false
        return
      }
    }
    
    // 并行请求统计数据和学生列表
    const [statsRes, studentsRes] = await Promise.all([
      api.getStats(),
      api.getStudentsWithCheckin()
    ])
    
    if (statsRes.success) {
      stats.value = {
        classCount: statsRes.data.class_count || 0,
        studentCount: statsRes.data.student_count || 0,
        todayCheckin: statsRes.data.today_checkin || 0,
        todayCheckinRate: statsRes.data.today_checkin_rate || 0,
        avgScore: statsRes.data.avg_score || 70
      }
      
      // 缓存统计数据
      cache.set(CACHE_KEYS.STATS, stats.value)
      
      // 处理班级列表
      if (statsRes.data.class_stats) {
        classList.value = statsRes.data.class_stats.map(c => ({
          className: c.class_name,
          studentCount: c.student_count,
          checkinCount: c.checkin_count
        }))
      }
    }
    
    if (studentsRes.success) {
      allStudents.value = studentsRes.data
      // 缓存学生数据
      cache.set(CACHE_KEYS.STUDENTS, allStudents.value)
    }
  } catch (error) {
    console.error('加载数据失败:', error)
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

// 强制刷新所有数据
const refreshAllData = () => {
  cache.delete(CACHE_KEYS.STATS)
  cache.delete(CACHE_KEYS.STUDENTS)
  loadData(true)
}

// 选择班级
const selectClass = (className) => {
  selectedClass.value = selectedClass.value === className ? '' : className
  currentPage.value = 1
}

// 快速修改分数（乐观更新）
const quickScore = async (student, delta) => {
  // 乐观更新：先改 UI
  const originalScore = student.score
  const pendingScore = originalScore + delta
  student._pendingScore = pendingScore
  student._updating = true
  
  try {
    const res = await api.updateScore(student.student_id, {
      score_change: delta,
      reason: delta > 0 ? '加分' : '扣分'
    })
    
    if (res.success) {
      // 更新成功
      student.score = pendingScore
      ElMessage.success(res.message)
      
      // 更新缓存中的数据
      updateCacheStudent(student.student_id, { score: student.score })
    } else {
      // 更新失败，恢复原值
      ElMessage.error(res.message)
    }
  } catch (error) {
    ElMessage.error('操作失败')
  } finally {
    student._updating = false
    student._pendingScore = undefined
  }
}

// 更新缓存中的学生数据（增量更新）
const updateCacheStudent = (studentId, updates) => {
  const cachedStudents = cache.get(CACHE_KEYS.STUDENTS)
  if (cachedStudents) {
    const student = cachedStudents.find(s => s.student_id === studentId)
    if (student) {
      Object.assign(student, updates)
      cache.set(CACHE_KEYS.STUDENTS, cachedStudents)
    }
  }
}

// 处理签到（乐观更新）
const handleCheckin = async (student) => {
  student._checkingIn = true
  
  // 乐观更新
  const wasCheckedIn = student.checked_in
  student.checked_in = true
  
  try {
    const res = await api.teacherCheckin({ student_id: student.student_id })
    if (res.success) {
      ElMessage.success(`${student.name} 签到成功`)
      
      // 更新缓存
      updateCacheStudent(student.student_id, { checked_in: true })
      
      // 更新班级签到数
      const classItem = classList.value.find(c => c.className === student.class_name)
      if (classItem) {
        classItem.checkinCount++
      }
      stats.value.todayCheckin++
    } else {
      // 失败回滚
      student.checked_in = wasCheckedIn
      ElMessage.error(res.message)
    }
  } catch (error) {
    student.checked_in = wasCheckedIn
    ElMessage.error('签到失败')
  } finally {
    student._checkingIn = false
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
    const delta = parseInt(value)
    const originalScore = student.score
    student.score += delta
    
    api.updateScore(student.student_id, {
      score_change: delta,
      reason: '手动调整分数'
    }).then(res => {
      if (res.success) {
        ElMessage.success(res.message)
        updateCacheStudent(student.student_id, { score: student.score })
      } else {
        student.score = originalScore
        ElMessage.error(res.message)
      }
    }).catch(() => {
      student.score = originalScore
      ElMessage.error('操作失败')
    })
  }).catch(() => {})
}

// 处理下拉菜单命令
const handleCommand = (command) => {
  switch (command) {
    case 'admin':
      router.push('/admin')
      break
    case 'password':
      // 预留修改密码功能
      ElMessage.info('修改密码功能开发中')
      break
    case 'logout':
      handleLogout()
      break
  }
}

// 退出登录
const handleLogout = () => {
  Cookies.remove('user_id')
  Cookies.remove('username')
  Cookies.remove('name')
  ElMessage.success('已退出登录')
  router.push('/')
}

// 处理排序
const handleSortChange = ({ prop, order }) => {
  sortConfig.value = { prop, order }
  currentPage.value = 1
}

// 分页处理
const handleSizeChange = (size) => {
  pageSize.value = size
  currentPage.value = 1
}

const handleCurrentChange = (page) => {
  currentPage.value = page
}

// 全选处理
const handleSelectAll = (val) => {
  pagedStudents.value.forEach(s => s._selected = val)
}

// Debounce 搜索
const debouncedSearch = debounce(() => {
  currentPage.value = 1
}, 300)

// 监听搜索关键词变化
watch(searchKeyword, () => {
  debouncedSearch()
})

// 监听筛选条件变化，重置分页
watch([selectedClass, scoreRange, filterCheckin], () => {
  currentPage.value = 1
})

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

/* 顶部导航栏 */
.top-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
  padding: 12px 20px;
  border-radius: 8px;
  margin-bottom: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.page-title {
  margin: 0;
  font-size: 18px;
  color: #262626;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-info {
  cursor: pointer;
  color: #595959;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.user-info:hover {
  color: #1890ff;
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

.sidebar-header .count {
  font-size: 12px;
  color: #8c8c8c;
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

.table-container {
  min-height: 400px;
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
  transition: all 0.3s;
}

.score-value.positive {
  color: #52c41a;
}

.score-value.negative {
  color: #f5222d;
}

.score-value.pending {
  color: #1890ff;
  font-style: italic;
}

.pagination-bar {
  display: flex;
  justify-content: flex-end;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
  margin-top: 16px;
}

.virtual-scroll-hint {
  margin-top: 16px;
}

/* 虚拟滚动表格 */
.virtual-table-container {
  height: 500px;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
}

.virtual-table-header {
  display: flex;
  background: #fafafa;
  border-bottom: 1px solid #f0f0f0;
  padding: 12px 0;
  font-weight: 600;
  color: #262626;
}

.virtual-table-header .th {
  padding: 0 12px;
}

.virtual-table-row {
  display: flex;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #f5f5f5;
}

.virtual-table-row:hover {
  background: #f5f7fa;
}

.virtual-table-row .td {
  padding: 0 12px;
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
