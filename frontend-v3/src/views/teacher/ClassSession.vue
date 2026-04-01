<script setup lang="ts">
import { ref, computed } from 'vue'
import { useClassSession, useClassSessionStart, useClassSessionEnd, useStudentCheckIn, useActiveClassSessions, useToast } from '@/composables'
import { useClasses, useClassStudents } from '@/composables/useClasses'
import { useSchedules } from '@/composables/useSchedules'
import { useTodayCheckins } from '@/composables/useCheckins'
import { useAuthStore } from '@/stores'
import { Card, Button, Input, Select, Badge, Dialog } from '@/components/ui'
import { Play, Square, CheckCircle, Clock, Users, Search, GraduationCap, AlertTriangle, MapPin, Loader2 } from 'lucide-vue-next'
import { formatTime } from '@/lib/date'
import { Toast } from '@/components/ui'
import { getErrorMessage } from '@/lib/error'

const className = ref('')
const courseName = ref('')
const studentCode = ref('')
const searchQuery = ref('')

// 地图选点相关
const showMapDialog = ref(false)
const selectedLocation = ref<{ lat: number; lng: number; name: string } | null>(null)
const checkinRadius = ref(100)
const isLoadingLocation = ref(false)
const mapContainer = ref<HTMLDivElement | null>(null)
const mapInstance = ref<any>(null)
const mapMarker = ref<any>(null)

// 获取当前用户信息
const authStore = useAuthStore()
const currentUser = computed(() => authStore.user)

const { data: activeSession } = useClassSession()
const { mutateAsync: startSession, isPending: isStartingSession } = useClassSessionStart()
const { mutateAsync: endSession, isPending: isEndingSession } = useClassSessionEnd()
const { mutateAsync: checkIn, isPending: isCheckingIn } = useStudentCheckIn(computed(() => activeSession.value?.class_name || ''))

// 获取活跃课堂列表
const { data: activeSessions } = useActiveClassSessions()

// 其他教师占用的班级（排除当前用户的）
const otherOccupiedClasses = computed(() => {
  if (!activeSessions.value) return []
  const currentUserId = currentUser.value?.id
  // 排除当前教师开启的所有课堂（不只是当前活跃课堂）
  return activeSessions.value.filter(s => s.teacher_id !== currentUserId)
})

// 可用的班级选项（被占用的标记为禁用）
const availableClassOptions = computed(() => {
  if (!classList.value) return []
  const occupiedMap = new Map(activeSessions.value?.map(s => [s.class_name, s.teacher_name]) || [])
  
  return classList.value.map(cls => {
    const teacherName = occupiedMap.get(cls.name)
    return {
      value: cls.name,
      label: teacherName ? `${cls.name} (已被 ${teacherName} 老师占用)` : cls.name,
      disabled: !!teacherName
    }
  })
})

// 获取班级列表
const { data: classList } = useClasses()

// 获取课程列表（用于选择）
const { data: schedules } = useSchedules()

// 可选的课程列表（根据教师分配的班级关联）
const courseOptions = computed(() => {
  if (!schedules.value) return []
  const courseNames = new Set(schedules.value.map(s => s.course_name).filter(Boolean))
  return Array.from(courseNames).map(name => ({ value: name, label: name }))
})

// 获取选中班级的学生列表
const { data: classStudents, isPending: isLoadingStudents } = useClassStudents(computed(() => activeSession.value?.class_name || ''))

// 获取当前课堂的签到记录
const { data: todayCheckins, refetch: refetchCheckins } = useTodayCheckins(computed(() => activeSession.value?.class_name || ''))

const { show, message: toastMessage, variant: toastVariant, success: showSuccessToast, error: showErrorToast } = useToast()



const isSessionActive = computed(() => !!activeSession.value)

// 已签到学生ID集合
const checkedInStudentIds = computed(() => {
  if (!todayCheckins.value) return new Set()
  return new Set(todayCheckins.value.map(c => c.student_id))
})

