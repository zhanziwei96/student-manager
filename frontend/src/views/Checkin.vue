<template>
  <div class="checkin-page">
    <!-- 背景装饰 -->
    <div class="bg-decoration">
      <div class="gradient-orb orb-1"></div>
      <div class="gradient-orb orb-2"></div>
    </div>

    <!-- 导航 -->
    <nav class="checkin-nav">
      <div class="nav-brand" @click="$router.push('/')">
        <div class="brand-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 2L2 7l10 5 10-5-10-5z"/>
            <path d="M2 17l10 5 10-5"/>
          </svg>
        </div>
        <span>ClassHub</span>
      </div>
      
      <div class="nav-info">
        <div class="info-item">
          <div class="info-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <polyline points="12 6 12 12 16 14"/>
            </svg>
          </div>
          <span>{{ currentTime }}</span>
        </div>
        <n-tag :type="classSession.active ? 'success' : 'error'" round size="small">
          {{ classSession.active ? '上课中' : '未开始上课' }}
        </n-tag>
      </div>
    </nav>

    <!-- 主内容 -->
    <main class="checkin-main">
      <!-- 页面标题 -->
      <div class="page-header">
        <h1>学生签到</h1>
        <p v-if="classSession.active">当前班级：{{ classSession.class_name }}</p>
        <p v-else>请等待老师开始上课后再签到</p>
      </div>

      <!-- 签到区域 -->
      <n-card class="checkin-card" :class="{ active: classSession.active }">
        <div class="checkin-form">
          <div class="input-section">
            <label>学号</label>
            <n-input 
              v-model:value="checkinForm.student_id" 
              placeholder="请输入学号"
              size="large"
              :disabled="!classSession.active || checkingIn"
              @keyup.enter="handleCheckin"
            >
              <template #prefix>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 18px; height: 18px;">
                  <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                  <circle cx="9" cy="7" r="4"/>
                </svg>
              </template>
            </n-input>
          </div>
          
          <div class="input-section">
            <label>姓名</label>
            <n-input 
              v-model:value="checkinForm.name" 
              placeholder="请输入姓名"
              size="large"
              :disabled="!classSession.active || checkingIn"
              @keyup.enter="handleCheckin"
            >
              <template #prefix>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 18px; height: 18px;">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                  <circle cx="12" cy="7" r="4"/>
                </svg>
              </template>
            </n-input>
          </div>
          
          <n-button 
            type="primary" 
            size="large" 
            :loading="checkingIn"
            :disabled="!classSession.active || !checkinForm.student_id || !checkinForm.name"
            @click="handleCheckin"
            class="checkin-btn"
          >
            <template #icon>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 20px; height: 20px;">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
            </template>
            确认签到
          </n-button>
        </div>
      </n-card>

      <!-- 已签到人员 -->
      <n-card class="checked-in-card">
        <template #header>
          <div class="card-header">
            <div class="header-title">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 20px; height: 20px;">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
                <line x1="16" y1="13" x2="8" y2="13"/>
                <line x1="16" y1="17" x2="8" y2="17"/>
              </svg>
              <span>今日签到</span>
            </div>
            <n-tag type="success" size="small" round>{{ checkedInStudents.length }} 人已签到</n-tag>
          </div>
        </template>

        <div class="student-tags">
          <div 
            v-for="student in checkedInStudents" 
            :key="student.student_id" 
            class="student-tag"
          >
            <div class="tag-avatar">{{ student.name.charAt(0) }}</div>
            <div class="tag-info">
              <span class="tag-name">{{ student.name }}</span>
              <span class="tag-class">{{ student.class_name }}</span>
            </div>
            <n-tag type="success" size="tiny" round>已签到</n-tag>
          </div>
          
          <n-empty v-if="checkedInStudents.length === 0" description="暂无签到记录" />
        </div>
      </n-card>

      <!-- 我的签到记录 -->
      <n-card class="my-records-card" v-if="myCheckinRecords.length > 0">
        <template #header>
          <div class="card-header">
            <div class="header-title">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 20px; height: 20px;">
                <circle cx="12" cy="12" r="10"/>
                <polyline points="12 6 12 12 16 14"/>
              </svg>
              <span>我的签到记录</span>
            </div>
          </div>
        </template>

        <div class="records-list">
          <div 
            v-for="record in myCheckinRecords" 
            :key="record.id" 
            class="record-item"
            :class="{ success: record.success, fail: !record.success }"
          >
            <div class="record-status">
              <div class="status-icon" :class="{ success: record.success, fail: !record.success }">
                <svg v-if="record.success" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
                <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="10"/>
                  <line x1="15" y1="9" x2="9" y2="15"/>
                  <line x1="9" y1="9" x2="15" y2="15"/>
                </svg>
              </div>
            </div>
            
            <div class="record-content">
              <div class="record-title">{{ record.message }}</div>
              <div class="record-time">{{ formatTime(record.timestamp) }}</div>
            </div>
          </div>
        </div>
      </n-card>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { checkin, getClassSession, getClassSessionStudents } from '@/api'

