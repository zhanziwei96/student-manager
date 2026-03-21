<template>
  <div class="student-layout">
    <!-- 顶部导航 -->
    <header class="student-header">
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
        <n-tag type="info" size="small" round>学生中心</n-tag>
      </div>
      <div class="header-right">
        <n-dropdown :options="userOptions" @select="handleUserAction">
          <div class="user-info">
            <div class="user-avatar">{{ studentInfo.name ? studentInfo.name.charAt(0) : '学' }}</div>
            <span class="username">{{ studentInfo.name || '学生' }}</span>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 14px; height: 14px;">
              <polyline points="6 9 12 15 18 9"/>
            </svg>
          </div>
        </n-dropdown>
      </div>
    </header>

    <!-- 主内容 -->
    <main class="student-main">
      <!-- 个人信息卡片 -->
      <n-card class="info-card">
        <template #header>
          <div class="card-header">
            <span>我的信息</span>
            <n-tag v-if="classSession.active" type="success" size="small">上课中</n-tag>
          </div>
        </template>
        
        <div class="info-grid">
          <div class="info-item">
            <div class="info-label">学号</div>
            <div class="info-value">{{ studentInfo.student_id }}</div>
          </div>
          <div class="info-item">
            <div class="info-label">姓名</div>
            <div class="info-value">{{ studentInfo.name }}</div>
          </div>
          <div class="info-item">
            <div class="info-label">班级</div>
            <div class="info-value">{{ studentInfo.class_name || '未分班' }}</div>
          </div>
          <div class="info-item highlight">
            <div class="info-label">当前分数</div>
            <div class="info-value score">{{ studentInfo.score }}</div>
          </div>
          <div class="info-item">
            <div class="info-label">班级排名</div>
            <div class="info-value">{{ classRank }} / {{ classTotal }}</div>
          </div>
          <div class="info-item">
            <div class="info-label">签到状态</div>
            <div class="info-value">
              <n-tag v-if="todayCheckin" type="success" size="small">已签到</n-tag>
              <n-tag v-else type="warning" size="small">未签到</n-tag>
            </div>
          </div>
        </div>
      </n-card>

      <!-- 快捷签到 -->
      <n-card v-if="classSession.active && !todayCheckin" class="checkin-card" hoverable @click="handleCheckin">
        <div class="checkin-content">
          <div class="checkin-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 11l3 3L22 4"/>
              <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
            </svg>
          </div>
          <div class="checkin-text">
            <div class="checkin-title">立即签到</div>
            <div class="checkin-desc">当前课程：{{ classSession.class_name }}</div>
          </div>
        </div>
      </n-card>

      <!-- 分数历史 -->
      <n-card class="history-card">
        <template #header>
          <div class="card-header">
            <span>分数变化历史</span>
          </div>
        </template>
        
        <n-timeline v-if="scoreLogs.length > 0">
          <n-timeline-item
            v-for="log in scoreLogs"
            :key="log.id"
            :type="log.delta > 0 ? 'success' : 'error'"
          >
            <div class="log-item">
              <div class="log-header">
                <span class="log-reason">{{ log.reason || '分数调整' }}</span>
                <span :class="['log-delta', log.delta > 0 ? 'positive' : 'negative']">
                  {{ log.delta > 0 ? '+' : '' }}{{ log.delta }}
                </span>
              </div>
              <div class="log-detail">
                <span>{{ log.old_score }} → {{ log.new_score }}</span>
                <span class="log-time">{{ formatTime(log.created_at) }}</span>
              </div>
            </div>
          </n-timeline-item>
        </n-timeline>
        
        <n-empty v-else description="暂无分数变动记录" />
      </n-card>

      <!-- 签到记录 -->
      <n-card class="checkin-history-card">
        <template #header>
          <div class="card-header">
            <span>签到记录</span>
          </div>
        </template>
        
        <n-list v-if="checkinRecords.length > 0">
          <n-list-item v-for="record in checkinRecords" :key="record.id">
            <div class="record-item">
              <div class="record-info">
                <div class="record-class">{{ record.class_name }}</div>
                <div class="record-time">{{ formatTime(record.checkin_time) }}</div>
              </div>
              <n-tag type="success" size="small">已签到</n-tag>
            </div>
          </n-list-item>
        </n-list>
        
        <n-empty v-else description="暂无签到记录" />
      </n-card>
    </main>

    <!-- 修改密码对话框 -->
    <n-modal v-model:show="changePasswordVisible" title="修改密码" preset="card" style="width: 400px;">
      <n-form :model="passwordForm" label-placement="left" label-width="100px">
        <n-form-item label="原密码" required>
          <n-input v-model:value="passwordForm.old" type="password" show-password-on="mousedown" />
        </n-form-item>
        <n-form-item label="新密码" required>
          <n-input v-model:value="passwordForm.new" type="password" show-password-on="mousedown" />
        </n-form-item>
        <n-form-item label="确认密码" required>
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
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import * as api from '@/api'

const router = useRouter()
const userStore = useUserStore()
const message = useMessage()

// 学生信息
const studentInfo = ref({
  student_id: '',
  name: '',
  class_name: '',
  score: 0
})

// 班级排名
const classRank = ref(0)
const classTotal = ref(0)

// 上课状态
const classSession = ref({ active: false, class_name: '' })
const todayCheckin = ref(false)

