<template>
  <el-container class="admin-container">
    <!-- 顶部导航 -->
    <el-header class="admin-header">
      <div class="header-left">
        <div class="logo">
          <el-icon size="28"><School /></el-icon>
          <h1>班级管理系统</h1>
        </div>
        <el-tag 
          :type="dbInfo.env === 'testing' ? 'warning' : 'success'"
          effect="dark"
          class="env-tag"
        >
          {{ dbInfo.name || '生产环境' }}
        </el-tag>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="$router.push('/checkin')" class="checkin-btn">
          <el-icon><EditPen /></el-icon>
          学生签到
        </el-button>
        <el-dropdown>
          <span class="user-info">
            <el-avatar :size="32" :icon="UserFilled" />
            <span class="username">{{ userName }}</span>
            <el-icon><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="openChangePasswordDialog">
                <el-icon><Lock /></el-icon>修改密码
              </el-dropdown-item>
              <el-dropdown-item divided @click="handleLogout">
                <el-icon><SwitchButton /></el-icon>退出登录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </el-header>
    
    <el-main class="admin-main">
      <!-- 上课控制卡片 -->
      <el-card class="control-card" :class="{ 'active': classSession.active }">
        <template #header>
          <div class="card-header">
            <div class="header-title">
              <el-icon size="20"><VideoPlay v-if="!classSession.active" /><VideoPause v-else /></el-icon>
              <span>{{ classSession.active ? '上课中' : '上课控制' }}</span>
            </div>
            <el-tag v-if="classSession.active" type="success" effect="dark">
              {{ classSession.class_name }}
            </el-tag>
          </div>
        </template>
        
        <div v-if="!classSession.active" class="class-selector">
          <el-select 
            v-model="selectedClass" 
            placeholder="选择上课班级" 
            size="large"
            clearable
            style="width: 280px;"
          >
            <el-option
              v-for="cls in classList"
              :key="cls"
              :label="cls"
              :value="cls"
            />
          </el-select>
          <el-button 
            type="success" 
            size="large" 
            @click="startClass"
            :disabled="!selectedClass"
          >
            <el-icon><VideoPlay /></el-icon>
            开始上课
          </el-button>
        </div>
        
        <div v-else class="class-info">
          <div class="stats-row">
            <div class="stat-item">
              <div class="stat-value">{{ classStats.total }}</div>
              <div class="stat-label">应到人数</div>
            </div>
            <div class="stat-item success">
              <div class="stat-value">{{ classStats.checked_in }}</div>
              <div class="stat-label">已签到</div>
            </div>
            <div class="stat-item danger">
              <div class="stat-value">{{ classStats.not_checked_in }}</div>
              <div class="stat-label">未签到</div>
            </div>
            <div class="stat-item primary">
              <div class="stat-value">{{ classStats.rate }}%</div>
              <div class="stat-label">签到率</div>
            </div>
          </div>
          <div class="class-actions">
            <el-button @click="refreshClassStatus" :icon="Refresh">刷新状态</el-button>
            <el-button type="danger" @click="endClass" :icon="CircleCloseFilled">结束上课</el-button>
          </div>
        </div>
      </el-card>
      
      <!-- 快捷操作区 -->
      <el-row :gutter="20" class="quick-actions">
        <el-col :span="8">
          <el-card class="action-card" shadow="hover" @click="showAddStudent = true">
            <el-icon class="action-icon" color="#409EFF"><User /></el-icon>
            <div class="action-title">添加学生</div>
            <div class="action-desc">单个添加学生信息</div>
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card class="action-card" shadow="hover" @click="showImport = true">
            <el-icon class="action-icon" color="#67C23A"><Upload /></el-icon>
            <div class="action-title">导入班级</div>
            <div class="action-desc">批量导入Excel文件</div>
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card class="action-card" shadow="hover" @click="showResetScore = true">
            <el-icon class="action-icon" color="#E6A23C"><Refresh /></el-icon>
            <div class="action-title">重置分数</div>
            <div class="action-desc">重置所有学生分数</div>
          </el-card>
        </el-col>
      </el-row>
      
      <!-- 学生列表 -->
      <el-card class="student-list-card">
        <template #header>
          <div class="card-header">
            <div class="header-title">
              <span>👥 学生列表</span>
              <el-tag type="info" effect="plain">共 {{ students.length }} 人</el-tag>
            </div>
            <div class="header-actions">
              <el-input
                v-model="searchQuery"
                placeholder="搜索学号或姓名"
                clearable
                style="width: 200px;"
                :prefix-icon="Search"
              />
              <el-button-group>
                <el-button @click="expandAll">全部展开</el-button>
                <el-button @click="collapseAll">全部折叠</el-button>
                <el-button type="primary" @click="loadStudents" :icon="Refresh">刷新</el-button>
              </el-button-group>
            </div>
          </div>
        </template>
        
        <div class="class-groups">
          <el-collapse v-model="activeGroups">
            <el-collapse-item
              v-for="group in groupedStudents"
              :key="group.className"
              :name="group.className"
            >
              <template #title>
                <div class="collapse-title">
                  <span class="class-name">{{ group.className }}</span>
                  <el-tag size="small" type="info">{{ group.students.length }} 人</el-tag>
                  <el-button 
                    type="danger" 
                    link 
                    size="small" 
                    @click.stop="handleDeleteClass(group.className)"
                  >
                    删除班级
                  </el-button>
                </div>
              </template>
              
              <el-table :data="group.students" stripe>
                <el-table-column prop="student_id" label="学号" width="120" />
                <el-table-column prop="name" label="姓名" width="100" />
                <el-table-column prop="class_name" label="班级" />
                <el-table-column prop="score" label="分数" width="100">
                  <template #default="scope">
                    <el-tag :type="getScoreType(scope.row.score)">
                      {{ scope.row.score }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="200" fixed="right">
                  <template #default="scope">
                    <el-button
                      type="primary"
                      size="small"
                      :icon="Edit"
                      @click="openScoreDialog(scope.row)"
                    >
                      分数
                    </el-button>
                    <el-button
                      type="danger"
                      size="small"
                      :icon="Delete"
                      @click="handleDeleteStudent(scope.row)"
                    >
                      删除
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
            </el-collapse-item>
          </el-collapse>
          
          <el-empty v-if="groupedStudents.length === 0" description="暂无学生数据" />
        </div>
      </el-card>
    </el-main>
    
    <!-- 添加学生对话框 -->
    <el-dialog v-model="showAddStudent" title="添加学生" width="500px">
      <el-form :model="newStudent" label-width="80px">
        <el-form-item label="学号" required>
          <el-input v-model="newStudent.student_id" placeholder="请输入学号" />
        </el-form-item>
        <el-form-item label="姓名" required>
          <el-input v-model="newStudent.name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="班级">
          <el-input v-model="newStudent.class_name" placeholder="班级（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddStudent = false">取消</el-button>
        <el-button type="primary" @click="handleAddStudent">确认添加</el-button>
      </template>
    </el-dialog>
    
    <!-- 导入班级对话框 -->
    <el-dialog v-model="showImport" title="导入班级" width="500px">
      <el-form label-width="100px">
        <el-form-item label="Excel文件">
          <el-upload
            action="/api/students/import"
            :auto-upload="false"
            :on-change="handleFileChange"
            :limit="1"
            accept=".xlsx,.xls"
          >
            <el-button type="primary">选择文件</el-button>
          </el-upload>
        </el-form-item>
        <el-form-item label="默认班级">
          <el-input v-model="importClassName" placeholder="如果Excel中没有班级列，将使用此值" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showImport = false">取消</el-button>
        <el-button type="primary" @click="handleImport" :loading="importLoading">导入</el-button>
      </template>
    </el-dialog>
    
    <!-- 重置分数对话框 -->
    <el-dialog v-model="showResetScore" title="重置所有分数" width="400px">
      <el-alert
        title="警告"
        description="此操作将重置所有学生的分数，且无法撤销！"
        type="warning"
        show-icon
        :closable="false"
        style="margin-bottom: 20px;"
      />
      <el-form label-width="100px">
        <el-form-item label="默认分数">
          <el-input-number v-model="resetScoreValue" :min="0" :max="100" />
        </el-form-item>
        <el-form-item label="管理员密码" required>
          <el-input v-model="resetPassword" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showResetScore = false">取消</el-button>
        <el-button type="danger" @click="handleResetScores">确认重置</el-button>
      </template>
    </el-dialog>
    
    <!-- 调整分数对话框 -->
    <el-dialog v-model="scoreDialogVisible" title="调整分数" width="450px">
      <div class="student-info">
        <span>学生：{{ selectedStudent.name }}</span>
        <span>学号：{{ selectedStudent.student_id }}</span>
      </div>
      <el-form label-width="80px">
        <el-form-item label="分数变更">
          <el-input-number v-model="scoreChange" :min="-100" :max="100" />
          <span class="tip">正数加分，负数扣分</span>
        </el-form-item>
        <el-form-item label="快捷标签">
          <div class="score-tags">
            <el-tag 
              v-for="tag in scoreTags" 
              :key="tag.label"
              :type="tag.score > 0 ? 'success' : 'danger'"
              class="score-tag"
              @click="applyScoreTag(tag)"
              style="cursor: pointer; margin-right: 8px; margin-bottom: 8px;"
            >
              {{ tag.label }} {{ tag.score > 0 ? '+' : '' }}{{ tag.score }}分
            </el-tag>
          </div>
        </el-form-item>
        <el-form-item label="变更原因">
          <el-input v-model="scoreReason" type="textarea" rows="3" placeholder="请输入分数变更原因" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="scoreDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleUpdateScore">确认调整</el-button>
      </template>
    </el-dialog>
    
    <!-- 删除确认对话框 -->
    <el-dialog v-model="deleteDialogVisible" title="安全验证" width="400px">
      <el-alert
        :title="deleteMessage"
        type="warning"
        show-icon
        :closable="false"
        style="margin-bottom: 20px;"
      />
      <el-form>
        <el-form-item label="请输入管理员密码">
          <el-input v-model="deletePassword" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="deleteDialogVisible = false">取消</el-button>
        <el-button type="danger" @click="handleConfirmDelete">确认删除</el-button>
      </template>
    </el-dialog>
    
    <!-- 修改密码对话框 -->
    <el-dialog v-model="changePasswordVisible" title="修改密码" width="400px">
      <el-form label-width="100px">
        <el-form-item label="原密码" required>
          <el-input v-model="passwordForm.old" type="password" show-password />
        </el-form-item>
        <el-form-item label="新密码" required>
          <el-input v-model="passwordForm.new" type="password" show-password />
        </el-form-item>
        <el-form-item label="确认密码" required>
          <el-input v-model="passwordForm.confirm" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="changePasswordVisible = false">取消</el-button>
        <el-button type="primary" @click="handleChangePassword">确认修改</el-button>
      </template>
    </el-dialog>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  School, User, UserFilled, ArrowDown, Lock, SwitchButton,
  VideoPlay, VideoPause, Refresh, CircleCloseFilled,
  Upload, Edit, Delete, Search, EditPen
} from '@element-plus/icons-vue'
import Cookies from 'js-cookie'
import * as api from '../api'

