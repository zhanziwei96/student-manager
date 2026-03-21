<template>
  <div class="admin-layout">
    <!-- 顶部导航 -->
    <header class="admin-header">
      <div class="header-left">
        <div class="logo">
          <div class="logo-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 2L2 7l10 5 10-5-10-5z"/>
              <path d="M2 17l10 5 10-5"/>
            </svg>
          </div>
          <h1>ClassHub</h1>
        </div>
        <n-tag type="info" size="small" round>教师工作台</n-tag>
      </div>
      <div class="header-right">
        <n-button type="primary" @click="$router.push('/checkin')" class="checkin-btn">
          <template #icon>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 16px; height: 16px;">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
            </svg>
          </template>
          学生签到
        </n-button>
        <n-dropdown :options="userOptions" @select="handleUserAction">
          <div class="user-info">
            <div class="user-avatar">{{ userName.charAt(0) }}</div>
            <span class="username">{{ userName }}</span>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 14px; height: 14px;">
              <polyline points="6 9 12 15 18 9"/>
            </svg>
          </div>
        </n-dropdown>
      </div>
    </header>

    <!-- 主内容 -->
    <main class="admin-main">
      <!-- 上课控制卡片 -->
      <n-card class="control-card" :class="{ active: classSession.active }">
        <template #header>
          <div class="card-header">
            <div class="header-title">
              <svg v-if="!classSession.active" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 20px; height: 20px;">
                <polygon points="5 3 19 12 5 21 5 3"/>
              </svg>
              <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 20px; height: 20px;">
                <rect x="6" y="4" width="4" height="16"/>
                <rect x="14" y="4" width="4" height="16"/>
              </svg>
              <span>{{ classSession.active ? '上课中' : '上课控制' }}</span>
            </div>
            <n-tag v-if="classSession.active" type="success" round>
              {{ classSession.class_name }}
            </n-tag>
          </div>
        </template>

        <div v-if="!classSession.active" class="class-selector">
          <n-select v-model:value="selectedClass" placeholder="选择上课班级" style="width: 280px;" :options="classOptions" />
          <n-button type="success" size="large" @click="startClass" :disabled="!selectedClass">
            <template #icon>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 16px; height: 16px;">
                <polygon points="5 3 19 12 5 21 5 3"/>
              </svg>
            </template>
            开始上课
          </n-button>
        </div>

        <div v-else class="class-info">
          <div class="stats-row-enhanced">
            <!-- 应到人数 -->
            <div class="stat-box">
              <div class="stat-number">{{ classStats.total }}</div>
              <div class="stat-label">应到人数</div>
            </div>
            <!-- 已签到 -->
            <div class="stat-box success">
              <div class="stat-number">{{ classStats.checked_in }}</div>
              <div class="stat-label">已签到</div>
              <div class="stat-indicator success-dot"></div>
            </div>
            <!-- 未签到 -->
            <div class="stat-box danger">
              <div class="stat-number">{{ classStats.not_checked_in }}</div>
              <div class="stat-label">未签到</div>
              <div class="stat-indicator danger-dot"></div>
            </div>
            <!-- 签到率 -->
            <div class="stat-box rate-box">
              <n-progress
                type="circle"
                :percentage="classStats.rate"
                :stroke-width="10"
                :width="100"
                :color="getRateColor(classStats.rate)"
                :track-color="'rgba(255, 255, 255, 0.1)'"
              >
                <div class="rate-text">{{ classStats.rate }}%</div>
              </n-progress>
              <div class="stat-label">签到率</div>
            </div>
          </div>
          <div class="class-actions">
            <n-button @click="refreshClassStatus">
              <template #icon>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 14px; height: 14px;">
                  <polyline points="23 4 23 10 17 10"/>
                  <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
                </svg>
              </template>
              刷新状态
            </n-button>
            <n-button type="error" @click="endClass">
              <template #icon>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 14px; height: 14px;">
                  <circle cx="12" cy="12" r="10"/>
                  <line x1="15" y1="9" x2="9" y2="15"/>
                  <line x1="9" y1="9" x2="15" y2="15"/>
                </svg>
              </template>
              结束上课
            </n-button>
          </div>
        </div>
      </n-card>

      <!-- 我的统计卡片 -->
      <n-card class="stats-card" title="我的班级统计">
        <div class="teacher-stats">
          <div class="stat-item">
            <div class="stat-value">{{ myClasses.length }}</div>
            <div class="stat-label">负责班级</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ myStudents.length }}</div>
            <div class="stat-label">学生总数</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ classAverageScore }}</div>
            <div class="stat-label">班级均分</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ todayCheckinRate }}%</div>
            <div class="stat-label">今日签到率</div>
          </div>
        </div>
      </n-card>

      <!-- 快捷操作 -->
      <div class="quick-actions">
        <n-card class="action-card" hoverable @click="showAddStudent = true">
          <div class="action-icon" style="background: linear-gradient(135deg, #6366f1, #8b5cf6);">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
              <circle cx="12" cy="7" r="4"/>
            </svg>
          </div>
          <div class="action-title">添加学生</div>
          <div class="action-desc">单个添加学生信息</div>
        </n-card>

        <n-card class="action-card" hoverable @click="showImport = true">
          <div class="action-icon" style="background: linear-gradient(135deg, #10b981, #34d399);">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="17 8 12 3 7 8"/>
              <line x1="12" y1="3" x2="12" y2="15"/>
            </svg>
          </div>
          <div class="action-title">导入班级</div>
          <div class="action-desc">批量导入Excel文件</div>
        </n-card>
      </div>

      <!-- 学生列表 -->
      <n-card class="student-list-card">
        <template #header>
          <div class="list-header">
            <div class="header-title">
              <span>我的学生</span>
              <n-tag type="info" size="small">共 {{ myStudents.length }} 人</n-tag>
            </div>
            <div class="header-actions">
              <n-input v-model:value="searchQuery" placeholder="搜索学号或姓名" style="width: 200px;" clearable>
                <template #prefix>
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 16px; height: 16px;">
                    <circle cx="11" cy="11" r="8"/>
                    <path d="M21 21l-4.35-4.35"/>
                  </svg>
                </template>
              </n-input>
              <n-button-group>
                <n-button @click="expandAll">全部展开</n-button>
                <n-button @click="collapseAll">全部折叠</n-button>
                <n-button type="primary" @click="loadStudents">
                  <template #icon>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 14px; height: 14px;">
                      <polyline points="23 4 23 10 17 10"/>
                      <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
                    </svg>
                  </template>
                  刷新
                </n-button>
              </n-button-group>
            </div>
          </div>
        </template>

        <div class="class-groups">
          <n-collapse v-model:expanded-names="activeGroups">
            <n-collapse-item v-for="group in groupedStudents" :key="group.className" :name="group.className" :title="group.className">
              <template #header-extra>
                <n-tag size="small" type="info" style="margin-right: 12px;">{{ group.students.length }} 人</n-tag>
              </template>

              <n-data-table 
                :columns="columns" 
                :data="group.students" 
                :pagination="false" 
                :bordered="false" 
                size="small"
                striped
                :row-class-name="getRowClassName"
              />
            </n-collapse-item>
          </n-collapse>

          <n-empty v-if="groupedStudents.length === 0" description="暂无学生数据" />
        </div>
      </n-card>
    </main>

    <!-- 添加学生对话框 -->
    <n-modal v-model:show="showAddStudent" title="添加学生" preset="card" style="width: 500px;">
      <n-form :model="newStudent" label-placement="left" label-width="80px">
        <n-form-item label="学号" required>
          <n-input v-model:value="newStudent.student_id" placeholder="请输入学号" />
        </n-form-item>
        <n-form-item label="姓名" required>
          <n-input v-model:value="newStudent.name" placeholder="请输入姓名" />
        </n-form-item>
        <n-form-item label="班级">
          <n-select v-model:value="newStudent.class_name" placeholder="选择班级" :options="classOptions" clearable />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-button @click="showAddStudent = false">取消</n-button>
        <n-button type="primary" @click="handleAddStudent">确认添加</n-button>
      </template>
    </n-modal>

    <!-- 导入班级对话框 -->
    <n-modal v-model:show="showImport" title="导入班级" preset="card" style="width: 500px;">
      <n-upload :custom-request="handleUpload" accept=".xlsx,.xls" :max="1">
        <n-button>选择文件</n-button>
      </n-upload>
      <n-form style="margin-top: 16px;">
        <n-form-item label="默认班级">
          <n-select v-model:value="importClassName" placeholder="选择默认班级" :options="classOptions" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-button @click="showImport = false">取消</n-button>
        <n-button type="primary" @click="handleImport" :loading="importLoading">导入</n-button>
      </template>
    </n-modal>

    <!-- 调整分数对话框 -->
    <n-modal v-model:show="scoreDialogVisible" title="调整分数" preset="card" style="width: 450px;">
      <div class="student-info" style="margin-bottom: 16px; padding: 12px; background: rgba(99, 102, 241, 0.1); border-radius: 8px;">
        <span>学生：{{ selectedStudent.name }}</span>
        <span style="margin-left: 24px;">学号：{{ selectedStudent.student_id }}</span>
      </div>
      <n-form label-placement="left" label-width="80px">
        <n-form-item label="分数变更">
          <n-input-number v-model:value="scoreChange" :min="-100" :max="100" />
          <span class="tip" style="margin-left: 12px; color: var(--text-muted); font-size: 13px;">正数加分，负数扣分</span>
        </n-form-item>
        <n-form-item label="快捷标签">
          <n-space>
            <n-tag v-for="tag in scoreTags" :key="tag.label" :type="tag.score > 0 ? 'success' : 'error'" style="cursor: pointer;" @click="applyScoreTag(tag)">
              {{ tag.label }} {{ tag.score > 0 ? '+' : '' }}{{ tag.score }}分
            </n-tag>
          </n-space>
        </n-form-item>
        <n-form-item label="变更原因">
          <n-input v-model:value="scoreReason" type="textarea" :rows="3" placeholder="请输入分数变更原因" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-button @click="scoreDialogVisible = false">取消</n-button>
        <n-button type="primary" @click="handleUpdateScore">确认调整</n-button>
      </template>
    </n-modal>

    <!-- 修改密码对话框 -->
    <n-modal v-model:show="changePasswordVisible" title="修改密码" preset="card" style="width: 400px;">
      <n-form :model="passwordForm" label-placement="left" label-width="100px">
        <n-form-item label="原密码" required>
          <n-input v-model:value="passwordForm.old" type="password" show-password-on="mousedown" />
        </n-form-item>
        <n-form-item label="新密码" required>
          <n-input v-model:value="passwordForm.new" type="password" show-password-on="mousedown" />
        </n-form-item>
        <n-form-item label="确认新密码" required>
          <n-input v-model:value="passwordForm.confirm" type="password" show-password-on="mousedown" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-button @click="changePasswordVisible = false">取消</n-button>
        <n-button type="primary" @click="handleChangePassword">确认修改</n-button>
      </template>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, h } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import * as api from '@/api'
