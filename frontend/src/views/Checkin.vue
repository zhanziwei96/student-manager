<template>
  <div class="checkin-page">
    <!-- 顶部导航 -->
    <div class="checkin-header">
      <div class="logo" @click="$router.push('/')">
        <el-icon size="24"><School /></el-icon>
        <span>班级管理系统</span>
      </div>
      <div class="header-actions">
        <el-button v-if="isTeacher" type="primary" @click="$router.push('/admin')">
          <el-icon><Management /></el-icon>
          管理后台
        </el-button>
      </div>
    </div>
    
    <div class="checkin-container">
      <!-- 老师面板 -->
      <el-card v-if="isTeacher" class="teacher-panel">
        <div class="teacher-info">
          <el-avatar :size="40" :icon="UserFilled" />
          <div class="teacher-detail">
            <div class="teacher-name">{{ teacherName }}</div>
            <div class="teacher-role">教师</div>
          </div>
        </div>
        <el-divider />
        <el-button type="primary" size="large" @click="showTeacherCheckin = true" style="width: 100%">
          <el-icon><EditPen /></el-icon>
          帮学生代签到
        </el-button>
      </el-card>
      
      <!-- 班级状态 -->
      <template v-if="classSession.active">
        <el-card class="class-status">
          <div class="status-header">
            <div class="status-title">
              <el-icon size="20" color="#52c41a"><CircleCheckFilled /></el-icon>
              <span>当前上课：{{ classSession.class_name }}</span>
            </div>
            <el-button type="primary" text @click="refreshStatus" :loading="refreshing">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
          
          <div class="stats-bar">
            <div class="stat-item">
              <div class="stat-label">应到</div>
              <div class="stat-value">{{ classStats.total }}人</div>
            </div>
            <el-divider direction="vertical" />
            <div class="stat-item success">
              <div class="stat-label">已签</div>
              <div class="stat-value">{{ classStats.checked_in }}人</div>
            </div>
            <el-divider direction="vertical" />
            <div class="stat-item warning">
              <div class="stat-label">未签</div>
              <div class="stat-value">{{ classStats.not_checked_in }}人</div>
            </div>
            <el-divider direction="vertical" />
            <div class="stat-item primary">
              <div class="stat-label">签到率</div>
              <div class="stat-value">{{ classStats.rate }}%</div>
            </div>
          </div>
          
          <!-- 学生状态列表 -->
          <div class="student-list">
            <div 
              v-for="student in classStudents" 
              :key="student.student_id"
              class="student-item"
              :class="{ 'checked': student.checked_in }"
            >
              <el-icon v-if="student.checked_in" size="16" color="#52c41a"><CircleCheckFilled /></el-icon>
              <el-icon v-else size="16" color="#909399"><CircleCheck /></el-icon>
              <span class="student-name">{{ student.name }}</span>
              <span v-if="student.checked_in" class="checkin-time">
                {{ formatTime(student.checkin_time) }}
              </span>
            </div>
          </div>
        </el-card>
      </template>
      
      <!-- 未上课提示 -->
      <el-card v-else class="no-class">
        <el-empty description="暂无课程">
          <template #image>
            <el-icon size="64" color="#dcdfe6"><Calendar /></el-icon>
          </template>
          <template #description>
            <div style="text-align: center; color: #666;">
              <div style="font-size: 16px; margin-bottom: 8px;">请等待老师开始上课</div>
              <div style="font-size: 13px; color: #999;">上课后即可进行签到</div>
            </div>
          </template>
          <el-button type="primary" @click="refreshStatus" :loading="refreshing">
            <el-icon><Refresh /></el-icon>
            刷新状态
          </el-button>
        </el-empty>
      </el-card>
      
      <!-- 签到表单 -->
      <el-card v-if="!hasCheckedIn" class="checkin-form">
        <template #header>
          <div class="form-header">
            <el-icon size="20" color="#667eea"><EditPen /></el-icon>
            <span>学生签到</span>
          </div>
        </template>
        
        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          label-position="top"
          size="large"
        >
          <el-form-item label="学号" prop="student_id">
            <el-input
              v-model="form.student_id"
              placeholder="请输入学号"
              clearable
              :prefix-icon="User"
            />
          </el-form-item>
          
          <el-form-item label="姓名" prop="name">
            <el-input
              v-model="form.name"
              placeholder="请输入姓名"
              clearable
              :prefix-icon="UserFilled"
              @keyup.enter="handleCheckin"
            />
          </el-form-item>
          
          <el-form-item>
            <el-button
              type="primary"
              size="large"
              :loading="loading"
              @click="handleCheckin"
              style="width: 100%; height: 48px;"
            >
              <template v-if="loading">
                <el-icon class="is-loading"><Loading /></el-icon>
                签到中...
              </template>
              <template v-else>
                立即签到
              </template>
            </el-button>
          </el-form-item>
        </el-form>
        

      </el-card>
      
      <!-- 已签到提示 -->
      <el-card v-else class="checked-in">
        <el-result
          icon="success"
          title="签到成功"
          :sub-title="`欢迎 ${checkedInInfo.name}，今日已完成签到`"
        >
          <template #icon>
            <div class="success-icon">
              <el-icon size="80" color="#52c41a"><CircleCheckFilled /></el-icon>
            </div>
          </template>
          <template #extra>
            <div class="checkin-detail">
              <div class="detail-item">
                <span class="label">签到时间</span>
                <span class="value">{{ formatFullTime(checkedInInfo.time) }}</span>
              </div>
            </div>
            <el-button @click="resetCheckin" text type="primary">
              <el-icon><RefreshLeft /></el-icon>
              重新签到（需密码）
            </el-button>
          </template>
        </el-result>
      </el-card>
      
      <!-- 最近签到 -->
      <el-card class="recent-records">
        <template #header>
          <div class="records-header">
            <span>最近签到</span>
            <el-button text type="primary" @click="loadRecords">
              <el-icon><Refresh /></el-icon>
            </el-button>
          </div>
        </template>
        
        <div v-if="recentRecords.length > 0" class="records-list">
          <div 
            v-for="record in recentRecords" 
            :key="record.record_id"
            class="record-item"
          >
            <div class="record-info">
              <span class="record-name">{{ record.student_name || record.student_id }}</span>
              <el-tag size="small" :type="record.checkin_type === '网页签到' ? 'success' : 'warning'">
                {{ record.checkin_type }}
              </el-tag>
            </div>
            <span class="record-time">{{ formatTime(record.checkin_time) }}</span>
          </div>
        </div>
        <el-empty v-else description="暂无签到记录" />
      </el-card>
    </div>
    
    <!-- 老师代签到对话框 -->
    <el-dialog v-model="showTeacherCheckin" title="帮学生代签到" width="400px">
      <el-form>
        <el-form-item label="学生姓名">
          <el-input v-model="teacherCheckinName" placeholder="输入学生姓名" />
        </el-form-item>
      </el-form>
      <div v-if="multipleStudents.length > 0" class="student-select">
        <p>找到多个同名学生，请选择：</p>
        <el-radio-group v-model="selectedStudentId">
          <el-radio 
            v-for="s in multipleStudents" 
            :key="s.student_id"
            :label="s.student_id"
          >
            {{ s.name }} ({{ s.class_name || '未分班' }}) - {{ s.student_id }}
          </el-radio>
        </el-radio-group>
      </div>
      <template #footer>
        <el-button @click="showTeacherCheckin = false">取消</el-button>
        <el-button type="primary" @click="handleTeacherCheckin">确认代签</el-button>
      </template>
    </el-dialog>
    
    <!-- 重置签到密码对话框 -->
    <el-dialog v-model="showResetDialog" title="重新签到" width="400px">
      <p style="margin-bottom: 16px; color: #666;">请输入管理员密码以重置签到状态</p>
      <el-input v-model="resetPassword" type="password" placeholder="管理员密码" show-password />
      <template #footer>
        <el-button @click="showResetDialog = false">取消</el-button>
        <el-button type="primary" @click="handleReset">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  School, Management, UserFilled, EditPen, CircleCheckFilled,
  CircleCheck, Refresh, Calendar, User, Loading,
  InfoFilled, RefreshLeft
} from '@element-plus/icons-vue'
import Cookies from 'js-cookie'
import * as api from '../api'
import '../styles/cyber-theme.css'

