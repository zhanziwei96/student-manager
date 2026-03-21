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
        <n-tag :type="dbInfo.env === 'testing' ? 'warning' : 'success'" size="small" round>
          {{ dbInfo.name || '生产环境' }}
        </n-tag>
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
            <!-- 签到率 - 环形进度条 -->
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

        <n-card class="action-card" hoverable @click="showResetScore = true">
          <div class="action-icon" style="background: linear-gradient(135deg, #f59e0b, #fbbf24);">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="23 4 23 10 17 10"/>
              <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
            </svg>
          </div>
          <div class="action-title">重置分数</div>
          <div class="action-desc">重置所有学生分数</div>
        </n-card>

        <n-card class="action-card" hoverable @click="showAddTeacher = true">
          <div class="action-icon" style="background: linear-gradient(135deg, #ec4899, #f472b6);">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
              <circle cx="12" cy="7" r="4"/>
              <line x1="16" y1="11" x2="16" y2="11"/>
              <line x1="8" y1="11" x2="8" y2="11"/>
            </svg>
          </div>
          <div class="action-title">新增教师</div>
          <div class="action-desc">创建教师账号</div>
        </n-card>

        <n-card class="action-card" hoverable @click="showManageTeachers = true">
          <div class="action-icon" style="background: linear-gradient(135deg, #06b6d4, #22d3ee);">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
              <circle cx="9" cy="7" r="4"/>
              <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
              <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
            </svg>
          </div>
          <div class="action-title">教师管理</div>
          <div class="action-desc">管理教师班级分配</div>
        </n-card>
      </div>

      <!-- 学生列表 -->
      <n-card class="student-list-card">
        <template #header>
          <div class="list-header">
            <div class="header-title">
              <span>学生列表</span>
              <n-tag type="info" size="small">共 {{ students.length }} 人</n-tag>
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
                <n-button text type="error" size="small" @click.stop="handleDeleteClass(group.className)">
                  删除班级
                </n-button>
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
      <n-alert type="info" :show-icon="true" style="margin-bottom: 16px;">
        <template #header>
          账号信息
        </template>
        <div v-if="newStudent.student_id">
          <p><strong>用户名：</strong>{{ newStudent.student_id }}</p>
          <p><strong>初始密码：</strong>{{ newStudent.student_id }}（与学号相同）</p>
        </div>
        <div v-else>
          填写学号后将自动显示账号信息
        </div>
      </n-alert>
      <n-form :model="newStudent" label-placement="left" label-width="80px">
        <n-form-item label="学号" required>
          <n-input v-model:value="newStudent.student_id" placeholder="请输入学号（作为登录账号）" />
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
          <n-input v-model:value="importClassName" placeholder="如果Excel中没有班级列，将使用此值" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-button @click="showImport = false">取消</n-button>
        <n-button type="primary" @click="handleImport" :loading="importLoading">导入</n-button>
      </template>
    </n-modal>

    <!-- 重置分数对话框 -->
    <n-modal v-model:show="showResetScore" title="重置所有分数" preset="card" style="width: 400px;">
      <n-alert type="warning" title="警告" :show-icon="true" style="margin-bottom: 16px;">
        此操作将重置所有学生的分数，且无法撤销！
      </n-alert>
      <n-form label-placement="left" label-width="100px">
        <n-form-item label="默认分数">
          <n-input-number v-model:value="resetScoreValue" :min="0" :max="100" />
        </n-form-item>
        <n-form-item label="管理员密码" required>
          <n-input v-model:value="resetPassword" type="password" show-password-on="mousedown" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-button @click="showResetScore = false">取消</n-button>
        <n-button type="error" @click="handleResetScores">确认重置</n-button>
      </template>
    </n-modal>

    <!-- 新增教师对话框 -->
    <n-modal v-model:show="showAddTeacher" title="新增教师" preset="card" style="width: 500px;">
      <n-alert type="info" :show-icon="true" style="margin-bottom: 16px;">
        默认密码为教师名字拼音首字母缩写 + 123（例如：张三 → zs123）
      </n-alert>
      <n-form :model="newTeacher" label-placement="left" label-width="100px">
        <n-form-item label="用户名" required>
          <n-input v-model:value="newTeacher.username" placeholder="请输入用户名（建议使用拼音，如：zhangsan）" />
        </n-form-item>
        <n-form-item label="姓名" required>
          <n-input v-model:value="newTeacher.name" placeholder="请输入教师姓名（如：张三）" />
        </n-form-item>
        <n-form-item label="负责班级">
          <n-select v-model:value="newTeacher.assigned_classes" placeholder="选择负责班级（可多选）" :options="classOptions" multiple clearable />
        </n-form-item>
        <n-form-item label="默认密码">
          <n-input :value="newTeacher.username ? generateTeacherPassword(newTeacher.username) : '填写用户名后自动生成'" disabled />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-button @click="showAddTeacher = false">取消</n-button>
        <n-button type="primary" @click="handleAddTeacher">确认创建</n-button>
      </template>
    </n-modal>

    <!-- 教师管理对话框 -->
    <n-modal v-model:show="showManageTeachers" title="教师管理" preset="card" style="width: 800px; max-height: 80vh;">
      <div class="teacher-list-header" style="margin-bottom: 16px;">
        <n-space>
          <n-tag type="info">共 {{ teachers.length }} 位教师</n-tag>
          <n-tag type="success">{{ teachers.filter(t => t.status === 'active').length }} 位在职</n-tag>
          <n-tag type="error">{{ teachers.filter(t => t.status !== 'active').length }} 位禁用</n-tag>
        </n-space>
      </div>
      
      <n-data-table
        :columns="teacherColumns"
        :data="teachers"
        :pagination="{ pageSize: 10 }"
        :bordered="false"
        size="small"
        striped
      />
      
      <template #footer>
        <n-button @click="showManageTeachers = false">关闭</n-button>
      </template>
    </n-modal>

    <!-- 编辑教师对话框 -->
    <n-modal v-model:show="showEditTeacher" title="编辑教师" preset="card" style="width: 500px;">
      <n-form :model="editingTeacher" label-placement="left" label-width="100px">
        <n-form-item label="用户名">
          <n-input v-model:value="editingTeacher.username" disabled />
        </n-form-item>
        <n-form-item label="姓名">
          <n-input v-model:value="editingTeacher.name" disabled />
        </n-form-item>
        <n-form-item label="负责班级">
          <n-select v-model:value="editingTeacher.assigned_classes" placeholder="选择负责班级（可多选）" :options="classOptions" multiple clearable />
        </n-form-item>
        <n-form-item label="账号状态">
          <n-select v-model:value="editingTeacher.status" :options="[{label: '启用', value: 'active'}, {label: '禁用', value: 'inactive'}]" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-button @click="showEditTeacher = false">取消</n-button>
        <n-button type="primary" @click="handleUpdateTeacher">保存修改</n-button>
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

    <!-- 删除确认对话框 -->
    <n-modal v-model:show="deleteDialogVisible" title="安全验证" preset="card" style="width: 400px;">
      <n-alert type="warning" :show-icon="true" style="margin-bottom: 16px;">
        {{ deleteMessage }}
      </n-alert>
      <n-form>
        <n-form-item label="请输入管理员密码">
          <n-input v-model:value="deletePassword" type="password" show-password-on="mousedown" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-button @click="deleteDialogVisible = false">取消</n-button>
        <n-button type="error" @click="handleConfirmDelete">确认删除</n-button>
      </template>
    </n-modal>

    <!-- 修改密码对话框 -->
    <n-modal v-model:show="changePasswordVisible" title="修改密码" preset="card" style="width: 400px;">
      <n-form label-placement="left" label-width="100px">
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
import { ref, computed, onMounted, h } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import * as api from '@/api'
import { NIcon } from 'naive-ui'
import { CreateOutline, TrashOutline, KeyOutline, BanOutline, CheckmarkCircleOutline } from '@vicons/ionicons5'