import { NIcon } from 'naive-ui'
import { CreateOutline } from '@vicons/ionicons5'

const router = useRouter()
const userStore = useUserStore()
const message = useMessage()
const dialog = useDialog()

const userName = ref(userStore.userName || '教师')

// 数据
const students = ref([])
const searchQuery = ref('')
const activeGroups = ref([])

// 控制显示
const showAddStudent = ref(false)
const showImport = ref(false)
const scoreDialogVisible = ref(false)
const changePasswordVisible = ref(false)

// 添加学生
const newStudent = ref({ student_id: '', name: '', class_name: '' })

// 导入
const importFile = ref(null)
const importClassName = ref('')
const importLoading = ref(false)

// 上课状态
const classSession = ref({ active: false })
const selectedClass = ref('')
const classStats = ref({ total: 0, checked_in: 0, not_checked_in: 0, rate: 0 })

// 根据签到率返回颜色
const getRateColor = (rate) => {
  if (rate >= 90) return '#10b981'
  if (rate >= 60) return '#f59e0b'
  return '#ef4444'
}

// 根据分数返回样式类
const getScoreClass = (score) => {
  if (score >= 90) return 'score-excellent'
  if (score >= 80) return 'score-good'
  if (score >= 60) return 'score-pass'
  return 'score-fail'
}