const router = useRouter()
const userName = ref(Cookies.get('name') || '老师')

// 数据
const students = ref([])
const searchQuery = ref('')
const activeGroups = ref([])
const dbInfo = ref({})

// 控制显示
const showAddStudent = ref(false)
const showImport = ref(false)
const showResetScore = ref(false)
const scoreDialogVisible = ref(false)
const deleteDialogVisible = ref(false)
const changePasswordVisible = ref(false)

// 添加学生
const newStudent = ref({ student_id: '', name: '', class_name: '' })

// 导入
const importFile = ref(null)
const importClassName = ref('')
const importLoading = ref(false)

// 重置分数
const resetScoreValue = ref(70)
const resetPassword = ref('')

// 上课状态
const classSession = ref({ active: false })
const selectedClass = ref('')
const classStats = ref({ total: 0, checked_in: 0, not_checked_in: 0, rate: 0 })

// 分数调整
const selectedStudent = ref({})
const scoreChange = ref(0)
const scoreReason = ref('')

// 分数变更快捷标签
const scoreTags = [
  { label: '回答问题', score: 2 },
  { label: '违反课堂纪律', score: -2 },
  { label: '旷课', score: -5 },
  { label: '未交作业', score: -2 }
]

// 应用分数标签
const applyScoreTag = (tag) => {
  scoreChange.value = tag.score
  scoreReason.value = tag.label
}