const message = useMessage()

// 数据
const classSession = ref({ active: false })
const checkedInStudents = ref([])
const checkinForm = ref({ student_id: '', name: '' })
const checkingIn = ref(false)
const myCheckinRecords = ref([])

// 时间显示
const currentTime = ref('')
let timeInterval = null

const updateTime = () => {
  const now = new Date()
  currentTime.value = now.toLocaleTimeString('zh-CN', { 
    hour: '2-digit', 
    minute: '2-digit' 
  })
}

// 加载上课状态
const loadClassSession = async () => {
  try {
    const res = await getClassSession()
    if (res.success) {
      classSession.value = res.data
      if (res.data.active) {
        loadCheckedInStudents()
      }
    }
  } catch (error) {
    // 静默失败
  }
}

// 加载已签到学生
const loadCheckedInStudents = async () => {
  try {
    const res = await getClassSessionStudents()
    if (res.success) {
      checkedInStudents.value = res.data.students.filter(s => s.checked_in)
    }
  } catch (error) {
    // 静默失败
  }
}

// 签到
const handleCheckin = async () => {
  if (!checkinForm.value.student_id || !checkinForm.value.name) {
    message.warning('请填写学号和姓名')
    return
  }

  checkingIn.value = true
  
  try {
    const res = await checkin({
      student_id: checkinForm.value.student_id,
      name: checkinForm.value.name
    })
    
    // 添加到我的记录
    myCheckinRecords.value.unshift({
      id: Date.now(),
      success: res.success,
      message: res.success ? '签到成功！' : (res.message || '签到失败'),
      timestamp: new Date().toISOString()
    })
    
    // 只保留最近5条记录
    if (myCheckinRecords.value.length > 5) {
      myCheckinRecords.value = myCheckinRecords.value.slice(0, 5)
    }
    
    if (res.success) {
      message.success(res.message)
      checkinForm.value = { student_id: '', name: '' }
      loadCheckedInStudents()
    } else {
      message.error(res.message || '签到失败')
    }
  } catch (error) {
    message.error('网络错误，请稍后重试')
    
    myCheckinRecords.value.unshift({
      id: Date.now(),
      success: false,
      message: '网络错误，请稍后重试',
      timestamp: new Date().toISOString()
    })
  } finally {
    checkingIn.value = false
  }
}

const formatTime = (time) => {
  if (!time) return ''
  const utcTime = time.endsWith('Z') ? time : time + 'Z'
  return new Date(utcTime).toLocaleString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

let refreshInterval = null

onMounted(() => {
  updateTime()
  timeInterval = setInterval(updateTime, 1000)
  loadClassSession()
  
  // 每5秒刷新一次状态
  refreshInterval = setInterval(() => {
    loadClassSession()
  }, 5000)
})

onUnmounted(() => {
  if (timeInterval) clearInterval(timeInterval)
  if (refreshInterval) clearInterval(refreshInterval)
})
</script>

<style scoped>
.checkin-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #0a0a0f 0%, #12121a 50%, #0d0d14 100%);
  position: relative;
}