// 表格行样式
const getRowClassName = (row, index) => {
  return index % 2 === 0 ? 'row-even' : 'row-odd'
}

// 分数调整
const selectedStudent = ref({})
const scoreChange = ref(0)
const scoreReason = ref('')

const scoreTags = [
  { label: '回答问题', score: 2 },
  { label: '违反课堂纪律', score: -2 },
  { label: '旷课', score: -5 },
  { label: '未交作业', score: -2 }
]

// 修改密码
const passwordForm = ref({ old: '', new: '', confirm: '' })

// 用户下拉选项
const userOptions = [
  { label: '修改密码', key: 'changePassword' },
  { label: '退出登录', key: 'logout' }
]

// 模拟教师负责的班级（实际应该从后端获取）
const myClasses = ref(['2025中药制药1班', '2025中药制药2班'])

// 表格列定义（教师版：只有编辑，没有删除）
const columns = [
  { title: '学号', key: 'student_id', width: 120 },
  { title: '姓名', key: 'name', width: 100 },
  { 
    title: '分数', 
    key: 'score', 
    width: 100,
    render(row) {
      const scoreClass = getScoreClass(row.score)
      return h('span', { class: `score-badge ${scoreClass}` }, row.score)
    }
  },
  {
    title: '操作',
    key: 'actions',
    width: 80,
    render(row) {
      return h('div', { class: 'action-buttons' }, [
        h('button', { 
          class: 'icon-btn edit',
          title: '编辑分数',
          onClick: () => openScoreDialog(row)
        }, [
          h(NIcon, { size: 18, color: '#818cf8' }, { default: () => h(CreateOutline) })
        ])
      ])
    }
  }
]