// REVIEW-P1: 预计算学生列表分组，避免在模板中重复 filter
const studentListWithCheckin = computed(() => {
  if (!classStudents.value) return []
  
  // 创建签到时间映射
  const checkinTimeMap = new Map<string, string>()
  if (todayCheckins.value) {
    todayCheckins.value.forEach(c => {
      checkinTimeMap.set(c.student_id, c.checkin_time)
    })
  }
  
  // 添加签到状态和时间
  let students = classStudents.value.map(s => ({
    ...s,
    checkedIn: checkedInStudentIds.value.has(s.student_id),
    checkinTime: checkinTimeMap.get(s.student_id)
  }))
  
  // 搜索过滤
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase()
    students = students.filter(s => 
      s.name.toLowerCase().includes(query) ||
      s.student_id.toLowerCase().includes(query)
    )
  }
  
  // 按签到状态排序（未签到在前）
  return students.sort((a, b) => (a.checkedIn === b.checkedIn ? 0 : a.checkedIn ? 1 : -1))
})

// 过滤后的学生列表（兼容原有代码）
const filteredStudents = computed(() => studentListWithCheckin.value)

// REVIEW-P1: 预计算分组，避免模板重复 filter
const notCheckedInStudents = computed(() => 
  studentListWithCheckin.value.filter(s => !s.checkedIn)
)

const checkedInStudents = computed(() => 
  studentListWithCheckin.value.filter(s => s.checkedIn)
)

// 签到统计
const checkinStats = computed(() => {
  if (!classStudents.value) return { total: 0, checkedIn: 0, notCheckedIn: 0 }
  const total = classStudents.value.length
  const checkedIn = classStudents.value.filter(s => checkedInStudentIds.value.has(s.student_id)).length
  return { total, checkedIn, notCheckedIn: total - checkedIn }
})

const handleStartSession = async () => {
  if (!className.value) {
    showErrorToast('请选择班级')
    return
  }

  // 打开地图选点对话框
  showMapDialog.value = true
  // 尝试获取当前位置作为默认位置
  if (navigator.geolocation) {
    isLoadingLocation.value = true
    navigator.geolocation.getCurrentPosition(
      (position) => {
        selectedLocation.value = {
          lat: position.coords.latitude,
          lng: position.coords.longitude,
          name: '当前位置'
        }
        // 反向地理编码获取地址名称
        reverseGeocode(position.coords.latitude, position.coords.longitude)
        isLoadingLocation.value = false
      },
      () => {
        // 定位失败，使用默认位置（学校中心）
        selectedLocation.value = {
          lat: 39.90923,  // 默认纬度（可根据学校位置调整）
          lng: 116.397428, // 默认经度
          name: '默认位置'
        }
        isLoadingLocation.value = false
      },
      { timeout: 5000 }
    )
  }
}

// 高德地图Key（从环境变量获取）
const AMAP_KEY = import.meta.env.VITE_AMAP_KEY || ''

// 反向地理编码
const reverseGeocode = (lat: number, lng: number) => {
  if (!AMAP_KEY) {
    // 没有配置Key，使用坐标作为位置名称
    selectedLocation.value!.name = `${lat.toFixed(4)}, ${lng.toFixed(4)}`
    return
  }
  
  // 使用高德地图逆地理编码API（添加extensions=all获取POI信息）
  fetch(`https://restapi.amap.com/v3/geocode/regeo?key=${AMAP_KEY}&location=${lng},${lat}&extensions=all&radius=100`)
    .then(res => res.json())
    .then(data => {
      if (data.status === '1' && data.regeocode) {
        const address = data.regeocode.formatted_address
        // 优先使用POI名称（如"XX大厦"），否则使用格式化地址
        const poi = data.regeocode.pois?.[0]?.name
        const street = data.regeocode.addressComponent?.street || ''
        const township = data.regeocode.addressComponent?.township || ''
        const district = data.regeocode.addressComponent?.district || ''
        const city = data.regeocode.addressComponent?.city || ''
        
        // 组合位置名称：POI名称 > 城市+区+街道 > 格式化地址 > 坐标
        let locationName = poi
        if (!locationName) {
          // 组合地址：城市 + 区 + 乡镇 + 街道
          const parts = [city, district, township, street].filter(Boolean)
          locationName = parts.join('') || address
        }
        
        selectedLocation.value!.name = locationName || `${lat.toFixed(4)}, ${lng.toFixed(4)}`
      } else {
        selectedLocation.value!.name = `${lat.toFixed(4)}, ${lng.toFixed(4)}`
      }
    })
    .catch(() => {
      // 失败则使用坐标
      selectedLocation.value!.name = `${lat.toFixed(4)}, ${lng.toFixed(4)}`
    })
}