// 删除确认
const deleteMessage = ref('')
const deletePassword = ref('')
const pendingDelete = ref({ type: '', data: null })

// 修改密码
const passwordForm = ref({ old: '', new: '', confirm: '' })

// 计算属性
const classList = computed(() => {
  const classes = new Set(students.value.map(s => s.class_name).filter(Boolean))
  return Array.from(classes).sort()
})

const groupedStudents = computed(() => {
  const groups = {}
  const query = searchQuery.value.toLowerCase()
  
  students.value.forEach(student => {
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

// 方法
const loadStudents = async () => {
  const res = await api.getStudents()
  if (res.success) {
    students.value = res.data
    // 默认所有班级折叠
    activeGroups.value = []
  }
}

const handleAddStudent = async () => {
  if (!newStudent.value.student_id || !newStudent.value.name) {
    ElMessage.warning('请填写学号和姓名')
    return
  }
  
  const res = await api.addStudent(newStudent.value)
  if (res.success) {
    ElMessage.success('添加成功')
    newStudent.value = { student_id: '', name: '', class_name: '' }
    showAddStudent.value = false
    loadStudents()
  }
}

const handleFileChange = (file) => {
  importFile.value = file.raw
}

const handleImport = async () => {
  if (!importFile.value) {
    ElMessage.warning('请选择文件')
    return
  }
  
  importLoading.value = true
  const formData = new FormData()
  formData.append('file', importFile.value)
  formData.append('class_name', importClassName.value)
  
  const res = await api.importStudents(formData)
  importLoading.value = false
  
  if (res.success) {
    ElMessage.success(res.message)
    showImport.value = false
    loadStudents()
  }
}

const handleResetScores = async () => {
  if (!resetPassword.value) {
    ElMessage.warning('请输入管理员密码')
    return
  }
  
  // 验证密码
  const authRes = await api.login({ username: 'admin', password: resetPassword.value })
  if (!authRes.success) {
    ElMessage.error('密码错误')
    return
  }
  
  const res = await api.resetAllScores({ default_score: resetScoreValue.value })
  if (res.success) {
    ElMessage.success(res.message)
    showResetScore.value = false
    resetPassword.value = ''
    loadStudents()
  }
  
  await api.logout()
}

const handleDeleteStudent = (student) => {
  deleteMessage.value = `确定要删除学生 "${student.name}" 吗？此操作不可撤销！`
  pendingDelete.value = { type: 'student', data: student }
  deletePassword.value = ''
  deleteDialogVisible.value = true
}

const handleDeleteClass = (className) => {
  deleteMessage.value = `确定要删除整个班级 "${className}" 吗？此操作将删除该班级所有学生，不可撤销！`
  pendingDelete.value = { type: 'class', data: className }
  deletePassword.value = ''
  deleteDialogVisible.value = true
}

const handleConfirmDelete = async () => {
  if (!deletePassword.value) {
    ElMessage.warning('请输入密码')
    return
  }
  
  const authRes = await api.login({ username: 'admin', password: deletePassword.value })
  if (!authRes.success) {
    ElMessage.error('密码错误')
    return
  }
  
  if (pendingDelete.value.type === 'student') {
    const res = await api.deleteStudent(pendingDelete.value.data.student_id)
    if (res.success) {
      ElMessage.success('删除成功')
      loadStudents()
    }
  } else if (pendingDelete.value.type === 'class') {
    const res = await api.deleteClass(pendingDelete.value.data)
    if (res.success) {
      ElMessage.success(res.message)
      loadStudents()
    }
  }
  
  await api.logout()
  deleteDialogVisible.value = false
}

const openScoreDialog = (student) => {
  selectedStudent.value = student
  scoreChange.value = 0
  scoreReason.value = ''
  scoreDialogVisible.value = true
}

const handleUpdateScore = async () => {
  const res = await api.updateScore(selectedStudent.value.student_id, {
    score_change: scoreChange.value,
    reason: scoreReason.value
  })
  if (res.success) {
    ElMessage.success(res.message)
    scoreDialogVisible.value = false
    loadStudents()
  }
}

const getScoreType = (score) => {
  if (score >= 80) return 'success'
  if (score >= 60) return 'warning'
  return 'danger'
}

const startClass = async () => {
  if (!selectedClass.value) return
  const res = await api.setClassSession({ class_name: selectedClass.value })
  if (res.success) {
    ElMessage.success(res.message)
    loadClassSession()
  }
}

const endClass = async () => {
  const res = await api.setClassSession({ class_name: '' })
  if (res.success) {
    ElMessage.success(res.message)
    loadClassSession()
  }
}

const loadClassSession = async () => {
  try {
    const res = await api.getClassSession()
    if (res.success) {
      classSession.value = res.data
      if (res.data.active) {
        const studentsRes = await api.getClassSessionStudents()
        if (studentsRes.success) {
          const { total, checked_in, not_checked_in } = studentsRes.data
          classStats.value = {
            total,
            checked_in,
            not_checked_in,
            rate: total > 0 ? Math.round((checked_in / total) * 100) : 0
          }
        } else {
          ElMessage.warning(studentsRes.message || '获取学生列表失败')
        }
      }
    }
  } catch (error) {
    ElMessage.error('刷新状态失败，请重试')
    console.error('loadClassSession error:', error)
  }
}

const refreshClassStatus = async () => {
  await loadClassSession()
}

const expandAll = () => {
  activeGroups.value = groupedStudents.value.map(g => g.className)
}

const collapseAll = () => {
  activeGroups.value = []
}

const openChangePasswordDialog = () => {
  passwordForm.value = { old: '', new: '', confirm: '' }
  changePasswordVisible.value = true
}

const handleChangePassword = async () => {
  if (!passwordForm.value.old || !passwordForm.value.new) {
    ElMessage.warning('请填写密码')
    return
  }
  if (passwordForm.value.new !== passwordForm.value.confirm) {
    ElMessage.warning('两次输入的密码不一致')
    return
  }
  if (passwordForm.value.new.length < 6) {
    ElMessage.warning('新密码长度至少为6位')
    return
  }
  
  const res = await api.changePassword({
    old_password: passwordForm.value.old,
    new_password: passwordForm.value.new
  })
  
  if (res.success) {
    ElMessage.success('密码修改成功，请重新登录')
    changePasswordVisible.value = false
    handleLogout()
  } else {
    ElMessage.error(res.message)
  }
}

const handleLogout = async () => {
  await api.logout()
  Cookies.remove('user_id')
  Cookies.remove('username')
  Cookies.remove('name')
  router.push('/login')
}

// 检查是否已登录
const checkAuth = () => {
  const userId = Cookies.get('user_id')
  if (!userId) {
    router.push('/login')
    return false
  }
  return true
}

onMounted(() => {
  if (!checkAuth()) return
  loadStudents()
  loadClassSession()
  api.getDbInfo().then(res => {
    if (res.success) dbInfo.value = res.data
  })
})
</script>

<style scoped>
.admin-container {
  min-height: 100vh;
  background: #f5f7fa;
}

.admin-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  height: 64px;
  padding: 0 24px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.1);
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

.logo h1 {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
}

.env-tag {
  font-size: 12px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.checkin-btn {
  background: rgba(255,255,255,0.2);
  border: 1px solid rgba(255,255,255,0.3);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 12px;
  border-radius: 20px;
  background: rgba(255,255,255,0.1);
  transition: background 0.3s;
}

.user-info:hover {
  background: rgba(255,255,255,0.2);
}

.username {
  font-size: 14px;
}

.admin-main {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

.control-card {
  margin-bottom: 24px;
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.3s;
}

.control-card.active {
  background: linear-gradient(135deg, #f0f9ff 0%, #e6f7ff 100%);
  border: 1px solid #91d5ff;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
}

.class-selector {
  display: flex;
  align-items: center;
  gap: 16px;
}

.class-info {
  text-align: center;
}

.stats-row {
  display: flex;
  justify-content: space-around;
  margin-bottom: 24px;
}

.stat-item {
  text-align: center;
  padding: 16px 32px;
  border-radius: 8px;
  background: #f5f7fa;
  transition: all 0.3s;
}

.stat-item.success {
  background: #f6ffed;
  color: #52c41a;
}

.stat-item.danger {
  background: #fff2f0;
  color: #ff4d4f;
}

.stat-item.primary {
  background: #e6f7ff;
  color: #1890ff;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: #666;
}

.class-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
}

.quick-actions {
  margin-bottom: 24px;
}

.action-card {
  text-align: center;
  padding: 24px;
  cursor: pointer;
  transition: all 0.3s;
  border-radius: 12px;
}

.action-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.1);
}

.action-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.action-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 4px;
}

.action-desc {
  font-size: 13px;
  color: #999;
}

.student-list-card {
  border-radius: 12px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.class-groups {
  padding: 8px 0;
}

.collapse-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.class-name {
  font-weight: 600;
  font-size: 15px;
}

.student-info {
  display: flex;
  gap: 24px;
  margin-bottom: 16px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
}

.unit {
  margin-left: 8px;
  color: #666;
}

.tip {
  margin-left: 12px;
  color: #999;
  font-size: 13px;
}

:deep(.el-collapse-item__header) {
  padding: 0 16px;
  font-size: 15px;
}

:deep(.el-collapse-item__content) {
  padding: 16px;
}

:deep(.el-table) {
  border-radius: 8px;
  overflow: hidden;
}
</style>