// 计算属性：教师的学生（过滤）
const myStudents = computed(() => {
  return students.value.filter(s => myClasses.value.includes(s.class_name))
})

// 计算属性：班级选项（仅限教师的班级）
const classOptions = computed(() => {
  return myClasses.value.map(cls => ({ label: cls, value: cls }))
})

// 计算属性：按班级分组的学生
const groupedStudents = computed(() => {
  const groups = {}
  const query = searchQuery.value.toLowerCase()
  
  myStudents.value.forEach(student => {
    if (query && !student.student_id.toLowerCase().includes(query) && 
        !student.name.toLowerCase().includes(query)) {
      return
    }
    
    const className = student.class_name || '未分班'
    if (!groups[className]) {
      groups[className] = []
    }
    groups[className].push(student)
  })
  
  return Object.keys(groups).sort().map(className => ({
    className,
    students: groups[className]
  }))
})

// 计算属性：班级平均分
const classAverageScore = computed(() => {
  if (myStudents.value.length === 0) return 0
  const total = myStudents.value.reduce((sum, s) => sum + s.score, 0)
  return (total / myStudents.value.length).toFixed(1)
})

// 计算属性：今日签到率（模拟数据，实际应该从后端获取）
const todayCheckinRate = computed(() => {
  // 这里应该调用 API 获取今日签到数据
  return 85
})

const loadStudents = async () => {
  const res = await api.getStudents()
  if (res.success) {
    students.value = res.data
    activeGroups.value = []
  }
}

const handleAddStudent = async () => {
  if (!newStudent.value.student_id || !newStudent.value.name) {
    message.warning('请填写学号和姓名')
    return
  }
  
  const res = await api.addStudent(newStudent.value)
  if (res.success) {
    message.success('添加成功')
    newStudent.value = { student_id: '', name: '', class_name: '' }
    showAddStudent.value = false
    loadStudents()
  }
}

const handleUpload = ({ file }) => {
  importFile.value = file.file
}

const handleImport = async () => {
  if (!importFile.value) {
    message.warning('请选择文件')
    return
  }
  
  importLoading.value = true
  const formData = new FormData()
  formData.append('file', importFile.value)
  formData.append('class_name', importClassName.value)
  
  const res = await api.importStudents(formData)
  importLoading.value = false
  
  if (res.success) {
    message.success(res.message)
    showImport.value = false
    loadStudents()
  }
}

const openScoreDialog = (student) => {
  selectedStudent.value = student
  scoreChange.value = 0
  scoreReason.value = ''
  scoreDialogVisible.value = true
}

const applyScoreTag = (tag) => {
  scoreChange.value = tag.score
  if (!scoreReason.value) {
    scoreReason.value = tag.label
  }
}

const handleUpdateScore = async () => {
  if (scoreChange.value === 0) {
    message.warning('分数变更不能为0')
    return
  }
  
  const res = await api.updateScore(selectedStudent.value.student_id, {
    change: scoreChange.value,
    reason: scoreReason.value
  })
  
  if (res.success) {
    message.success('分数调整成功')
    scoreDialogVisible.value = false
    loadStudents()
  }
}