// 初始化地图
const initMap = () => {
  if (!mapContainer.value || !window.AMap) {
    console.error('地图容器或AMap未就绪')
    return
  }
  
  // 如果地图已存在，先销毁
  if (mapInstance.value) {
    mapInstance.value.destroy()
    mapInstance.value = null
  }
  
  const center = selectedLocation.value 
    ? [selectedLocation.value.lng, selectedLocation.value.lat]
    : [115.580853, 27.963478] // 默认中心
  
  try {
    // 创建地图实例
    mapInstance.value = new window.AMap.Map(mapContainer.value, {
      zoom: 16,
      center: center,
      viewMode: '2D',
      resizeEnable: true
    })
    
    // 如果已有选中位置，添加标记
    if (selectedLocation.value) {
      addMarker(selectedLocation.value.lng, selectedLocation.value.lat)
    }
    
    // 点击地图事件
    mapInstance.value.on('click', (e: any) => {
      const lng = e.lnglat.getLng()
      const lat = e.lnglat.getLat()
      
      selectedLocation.value = {
        lat,
        lng,
        name: '选择的位置'
      }
      
      // 添加/移动标记
      addMarker(lng, lat)
      
      // 反向地理编码获取地址
      reverseGeocode(lat, lng)
    })
    
    // 强制刷新地图尺寸
    setTimeout(() => {
      mapInstance.value?.resize()
    }, 200)
  } catch (error) {
    console.error('地图初始化失败:', error)
  }
}

// 添加标记
const addMarker = (lng: number, lat: number) => {
  if (!mapInstance.value) return
  
  // 移除旧标记
  if (mapMarker.value) {
    mapInstance.value.remove(mapMarker.value)
  }
  
  // 创建新标记
  mapMarker.value = new window.AMap.Marker({
    position: [lng, lat],
    title: '签到位置'
  })
  
  mapInstance.value.add(mapMarker.value)
}

// 在地图对话框打开时初始化
const onMapDialogOpen = () => {
  // 等待DOM更新和对话框动画完成后初始化地图
  setTimeout(() => {
    initMap()
  }, 300)
}

// 确认开始课堂（带位置信息）
const confirmStartSession = async () => {
  if (!selectedLocation.value) {
    showErrorToast('请选择签到位置')
    return
  }

  try {
    await startSession({
      className: className.value,
      courseName: courseName.value || undefined,
      locationLat: selectedLocation.value.lat,
      locationLng: selectedLocation.value.lng,
      locationName: selectedLocation.value.name,
      checkinRadius: checkinRadius.value
    })
    showSuccessToast('课堂已开始！')
    showMapDialog.value = false
  } catch (err: unknown) {
    showErrorToast(getErrorMessage(err) || '开始课堂失败')
  }
}

const handleEndSession = async () => {
  try {
    await endSession()
    showSuccessToast('课堂已结束！')
    className.value = ''
  } catch (err: unknown) {
    showErrorToast(getErrorMessage(err) || '结束课堂失败')
  }
}

const handleCheckIn = async () => {
  if (!studentCode.value.trim()) {
    showErrorToast('请输入学生代码')
    return
  }

  try {
    await checkIn(studentCode.value.trim())
    showSuccessToast('学生签到成功！')
    studentCode.value = ''
    // 刷新签到记录
    refetchCheckins()
  } catch (err: unknown) {
    showErrorToast(getErrorMessage(err) || '签到失败')
  }
}