const router = useRouter()

const formRef = ref()
const loading = ref(false)
const refreshing = ref(false)
const hasCheckedIn = ref(false)
const checkedInInfo = ref({ name: '', time: '' })

// 老师相关
const isTeacher = ref(false)
const teacherName = ref('')
const showTeacherCheckin = ref(false)
const teacherCheckinName = ref('')
const multipleStudents = ref([])
const selectedStudentId = ref('')

// 班级状态
const classSession = ref({ active: false })
const classStudents = ref([])
const classStats = ref({ total: 0, checked_in: 0, not_checked_in: 0, rate: 0 })

// 最近记录
const recentRecords = ref([])

// 重置对话框
const showResetDialog = ref(false)
const resetPassword = ref('')

const form = reactive({
  student_id: '',
  name: ''
})

const rules = {
  student_id: [{ required: true, message: '请输入学号', trigger: 'blur' }],
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }]
}

// 检查登录状态
const checkLogin = async () => {
  const userId = Cookies.get('user_id')
  if (userId) {
    const res = await api.getUserInfo()
    if (res.success) {
      isTeacher.value = true
      teacherName.value = res.user.name
    }
  }
}

// 签到
const handleCheckin = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  
  loading.value = true
  
  const res = await api.checkin({
    student_id: form.student_id,
    name: form.name
  })
  
  loading.value = false
  
  if (res.success) {
    ElMessage.success(`签到成功！欢迎 ${res.student_name}`)
    hasCheckedIn.value = true
    checkedInInfo.value = {
      name: res.student_name,
      time: new Date().toISOString()
    }
    // 保存匿名签到标志（防止重复签到，不存储学生敏感信息）
    saveCheckinStatus()
    loadRecords()
    loadClassSession()
  } else {
    ElMessage.error(res.message)
  }
}