const startClass = async () => {
  const res = await api.setClassSession({ class_name: selectedClass.value })
  if (res.success) {
    message.success('上课开始')
    classSession.value = { active: true, class_name: selectedClass.value }
    refreshClassStatus()
  }
}

const endClass = async () => {
  const res = await api.setClassSession({ class_name: '' })
  if (res.success) {
    message.success('上课结束')
    classSession.value = { active: false }
  }
}

const refreshClassStatus = async () => {
  const res = await api.getClassSession()
  if (res.success && res.data.active) {
    const studentsRes = await api.getClassSessionStudents()
    if (studentsRes.success) {
      const total = studentsRes.data.length
      const checkedIn = studentsRes.data.filter(s => s.checked_in).length
      classStats.value = {
        total,
        checked_in: checkedIn,
        not_checked_in: total - checkedIn,
        rate: total > 0 ? Math.round((checkedIn / total) * 100) : 0
      }
    }
  }
}

const expandAll = () => {
  activeGroups.value = groupedStudents.value.map(g => g.className)
}

const collapseAll = () => {
  activeGroups.value = []
}

const handleChangePassword = async () => {
  if (!passwordForm.value.old || !passwordForm.value.new || !passwordForm.value.confirm) {
    message.warning('请填写完整信息')
    return
  }
  
  if (passwordForm.value.new !== passwordForm.value.confirm) {
    message.warning('两次输入的新密码不一致')
    return
  }
  
  const res = await api.changePassword({
    old_password: passwordForm.value.old,
    new_password: passwordForm.value.new
  })
  
  if (res.success) {
    message.success('密码修改成功')
    changePasswordVisible.value = false
    passwordForm.value = { old: '', new: '', confirm: '' }
  }
}

const handleUserAction = async (key) => {
  if (key === 'changePassword') {
    passwordForm.value = { old: '', new: '', confirm: '' }
    changePasswordVisible.value = true
  } else if (key === 'logout') {
    await api.logout()
    userStore.clearUser()
    router.push('/login')
  }
}

onMounted(() => {
  loadStudents()
  refreshClassStatus()
})
</script>

<style scoped>
/* 复用 Admin.vue 的样式 */
.admin-layout {
  min-height: 100vh;
  background: #0a0a0f;
}