// 快速签到
const quickCheckIn = async (studentId: string) => {
  try {
    await checkIn(studentId)
    showSuccessToast('签到成功！')
    refetchCheckins()
  } catch (err: unknown) {
    showErrorToast(getErrorMessage(err) || '签到失败')
  }
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div>
      <h1 class="text-2xl font-bold text-white">
        课堂签到
      </h1>
      <p class="text-white/60">
        管理您的活跃课堂
      </p>
    </div>

    <!-- Session status -->
    <Card
      class="border-white/10 p-6"
      :class="isSessionActive ? 'bg-green-500/5 border-green-500/20' : 'bg-white/[0.02]'"
    >
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-4">
          <div
            class="flex h-12 w-12 items-center justify-center rounded-full"
            :class="isSessionActive ? 'bg-green-500/20 text-green-400' : 'bg-white/10 text-white/60'"
          >
            <Clock class="h-6 w-6" />
          </div>
          <div>
            <h2 class="font-medium text-white">
              {{ isSessionActive ? '课堂进行中' : '暂无活跃课堂' }}
            </h2>
            <p
              v-if="activeSession"
              class="text-sm text-white/60"
            >
              {{ activeSession.class_name }} • 开始于 {{ activeSession.start_time }}
            </p>
            <p
              v-if="activeSession?.location_name"
              class="text-sm text-blue-400 flex items-center gap-1"
            >
              <MapPin class="h-3 w-3" />
              {{ activeSession.location_name }} ({{ activeSession.checkin_radius || 100 }}米范围)
            </p>
            <p
              v-else-if="!isSessionActive"
              class="text-sm text-white/60"
            >
              选择班级开始新课堂
            </p>
          </div>
        </div>
        <div>
          <Button
            v-if="!isSessionActive"
            :loading="isStartingSession"
            @click="handleStartSession"
          >
            <Play class="mr-2 h-4 w-4" />
            开始课堂
          </Button>
          <Button
            v-else
            variant="destructive"
            :loading="isEndingSession"
            @click="handleEndSession"
          >
            <Square class="mr-2 h-4 w-4" />
            结束课堂
          </Button>
        </div>
      </div>
    </Card>

    <!-- Start session form -->
    <Card
      v-if="!isSessionActive"
      class="border-white/10 bg-white/[0.02] p-6"
    >
      <h3 class="font-medium text-white">
        开始新课堂
      </h3>
      <p class="text-sm text-white/60">
        选择课程和班级开始上课
      </p>
      
      <!-- 显示班级占用状态 -->
      <div
        v-if="otherOccupiedClasses.length > 0"
        class="mt-4 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg"
      >
        <p class="text-sm text-yellow-400 flex items-center gap-2">
          <AlertTriangle class="h-4 w-4" />
          以下班级正在被其他教师上课：
        </p>
        <ul class="mt-2 text-sm text-white/70 space-y-1">
          <li
            v-for="cls in otherOccupiedClasses"
            :key="cls.class_name"
          >
            {{ cls.class_name }} - {{ cls.teacher_name || '其他教师' }} 老师
          </li>
        </ul>
      </div>
      
      <div class="mt-4 space-y-4">
        <div class="flex gap-4">
          <Select 
            v-model="courseName" 
            class="flex-1"
            placeholder="请选择课程（可选）"
            :options="courseOptions"
          />
          <Select 
            v-model="className" 
            class="flex-1"
            placeholder="请选择班级"
            :options="availableClassOptions"
          />
        </div>
        <Button
          :loading="isStartingSession"
          :disabled="!className"
          class="w-full"
          @click="handleStartSession"
        >
          <Play class="mr-2 h-4 w-4" />
          开始上课
        </Button>
      </div>
    </Card>

    <!-- Check-in section -->
    <template v-if="isSessionActive">
      <!-- Check-in form -->
      <Card class="border-white/10 bg-white/[0.02] p-6">
        <div class="flex items-center gap-3">
          <div class="flex h-10 w-10 items-center justify-center rounded-full bg-primary/20">
            <CheckCircle class="h-5 w-5 text-primary" />
          </div>
          <div>
            <h3 class="font-medium text-white">
              学生签到
            </h3>
            <p class="text-sm text-white/60">
              输入学生学号进行签到
            </p>
          </div>
        </div>
        <div class="mt-4 flex gap-4">
          <Input
            v-model="studentCode"
            placeholder="请输入学生学号"
            class="flex-1"
            @keyup.enter="handleCheckIn"
          />
          <Button
            :loading="isCheckingIn"
            @click="handleCheckIn"
          >
            <CheckCircle class="mr-2 h-4 w-4" />
            签到
          </Button>
        </div>
      </Card>

      <!-- Stats cards -->
      <div class="grid gap-4 sm:grid-cols-3">
        <Card class="border-white/10 bg-white/[0.02] p-4">
          <div class="flex items-center gap-3">
            <Users class="h-5 w-5 text-white/60" />
            <div>
              <p class="text-xs text-white/50">
                班级人数
              </p>
              <p class="text-xl font-bold text-white">
                {{ checkinStats.total }}
              </p>
            </div>
          </div>
        </Card>
        <Card class="border-white/10 bg-white/[0.02] p-4">
          <div class="flex items-center gap-3">
            <div class="flex h-8 w-8 items-center justify-center rounded-full bg-green-500/20">
              <CheckCircle class="h-4 w-4 text-green-400" />
            </div>
            <div>
              <p class="text-xs text-white/50">
                已签到
              </p>
              <p class="text-xl font-bold text-green-400">
                {{ checkinStats.checkedIn }}
              </p>
            </div>
          </div>
        </Card>
        <Card class="border-white/10 bg-white/[0.02] p-4">
          <div class="flex items-center gap-3">
            <div class="flex h-8 w-8 items-center justify-center rounded-full bg-red-500/20">
              <Clock class="h-4 w-4 text-red-400" />
            </div>
            <div>
              <p class="text-xs text-white/50">
                未签到
              </p>
              <p class="text-xl font-bold text-red-400">
                {{ checkinStats.notCheckedIn }}
              </p>
            </div>
          </div>
        </Card>
      </div>

      <!-- Student list - 列表式布局 -->
      <Card class="border-white/10 bg-white/[0.02]">
        <div class="p-4 border-b border-white/10 flex items-center justify-between">
          <div>
            <h3 class="font-medium text-white flex items-center gap-2">
              <GraduationCap class="h-5 w-5" />
              班级学生列表
              <span class="text-sm text-white/50">({{ checkinStats.total }}人)</span>
            </h3>
          </div>
          <div class="relative w-48">
            <Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/50" />
            <Input
              v-model="searchQuery"
              placeholder="搜索学生..."
              class="pl-10 h-9"
            />
          </div>
        </div>
        
        <div
          v-if="isLoadingStudents"
          class="flex h-48 items-center justify-center"
        >
          <div class="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
        </div>
        
        <!-- 卡片网格布局 -->
        <div
          v-else-if="filteredStudents.length > 0"
          class="p-4"
        >
          <!-- 统计标签 -->
          <div class="flex items-center gap-4 mb-4">
            <div class="flex items-center gap-2">
              <div class="flex h-2 w-2 rounded-full bg-green-400" />
              <span class="text-sm text-white/60">已签到 {{ checkedInStudents.length }}人</span>
            </div>
            <div class="flex items-center gap-2">
              <div class="flex h-2 w-2 rounded-full bg-red-400" />
              <span class="text-sm text-white/60">未签到 {{ notCheckedInStudents.length }}人</span>
            </div>
          </div>
          
          <!-- 学生卡片网格 -->
          <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
            <div
              v-for="student in filteredStudents"
              :key="student.id"
              class="relative rounded-lg border p-3 transition-all cursor-pointer group"
              :class="[
                student.checkedIn 
                  ? 'bg-green-500/10 border-green-500/30 hover:border-green-500/50' 
                  : 'bg-red-500/10 border-red-500/30 hover:border-red-500/50 hover:bg-red-500/15'
              ]"
              @click="!student.checkedIn && quickCheckIn(student.student_id)"
            >
              <!-- 签到状态图标 -->
              <div 
                class="absolute top-2 right-2 flex h-5 w-5 items-center justify-center rounded-full"
                :class="student.checkedIn ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'"
              >
                <CheckCircle v-if="student.checkedIn" class="h-3 w-3" />
                <span v-else class="text-xs">!</span>
              </div>
              
              <!-- 学生信息 -->
              <div class="flex flex-col items-center text-center">
                <div 
                  class="flex h-10 w-10 items-center justify-center rounded-full text-sm font-medium mb-2"
                  :class="student.checkedIn 
                    ? 'bg-green-500/20 text-green-400' 
                    : 'bg-red-500/20 text-red-400 group-hover:bg-red-500/30'"
                >
                  {{ student.name.charAt(0) }}
                </div>
                <p 
                  class="text-sm font-medium truncate w-full"
                  :class="student.checkedIn ? 'text-green-400' : 'text-red-400'"
                >
                  {{ student.name }}
                </p>
                <p class="text-xs text-white/40 mt-0.5">{{ student.student_id }}</p>
                <p v-if="student.checkedIn && student.checkinTime" class="text-xs text-white/50 mt-1">
                  {{ formatTime(student.checkinTime) }}
                </p>
                <p v-else-if="!student.checkedIn" class="text-xs text-red-400/70 mt-1">
                  点击签到
                </p>
              </div>
            </div>
          </div>
        </div>
        
        <div
          v-else
          class="flex h-48 flex-col items-center justify-center text-white/60"
        >
          <GraduationCap class="mb-4 h-12 w-12 opacity-50" />
          <p>暂无学生数据</p>
        </div>
      </Card>
    </template>

    <!-- 地图选点对话框 -->
    <Dialog
      v-model:open="showMapDialog"
      title="选择签到位置"
      @open="onMapDialogOpen"
    >
      <div class="space-y-4">
        <!-- 位置显示 -->
        <div
          v-if="selectedLocation"
          class="rounded-lg border border-blue-500/20 bg-blue-500/5 p-3"
        >
          <div class="flex items-center gap-2 text-sm text-blue-400">
            <MapPin class="h-4 w-4" />
            <span>{{ selectedLocation.name }}</span>
          </div>
          <div class="mt-1 text-xs text-white/40">
            坐标: {{ selectedLocation.lat.toFixed(6) }}, {{ selectedLocation.lng.toFixed(6) }}
          </div>
        </div>

        <div v-else-if="isLoadingLocation" class="text-center py-8 text-white/60">
          <Loader2 class="mx-auto h-8 w-8 animate-spin mb-2" />
          <p>正在获取位置...</p>
        </div>

        <div v-else class="text-center py-4 text-white/60">
          <MapPin class="mx-auto h-6 w-6 mb-1 opacity-50" />
          <p class="text-sm">点击地图选择签到位置</p>
        </div>

        <!-- 地图容器 -->
        <div class="relative">
          <div 
            ref="mapContainer"
            class="w-full rounded-lg border border-white/20"
            style="height: 300px; background: linear-gradient(135deg, #1e3a5f 0%, #2d3748 100%);"
          />
          <!-- 地图加载提示 -->
          <div 
            v-if="!mapInstance && !selectedLocation"
            class="absolute inset-0 flex flex-col items-center justify-center text-white/60 pointer-events-none"
          >
            <MapPin class="h-8 w-8 mb-2" />
            <p class="text-sm">点击地图选择位置</p>
          </div>
        </div>

        <!-- 手动输入（备选） -->
        <div class="rounded-lg border border-white/10 bg-white/5 p-3">
          <label class="block text-xs text-white/40 mb-2">手动调整（可选）</label>
          <div class="grid grid-cols-2 gap-2">
            <Input
              v-model="selectedLocation!.lat"
              type="number"
              step="0.000001"
              placeholder="纬度"
              size="sm"
            />
            <Input
              v-model="selectedLocation!.lng"
              type="number"
              step="0.000001"
              placeholder="经度"
              size="sm"
            />
          </div>
          <Input
            v-model="selectedLocation!.name"
            class="mt-2"
            placeholder="位置名称（如：机房312）"
            size="sm"
          />
        </div>

        <!-- 签到半径 -->
        <div>
          <label class="block text-sm text-white/60 mb-2">
            签到半径: {{ checkinRadius }} 米
          </label>
          <input
            v-model="checkinRadius"
            type="range"
            min="50"
            max="500"
            step="10"
            class="w-full"
          />
          <div class="flex justify-between text-xs text-white/40 mt-1">
            <span>50米</span>
            <span>500米</span>
          </div>
        </div>

        <!-- 按钮 -->
        <div class="flex gap-2 pt-2">
          <Button
            variant="outline"
            class="flex-1"
            @click="showMapDialog = false"
          >
            取消
          </Button>
          <Button
            class="flex-1"
            :loading="isStartingSession"
            :disabled="!selectedLocation"
            @click="confirmStartSession"
          >
            开始课堂
          </Button>
        </div>
      </div>
    </Dialog>

    <!-- Toast -->
    <Toast
      v-model:show="show"
      :message="toastMessage"
      :variant="toastVariant"
    />
  </div>
</template>