// 老师代签到
const handleTeacherCheckin = async () => {
  if (!teacherCheckinName.value) {
    ElMessage.warning('请输入学生姓名')
    return
  }
  
  // 如果选择了具体学生
  if (selectedStudentId.value) {
    const res = await api.teacherCheckin({ student_id: selectedStudentId.value })
    if (res.success) {
      ElMessage.success(`代签到成功：${res.student_name}`)
      closeTeacherCheckin()
      loadRecords()
      loadClassSession()
    } else {
      ElMessage.error(res.message)
    }
    return
  }
  
  // 先按姓名查找
  const res = await api.teacherCheckin({ student_name: teacherCheckinName.value })
  
  if (res.success) {
    ElMessage.success(`代签到成功：${res.student_name}`)
    closeTeacherCheckin()
    loadRecords()
    loadClassSession()
  } else if (res.multiple_students) {
    multipleStudents.value = res.students
  } else {
    ElMessage.error(res.message)
  }
}

const closeTeacherCheckin = () => {
  showTeacherCheckin.value = false
  teacherCheckinName.value = ''
  multipleStudents.value = []
  selectedStudentId.value = ''
}

// 重置签到
const resetCheckin = () => {
  showResetDialog.value = true
  resetPassword.value = ''
}

const handleReset = async () => {
  const res = await api.login({ username: 'admin', password: resetPassword.value })
  if (res.success) {
    hasCheckedIn.value = false
    checkedInInfo.value = { name: '', time: '' }
    // 清除签到标志
    clearCheckinStatus()
    ElMessage.success('重置成功')
    showResetDialog.value = false
    await api.logout()
  } else {
    ElMessage.error('密码错误')
  }
}

// 加载班级状态
const loadClassSession = async () => {
  try {
    const res = await api.getClassSession()
    if (res.success && res.data.active) {
      classSession.value = res.data
      const studentsRes = await api.getClassSessionStudents()
      if (studentsRes.success) {
        classStudents.value = studentsRes.data.students
        const { total, checked_in, not_checked_in } = studentsRes.data
        classStats.value = {
          total,
          checked_in,
          not_checked_in,
          rate: total > 0 ? Math.round((checked_in / total) * 100) : 0
        }
      }
    } else {
      classSession.value = { active: false }
      classStudents.value = []
      classStats.value = { total: 0, checked_in: 0, not_checked_in: 0, rate: 0 }
    }
  } catch (error) {
    classSession.value = { active: false }
  }
}

// 加载签到记录
const loadRecords = async () => {
  const today = new Date().toISOString().split('T')[0]
  const res = await api.getCheckinRecords({ date: today })
  if (res.success) {
    recentRecords.value = res.data.slice(0, 10)
  }
}

// 手动刷新
const refreshStatus = async () => {
  refreshing.value = true
  await loadClassSession()
  await loadRecords()
  refreshing.value = false
}