const router = useRouter()
const userStore = useUserStore()
const message = useMessage()
const dialog = useDialog()

const userName = ref(userStore.userName || '老师')

// 数据
const students = ref([])
const searchQuery = ref('')
const activeGroups = ref([])
const dbInfo = ref({})

// 控制显示
const showAddStudent = ref(false)
const showImport = ref(false)
const showResetScore = ref(false)
const showAddTeacher = ref(false)
const showManageTeachers = ref(false)
const showEditTeacher = ref(false)
const scoreDialogVisible = ref(false)
const deleteDialogVisible = ref(false)
const changePasswordVisible = ref(false)

// 添加学生
const newStudent = ref({ student_id: '', name: '', class_name: '' })

// 添加教师
const newTeacher = ref({ username: '', name: '', assigned_classes: [] })

// 教师管理
const teachers = ref([])
const editingTeacher = ref({ id: null, username: '', name: '', assigned_classes: [], status: 'active' })

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

// 根据签到率返回颜色
const getRateColor = (rate) => {
  if (rate >= 90) return '#10b981' // 绿色
  if (rate >= 60) return '#f59e0b' // 橙色
  return '#ef4444' // 红色
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

// 删除确认
const deleteMessage = ref('')
const deletePassword = ref('')
const pendingDelete = ref({ type: '', data: null })

// 修改密码
const passwordForm = ref({ old: '', new: '', confirm: '' })

// 用户下拉选项
const userOptions = [
  { label: '修改密码', key: 'changePassword' },
  { label: '退出登录', key: 'logout' }
]

// 教师表格列定义
const teacherColumns = [
  { title: '用户名', key: 'username', width: 120 },
  { title: '姓名', key: 'name', width: 100 },
  { 
    title: '负责班级', 
    key: 'assigned_classes', 
    width: 200,
    render(row) {
      if (!row.assigned_classes || row.assigned_classes.length === 0) {
        return h('span', { style: 'color: #64748b;' }, '未分配')
      }
      return h('div', { style: 'display: flex; flex-wrap: wrap; gap: 4px;' }, 
        row.assigned_classes.map(cls => 
          h('span', { 
            style: 'background: rgba(99, 102, 241, 0.15); color: #818cf8; padding: 2px 8px; border-radius: 4px; font-size: 12px;' 
          }, cls)
        )
      )
    }
  },
  { 
    title: '状态', 
    key: 'is_active', 
    width: 80,
    render(row) {
      return h('span', { 
        style: row.status === 'active' ? 'color: #34d399;' : 'color: #f87171;'
      }, row.status === 'active' ? '启用' : '禁用')
    }
  },
  {
    title: '操作',
    key: 'actions',
    width: 200,
    render(row) {
      return h('div', { style: 'display: flex; gap: 8px;' }, [
        h('button', { 
          class: 'icon-btn edit',
          title: '编辑',
          onClick: () => openEditTeacher(row)
        }, [
          h(NIcon, { size: 16, color: '#818cf8' }, { default: () => h(CreateOutline) })
        ]),
        h('button', {
          class: 'icon-btn reset',
          title: '重置密码',
          onClick: () => handleResetTeacherPassword(row)
        }, [
          h(NIcon, { size: 16, color: '#f59e0b' }, { default: () => h(KeyOutline) })
        ]),
        h('button', {
          class: row.status === 'active' ? 'icon-btn disable' : 'icon-btn enable',
          title: row.status === 'active' ? '禁用' : '启用',
          onClick: () => handleToggleTeacherStatus(row)
        }, [
          h(NIcon, { size: 16, color: row.status === 'active' ? '#ef4444' : '#10b981' }, { 
            default: () => row.status === 'active' ? h(BanOutline) : h(CheckmarkCircleOutline) 
          })
        ]),
        h('button', {
          class: 'icon-btn delete',
          title: '删除教师',
          onClick: () => handleDeleteTeacher(row)
        }, [
          h(NIcon, { size: 16, color: '#ef4444' }, { default: () => h(TrashOutline) })
        ])
      ])
    }
  }
]

// 表格列定义
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
    width: 140,
    render(row) {
      return h('div', { class: 'action-buttons' }, [
        h('button', { 
          class: 'icon-btn edit',
          title: '编辑分数',
          onClick: () => openScoreDialog(row)
        }, [
          h(NIcon, { size: 18, color: '#818cf8' }, { default: () => h(CreateOutline) })
        ]),
        h('button', {
          class: 'icon-btn reset',
          title: '重置密码',
          onClick: () => handleResetStudentPassword(row)
        }, [
          h(NIcon, { size: 18, color: '#f59e0b' }, { default: () => h(KeyOutline) })
        ]),
        h('button', {
          class: 'icon-btn delete',
          title: '删除学生',
          onClick: () => handleDeleteStudent(row)
        }, [
          h(NIcon, { size: 18, color: '#f87171' }, { default: () => h(TrashOutline) })
        ])
      ])
    }
  }
]