/* 背景装饰 */
.bg-decoration {
  position: fixed;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
  z-index: 0;
}

.gradient-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.15;
}

.orb-1 {
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, #6366f1, transparent);
  top: -100px;
  right: -100px;
}

.orb-2 {
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, #06b6d4, transparent);
  bottom: 10%;
  left: -50px;
}

/* 导航 */
.checkin-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 32px;
  background: rgba(19, 19, 31, 0.8);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  position: relative;
  z-index: 10;
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  color: white;
  font-weight: 600;
  font-size: 1.1rem;
}

.brand-icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border-radius: 10px;
}

.brand-icon svg {
  width: 20px;
  height: 20px;
}

.nav-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.9rem;
}

.info-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
}

.info-icon svg {
  width: 16px;
  height: 16px;
}

/* 主内容 */
.checkin-main {
  max-width: 600px;
  margin: 0 auto;
  padding: 48px 24px;
  position: relative;
  z-index: 1;
}

.page-header {
  text-align: center;
  margin-bottom: 32px;
}

.page-header h1 {
  font-size: 2rem;
  font-weight: 700;
  color: white;
  margin-bottom: 8px;
}

.page-header p {
  color: rgba(255, 255, 255, 0.5);
  font-size: 1rem;
}

/* 签到卡片 */
.checkin-card {
  background: rgba(255, 255, 255, 0.03) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  margin-bottom: 24px;
}

.checkin-card.active {
  border-color: rgba(99, 102, 241, 0.3) !important;
  background: rgba(99, 102, 241, 0.05) !important;
}

.checkin-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.input-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.input-section label {
  font-size: 0.9rem;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.7);
}

.checkin-btn {
  margin-top: 8px;
  height: 48px;
  font-size: 1rem;
  background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
}

.checkin-btn:not(:disabled):hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(99, 102, 241, 0.4);
}

/* 已签到卡片 */
.checked-in-card,
.my-records-card {
  background: rgba(255, 255, 255, 0.03) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
}

.checked-in-card {
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 10px;
  color: white;
  font-weight: 600;
}

.student-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.student-tag {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.2);
  border-radius: 12px;
}

.tag-avatar {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  color: white;
}

.tag-info {
  display: flex;
  flex-direction: column;
}

.tag-name {
  font-weight: 500;
  color: white;
  font-size: 0.9rem;
}

.tag-class {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
}

/* 我的记录 */
.records-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.record-item {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 14px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12px;
  border: 1px solid transparent;
}

.record-item.success {
  background: rgba(16, 185, 129, 0.08);
  border-color: rgba(16, 185, 129, 0.15);
}

.record-item.fail {
  background: rgba(239, 68, 68, 0.08);
  border-color: rgba(239, 68, 68, 0.15);
}

.status-icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
}

.status-icon.success {
  background: rgba(16, 185, 129, 0.2);
  color: #34d399;
}

.status-icon.fail {
  background: rgba(239, 68, 68, 0.2);
  color: #f87171;
}

.status-icon svg {
  width: 18px;
  height: 18px;
}

.record-content {
  flex: 1;
}

.record-title {
  font-weight: 500;
  color: white;
  font-size: 0.95rem;
}

.record-time {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.4);
  margin-top: 4px;
}

/* 响应式 */
@media (max-width: 640px) {
  .checkin-nav {
    padding: 12px 16px;
  }
  
  .nav-brand span {
    display: none;
  }
  
  .checkin-main {
    padding: 32px 16px;
  }
  
  .page-header h1 {
    font-size: 1.5rem;
  }
}
</style>