const formatTime = (time) => {
  if (!time) return ''
  // 把后端返回的 UTC 时间转换为本地时间
  const utcTime = time.endsWith('Z') ? time : time + 'Z'
  return new Date(utcTime).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

const formatFullTime = (time) => {
  if (!time) return ''
  // 把后端返回的 UTC 时间转换为本地时间
  const utcTime = time.endsWith('Z') ? time : time + 'Z'
  return new Date(utcTime).toLocaleString('zh-CN')
}

onMounted(() => {
  checkLogin()
  loadClassSession()
  loadRecords()
  checkLocalStorage()
})

// 检查 localStorage 中的签到状态
const CHECKIN_STATUS_KEY = 'has_checked_in_today'

const checkLocalStorage = () => {
  const savedDate = localStorage.getItem(CHECKIN_STATUS_KEY)
  if (savedDate) {
    const today = new Date().toDateString()
    if (today === savedDate) {
      // 今天已签到（匿名标志，不显示具体学生信息）
      hasCheckedIn.value = true
      checkedInInfo.value = {
        name: '已签到',
        time: new Date().toISOString()
      }
    } else {
      // 不是今天的签到，清除状态
      localStorage.removeItem(CHECKIN_STATUS_KEY)
    }
  }
}

// 保存签到状态到 localStorage
// 保存匿名签到标志（只存日期，不存学生敏感信息）
const saveCheckinStatus = () => {
  const today = new Date().toDateString()
  localStorage.setItem(CHECKIN_STATUS_KEY, today)
}

// 清除签到标志
const clearCheckinStatus = () => {
  localStorage.removeItem(CHECKIN_STATUS_KEY)
}
</script>

<style scoped>
.checkin-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e7ed 100%);
}

.checkin-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: white;
  box-shadow: 0 2px 12px rgba(0,0,0,0.05);
  position: sticky;
  top: 0;
  z-index: 100;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
  color: #667eea;
  cursor: pointer;
}

.checkin-container {
  max-width: 600px;
  margin: 0 auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.teacher-panel {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.teacher-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.teacher-detail {
  flex: 1;
}

.teacher-name {
  font-size: 16px;
  font-weight: 600;
}

.teacher-role {
  font-size: 13px;
  opacity: 0.8;
}

:deep(.teacher-panel .el-divider) {
  border-color: rgba(255,255,255,0.2);
  margin: 16px 0;
}

.class-status {
  border-radius: 12px;
  overflow: hidden;
}

.status-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.status-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
}

.stats-bar {
  display: flex;
  justify-content: space-around;
  align-items: center;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
  margin-bottom: 16px;
}

.stat-item {
  text-align: center;
}

.stat-item.success .stat-value {
  color: #52c41a;
}

.stat-item.warning .stat-value {
  color: #faad14;
}

.stat-item.primary .stat-value {
  color: #1890ff;
}

.stat-label {
  font-size: 12px;
  color: #999;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 20px;
  font-weight: 600;
}

.student-list {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.student-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: #f5f7fa;
  border-radius: 6px;
  font-size: 13px;
}

.student-item.checked {
  background: #f6ffed;
}

.student-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.checkin-time {
  font-size: 11px;
  color: #999;
}

.no-class {
  padding: 40px 20px;
}

.checkin-form {
  border-radius: 12px;
}

.form-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
}

.form-tips {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  margin-top: 16px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
  color: #666;
  font-size: 13px;
}

.checked-in {
  border-radius: 12px;
}

.success-icon {
  animation: scaleIn 0.5s ease;
}

@keyframes scaleIn {
  from {
    transform: scale(0);
    opacity: 0;
  }
  to {
    transform: scale(1);
    opacity: 1;
  }
}

.checkin-detail {
  margin-bottom: 20px;
}

.detail-item {
  display: flex;
  justify-content: center;
  gap: 12px;
}

.detail-item .label {
  color: #999;
}

.detail-item .value {
  color: #333;
  font-weight: 500;
}

.recent-records {
  border-radius: 12px;
}

.records-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.records-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.record-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  background: #f5f7fa;
  border-radius: 6px;
}

.record-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.record-name {
  font-weight: 500;
}

.record-time {
  font-size: 12px;
  color: #999;
}

.student-select {
  margin-top: 16px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.student-select p {
  margin-bottom: 12px;
  color: #666;
}

:deep(.el-radio-group) {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

@media (max-width: 640px) {
  .checkin-container {
    padding: 16px;
  }
  
  .student-list {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .stats-bar {
    flex-wrap: wrap;
    gap: 16px;
  }
}

/* 输入框样式优化 - 深色背景下的可读性 */
:deep(.el-input__wrapper) {
  background-color: rgba(255, 255, 255, 0.1) !important;
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.2) inset !important;
}

:deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.4) inset !important;
}

:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #667eea inset !important;
}

:deep(.el-input__inner) {
  color: white !important;
  font-weight: 500;
}

:deep(.el-input__inner::placeholder) {
  color: rgba(255, 255, 255, 0.5) !important;
}

:deep(.el-input__prefix-inner) {
  color: rgba(255, 255, 255, 0.6) !important;
}
</style>