.admin-header {
  height: 64px;
  background: rgba(19, 19, 31, 0.8);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 32px;
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-icon {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-icon svg {
  width: 20px;
  height: 20px;
  color: white;
}

.logo h1 {
  font-size: 20px;
  font-weight: 700;
  color: white;
  margin: 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.checkin-btn {
  background: linear-gradient(135deg, #6366f1, #4f46e5) !important;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.user-info:hover {
  background: rgba(255, 255, 255, 0.1);
}

.user-avatar {
  width: 28px;
  height: 28px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 12px;
  font-weight: 600;
}

.username {
  color: #e2e8f0;
  font-size: 14px;
}

.admin-main {
  padding: 32px;
  max-width: 1400px;
  margin: 0 auto;
}

.control-card {
  margin-bottom: 24px;
  background: rgba(255, 255, 255, 0.03) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
}

.control-card.active {
  background: rgba(99, 102, 241, 0.1) !important;
  border-color: rgba(99, 102, 241, 0.3) !important;
}

/* 统计卡片 */
.stats-card {
  margin-bottom: 24px;
  background: rgba(255, 255, 255, 0.03) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
}

.teacher-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
  padding: 16px 0;
}

.teacher-stats .stat-item {
  text-align: center;
  padding: 20px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.teacher-stats .stat-value {
  font-size: 32px;
  font-weight: 700;
  color: white;
  margin-bottom: 4px;
}

.teacher-stats .stat-label {
  font-size: 14px;
  color: #94a3b8;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  font-weight: 600;
  color: white;
}

.class-selector {
  display: flex;
  align-items: center;
  gap: 16px;
}

.class-info {
  text-align: center;
}

.stats-row-enhanced {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 32px;
  gap: 32px;
  flex-wrap: wrap;
}

.stat-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 24px 32px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  min-width: 120px;
  position: relative;
}

.stat-box.success {
  background: rgba(16, 185, 129, 0.08);
  border-color: rgba(16, 185, 129, 0.25);
}

.stat-box.danger {
  background: rgba(239, 68, 68, 0.08);
  border-color: rgba(239, 68, 68, 0.25);
}

.stat-number {
  font-size: 40px;
  font-weight: 800;
  color: white;
  line-height: 1.2;
  margin-bottom: 8px;
}

.stat-box.success .stat-number {
  color: #34d399;
}

.stat-box.danger .stat-number {
  color: #f87171;
}

.stat-label {
  font-size: 14px;
  color: #94a3b8;
  font-weight: 500;
}

.stat-indicator {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.success-dot {
  background: #10b981;
  box-shadow: 0 0 8px #10b981;
}

.danger-dot {
  background: #ef4444;
  box-shadow: 0 0 8px #ef4444;
}

.rate-box {
  padding: 16px 24px;
}

.rate-text {
  font-size: 24px;
  font-weight: 700;
  color: white;
}

.class-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
}

.quick-actions {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
  margin-bottom: 32px;
}

.action-card {
  text-align: center;
  padding: 32px 24px;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.03) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  transition: all 0.3s ease;
}

.action-card:hover {
  transform: translateY(-4px);
  background: rgba(255, 255, 255, 0.06) !important;
  border-color: rgba(99, 102, 241, 0.3) !important;
}

.action-icon {
  width: 64px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 16px;
  margin: 0 auto 16px;
}

.action-icon svg {
  width: 28px;
  height: 28px;
  color: white;
}

.action-title {
  font-size: 16px;
  font-weight: 600;
  color: white;
  margin-bottom: 6px;
}

.action-desc {
  font-size: 13px;
  color: #94a3b8;
}

.student-list-card {
  background: rgba(255, 255, 255, 0.03) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 12px;
  color: white;
  font-size: 16px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.class-groups {
  margin-top: 16px;
}

.student-info {
  color: white;
}

.tip {
  color: #64748b;
  font-size: 13px;
}

/* 分数徽章样式 */
:deep(.score-badge) {
  display: inline-block;
  padding: 4px 12px;
  background: rgba(99, 102, 241, 0.15);
  border-radius: 20px;
  color: #818cf8;
  font-weight: 600;
  font-size: 13px;
  min-width: 44px;
  text-align: center;
}

:deep(.score-badge.score-excellent) {
  background: rgba(16, 185, 129, 0.15) !important;
  color: #34d399 !important;
}

:deep(.score-badge.score-good) {
  background: rgba(99, 102, 241, 0.15) !important;
  color: #818cf8 !important;
}

:deep(.score-badge.score-pass) {
  background: rgba(245, 158, 11, 0.15) !important;
  color: #fbbf24 !important;
}

:deep(.score-badge.score-fail) {
  background: rgba(239, 68, 68, 0.15) !important;
  color: #f87171 !important;
}

/* 表格斑马纹和悬停效果 */
:deep(.n-data-table .n-data-table-tbody .n-data-table-tr.row-even) {
  background: transparent;
}

:deep(.n-data-table .n-data-table-tbody .n-data-table-tr.row-odd) {
  background: rgba(255, 255, 255, 0.02);
}

:deep(.n-data-table .n-data-table-tbody .n-data-table-tr:hover) {
  background: rgba(99, 102, 241, 0.08) !important;
  transition: background 0.2s ease;
}

/* 图标按钮样式 */
.action-buttons {
  display: flex;
  gap: 24px;
  align-items: center;
  justify-content: center;
  padding: 0 12px;
}

.icon-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.25s ease;
  background: rgba(255, 255, 255, 0.05);
  color: #e2e8f0;
}

.icon-btn.edit {
  color: #818cf8;
  background: rgba(99, 102, 241, 0.1);
}

.icon-btn.edit:hover {
  background: rgba(99, 102, 241, 0.25);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.2);
}

.icon-btn:active {
  transform: scale(0.95);
}

/* 响应式 */
@media (max-width: 1200px) {
  .teacher-stats {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .admin-header {
    padding: 0 16px;
  }
  
  .admin-main {
    padding: 16px;
  }
  
  .teacher-stats {
    grid-template-columns: 1fr;
  }
  
  .quick-actions {
    grid-template-columns: 1fr;
  }
  
  .stats-row-enhanced {
    gap: 16px;
  }
  
  .stat-box {
    padding: 16px 24px;
    min-width: 100px;
  }
  
  .stat-number {
    font-size: 28px;
  }
}
</style>