// 分数历史
const scoreLogs = ref([])

// 签到记录
const checkinRecords = ref([])

// 修改密码
const changePasswordVisible = ref(false)
const passwordForm = ref({ old: '', new: '', confirm: '' })

// 用户选项
const userOptions = [
  { label: '修改密码', key: 'changePassword' },
  { label: '退出登录', key: 'logout' }
]

// 加载学生信息
const loadStudentInfo = async () => {
  // 从Cookie获取学号（学生登录时应该存储）
  // 这里使用模拟数据，实际应该从后端获取
  const username = userStore.username || '2513070101'
  
  // 调用API获取学生详情
  const res = await api.getStudents()
  if (res.success) {
    const student = res.data.find(s => s.student_id === username)
    if (student) {
      studentInfo.value = student
      await loadScoreLogs(student.student_id)
      await loadCheckinRecords(student.student_id)
      await loadClassRank(student.class_name)
    }
  }
}

// 加载分数历史
const loadScoreLogs = async (studentId) => {
  const res = await api.getScoreLogs({ student_id: studentId })
  if (res.success) {
    scoreLogs.value = res.data || []
  }
}

// 加载签到记录
const loadCheckinRecords = async (studentId) => {
  const res = await api.getCheckinRecords({ student_id: studentId })
  if (res.success) {
    checkinRecords.value = res.data || []
    // 检查今天是否已签到
    const today = new Date().toDateString()
    todayCheckin.value = checkinRecords.value.some(r => 
      new Date(r.checkin_time).toDateString() === today
    )
  }
}

// 加载班级排名
const loadClassRank = async (className) => {
  if (!className) return
  const res = await api.getStudents()
  if (res.success) {
    const classStudents = res.data.filter(s => s.class_name === className)
    classStudents.sort((a, b) => b.score - a.score)
    classTotal.value = classStudents.length
    const rank = classStudents.findIndex(s => s.student_id === studentInfo.value.student_id)
    classRank.value = rank + 1
  }
}

// 加载上课状态
const loadClassSession = async () => {
  const res = await api.getClassSession()
  if (res.success) {
    classSession.value = res.data
  }
}

// 签到
const handleCheckin = async () => {
  try {
    const res = await api.checkin({
      student_id: studentInfo.value.student_id,
      class_name: classSession.value.class_name
    })
    if (res.success) {
      message.success('签到成功！')
      todayCheckin.value = true
      await loadCheckinRecords(studentInfo.value.student_id)
    }
  } catch (error) {
    message.error(error?.response?.data?.message || '签到失败')
  }
}

// 修改密码
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

// 用户操作
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

// 格式化时间
const formatTime = (timeStr) => {
  if (!timeStr) return ''
  const date = new Date(timeStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(() => {
  loadStudentInfo()
  loadClassSession()
})
</script>

<style scoped>
.student-layout {
  min-height: 100vh;
  background: #0a0a0f;
}

.student-header {
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

.student-main {
  padding: 32px;
  max-width: 1000px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.info-card,
.checkin-card,
.history-card,
.checkin-history-card {
  background: rgba(255, 255, 255, 0.03) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  color: white;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
}

.info-item {
  text-align: center;
  padding: 20px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.info-item.highlight {
  background: rgba(99, 102, 241, 0.1);
  border-color: rgba(99, 102, 241, 0.3);
}

.info-label {
  font-size: 13px;
  color: #94a3b8;
  margin-bottom: 8px;
}

.info-value {
  font-size: 18px;
  font-weight: 600;
  color: white;
}

.info-value.score {
  font-size: 32px;
  color: #818cf8;
}

.checkin-card {
  cursor: pointer;
  transition: all 0.3s ease;
}

.checkin-card:hover {
  transform: translateY(-4px);
  background: rgba(16, 185, 129, 0.1) !important;
  border-color: rgba(16, 185, 129, 0.3) !important;
}

.checkin-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 24px;
  padding: 32px;
}

.checkin-icon {
  width: 64px;
  height: 64px;
  background: linear-gradient(135deg, #10b981, #34d399);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.checkin-icon svg {
  width: 32px;
  height: 32px;
  color: white;
}

.checkin-title {
  font-size: 24px;
  font-weight: 700;
  color: white;
  margin-bottom: 8px;
}

.checkin-desc {
  font-size: 14px;
  color: #94a3b8;
}

.log-item {
  padding: 12px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 8px;
  margin-bottom: 8px;
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.log-reason {
  font-weight: 600;
  color: white;
}

.log-delta {
  font-weight: 700;
  font-size: 18px;
}

.log-delta.positive {
  color: #34d399;
}

.log-delta.negative {
  color: #f87171;
}

.log-detail {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: #94a3b8;
}

.log-time {
  color: #64748b;
}

.record-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
}

.record-class {
  font-weight: 600;
  color: white;
  margin-bottom: 4px;
}

.record-time {
  font-size: 13px;
  color: #94a3b8;
}

@media (max-width: 768px) {
  .student-header {
    padding: 0 16px;
  }
  
  .student-main {
    padding: 16px;
  }
  
  .info-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
  }
  
  .info-item {
    padding: 16px;
  }
  
  .checkin-content {
    flex-direction: column;
    text-align: center;
    padding: 24px;
  }
}
</style>