const classList = computed(() => {
  const classes = new Set(students.value.map(s => s.class_name).filter(Boolean))
  return Array.from(classes).sort()
})

const classOptions = computed(() => {
  return classList.value.map(cls => ({ label: cls, value: cls }))
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

// 生成默认密码（用户名前3位 + 123）
const generateTeacherPassword = (username) => {
  // 取用户名前3个字符（小写），不足3位则取全部
  const prefix = username.slice(0, 3).toLowerCase()
  return prefix + '123'
}

const handleAddTeacher = async () => {
  if (!newTeacher.value.username || !newTeacher.value.name) {
    message.warning('请填写用户名和姓名')
    return
  }
  
  const password = generateTeacherPassword(newTeacher.value.username)
  
  const res = await api.createUser({
    username: newTeacher.value.username,
    name: newTeacher.value.name,
    role: 'teacher',
    assigned_classes: newTeacher.value.assigned_classes,
    password: password
  })
  
  if (res.success) {
    message.success(`教师创建成功，默认密码：${password}`)
    newTeacher.value = { username: '', name: '', assigned_classes: [] }
    showAddTeacher.value = false
    loadTeachers()
  }
}

// 加载教师列表
const loadTeachers = async () => {
  const res = await api.getUsers()
  if (res.success) {
    // 前端过滤出教师角色
    teachers.value = res.data.filter(u => u.role === 'teacher')
  }
}

// 打开编辑教师对话框
const openEditTeacher = (teacher) => {
  editingTeacher.value = { 
    id: teacher.id,
    username: teacher.username,
    name: teacher.name,
    assigned_classes: [...teacher.assigned_classes],
    status: teacher.status
  }
  showEditTeacher.value = true
}

// 更新教师信息
const handleUpdateTeacher = async () => {
  const res = await api.updateUser(editingTeacher.value.id, {
    assigned_classes: editingTeacher.value.assigned_classes,
    status: editingTeacher.value.status
  })
  
  if (res.success) {
    message.success('教师信息更新成功')
    showEditTeacher.value = false
    loadTeachers()
  }
}

// 重置教师密码
const handleResetTeacherPassword = async (teacher) => {
  const newPassword = generateTeacherPassword(teacher.username)
  
  dialog.warning({
    title: '重置密码',
    content: `确定要重置 ${teacher.name} 的密码吗？新密码将为：${newPassword}`,
    positiveText: '确认重置',
    negativeText: '取消',
    onPositiveClick: async () => {
      const res = await api.resetUserPassword(teacher.id, { new_password: newPassword })
      if (res.success) {
        message.success(`密码已重置，新密码：${newPassword}`)
      }
    }
  })
}

// 切换教师账号状态
const handleToggleTeacherStatus = async (teacher) => {
  const action = teacher.status === 'active' ? '禁用' : '启用'
  
  dialog.warning({
    title: `${action}账号`,
    content: `确定要${action} ${teacher.name} 的账号吗？`,
    positiveText: '确认',
    negativeText: '取消',
    onPositiveClick: async () => {
      const res = await api.updateUser(teacher.id, { status: teacher.status === 'active' ? 'inactive' : 'active' })
      if (res.success) {
        message.success(`账号已${action}`)
        loadTeachers()
      }
    }
  })
}

// 删除教师
const handleDeleteTeacher = async (teacher) => {
  dialog.error({
    title: '删除教师',
    content: `确定要删除教师 "${teacher.name}" 吗？此操作不可撤销！`,
    positiveText: '确认删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      const res = await api.deleteUser(teacher.id)
      if (res.success) {
        message.success('教师已删除')
        loadTeachers()
      }
    }
  })
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

const handleResetScores = async () => {
  if (!resetPassword.value) {
    message.warning('请输入管理员密码')
    return
  }
  
  const authRes = await api.login({ username: 'admin', password: resetPassword.value })
  if (!authRes.success) {
    message.error('密码错误')
    return
  }
  
  const res = await api.resetAllScores({ default_score: resetScoreValue.value })
  if (res.success) {
    message.success(res.message)
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

// 重置学生密码
const handleResetStudentPassword = async (student) => {
  const newPassword = student.student_id  // 默认重置为学号
  
  dialog.warning({
    title: '重置学生密码',
    content: `确定要重置 "${student.name}" 的密码吗？新密码将为：${newPassword}`,
    positiveText: '确认重置',
    negativeText: '取消',
    onPositiveClick: async () => {
      const res = await api.resetStudentPassword(student.student_id, { password: newPassword })
      if (res.success) {
        message.success(`密码已重置，新密码：${newPassword}`)
      }
    }
  })
}

const handleDeleteClass = (className) => {
  deleteMessage.value = `确定要删除整个班级 "${className}" 吗？此操作将删除该班级所有学生，不可撤销！`
  pendingDelete.value = { type: 'class', data: className }
  deletePassword.value = ''
  deleteDialogVisible.value = true
}

const handleConfirmDelete = async () => {
  if (!deletePassword.value) {
    message.warning('请输入密码')
    return
  }
  
  const authRes = await api.login({ username: 'admin', password: deletePassword.value })
  if (!authRes.success) {
    message.error('密码错误')
    return
  }
  
  if (pendingDelete.value.type === 'student') {
    const res = await api.deleteStudent(pendingDelete.value.data.student_id)
    if (res.success) {
      message.success('删除成功')
      loadStudents()
    }
  } else if (pendingDelete.value.type === 'class') {
    const res = await api.deleteClass(pendingDelete.value.data)
    if (res.success) {
      message.success(res.message)
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
    message.success(res.message)
    scoreDialogVisible.value = false
    loadStudents()
  }
}

const applyScoreTag = (tag) => {
  scoreChange.value = tag.score
  scoreReason.value = tag.label
}

const startClass = async () => {
  if (!selectedClass.value) return
  const res = await api.setClassSession({ class_name: selectedClass.value })
  if (res.success) {
    message.success(res.message)
    loadClassSession()
  }
}

const endClass = async () => {
  const res = await api.setClassSession({ class_name: '' })
  if (res.success) {
    message.success(res.message)
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
        }
      }
    }
  } catch (error) {
    message.error('刷新状态失败')
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

const handleUserAction = (key) => {
  if (key === 'changePassword') {
    passwordForm.value = { old: '', new: '', confirm: '' }
    changePasswordVisible.value = true
  } else if (key === 'logout') {
    handleLogout()
  }
}

const handleChangePassword = async () => {
  if (!passwordForm.value.old || !passwordForm.value.new) {
    message.warning('请填写密码')
    return
  }
  if (passwordForm.value.new !== passwordForm.value.confirm) {
    message.warning('两次输入的密码不一致')
    return
  }
  if (passwordForm.value.new.length < 6) {
    message.warning('新密码长度至少为6位')
    return
  }
  
  const res = await api.changePassword({
    old_password: passwordForm.value.old,
    new_password: passwordForm.value.new
  })
  
  if (res.success) {
    message.success('密码修改成功，请重新登录')
    changePasswordVisible.value = false
    handleLogout()
  } else {
    message.error(res.message)
  }
}

const handleLogout = async () => {
  await api.logout()
  userStore.clearUser()
  router.push('/login')
}

onMounted(() => {
  loadStudents()
  loadClassSession()
  loadTeachers()
})
</script>

<style scoped>
.admin-layout {
  min-height: 100vh;
  background: linear-gradient(135deg, #0a0a0f 0%, #12121a 50%, #0d0d14 100%);
}

.admin-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 32px;
  height: 72px;
  background: rgba(19, 19, 31, 0.8);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
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
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border-radius: 10px;
}

.logo-icon svg {
  width: 22px;
  height: 22px;
  color: white;
}

.logo h1 {
  font-size: 22px;
  font-weight: 700;
  color: white;
  margin: 0;
  background: linear-gradient(135deg, #fff, #94a3b8);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.checkin-btn {
  background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 12px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  color: white;
}

.user-info:hover {
  background: rgba(255, 255, 255, 0.1);
}

.user-avatar {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border-radius: 50%;
  font-size: 12px;
  font-weight: 600;
}

.username {
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

/* 旧版样式兼容 */
.stats-row {
  display: flex;
  justify-content: space-around;
  margin-bottom: 24px;
  gap: 16px;
}

/* 新版增强样式 */
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

/* 旧版兼容 */
.stat-item {
  text-align: center;
  padding: 20px 40px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.stat-item.success {
  background: rgba(16, 185, 129, 0.1);
  border-color: rgba(16, 185, 129, 0.3);
}

.stat-item.success .stat-value {
  color: #34d399;
}

.stat-item.danger {
  background: rgba(239, 68, 68, 0.1);
  border-color: rgba(239, 68, 68, 0.3);
}

.stat-item.danger .stat-value {
  color: #f87171;
}

.stat-item.primary {
  background: rgba(99, 102, 241, 0.1);
  border-color: rgba(99, 102, 241, 0.3);
}

.stat-item.primary .stat-value {
  color: #818cf8;
}

.stat-value {
  font-size: 36px;
  font-weight: 700;
  color: white;
  margin-bottom: 4px;
}

.class-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
}

.quick-actions {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
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

/* 分数徽章样式 - 使用 :deep 确保应用到表格内部 */
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

/* 表头固定样式 */
:deep(.n-data-table .n-data-table-thead) {
  position: sticky;
  top: 0;
  z-index: 10;
}

:deep(.n-data-table .n-data-table-th) {
  background: rgba(19, 19, 31, 0.95) !important;
  backdrop-filter: blur(8px);
  font-weight: 600;
}

.action-btn {
  padding: 6px 12px;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.action-btn.edit {
  background: rgba(99, 102, 241, 0.2);
  color: #818cf8;
}

.action-btn.edit:hover {
  background: rgba(99, 102, 241, 0.3);
}

.action-btn.delete {
  background: rgba(239, 68, 68, 0.2);
  color: #f87171;
}

.action-btn.delete:hover {
  background: rgba(239, 68, 68, 0.3);
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

.icon-btn svg {
  stroke: currentColor;
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

.icon-btn.delete {
  color: #f87171;
  background: rgba(239, 68, 68, 0.1);
}

.icon-btn.delete:hover {
  background: rgba(239, 68, 68, 0.25);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.2);
}

.icon-btn.reset {
  color: #fbbf24;
  background: rgba(245, 158, 11, 0.1);
}

.icon-btn.reset:hover {
  background: rgba(245, 158, 11, 0.25);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(245, 158, 11, 0.2);
}

.icon-btn.enable {
  color: #34d399;
  background: rgba(16, 185, 129, 0.1);
}

.icon-btn.enable:hover {
  background: rgba(16, 185, 129, 0.25);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);
}

.icon-btn.disable {
  color: #f87171;
  background: rgba(239, 68, 68, 0.1);
}

.icon-btn.disable:hover {
  background: rgba(239, 68, 68, 0.25);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.2);
}

.icon-btn:active {
  transform: scale(0.95);
}

.teacher-list-header {
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.tip {
  color: #64748b;
  font-size: 13px;
}
</style>
