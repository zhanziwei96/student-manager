<script setup lang="ts">
/**
 * 位置选择器组件 - 地图选点功能
 *
 * 从 ClassSession.vue 拆分出来的地图选点功能
 */
import { ref, computed, watch } from 'vue'
import { Button, Input } from '@/components/ui'
import { MapPin, Loader2 } from 'lucide-vue-next'

interface Location {
  lat: number
  lng: number
  name: string
}

const props = defineProps<{
  modelValue: Location | null
  radius?: number
  loading?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [location: Location | null]
  'update:radius': [radius: number]
  'confirm': []
  'cancel': []
}>()

// 本地状态
const mapContainer = ref<HTMLDivElement | null>(null)
const mapInstance = ref<AMapMap | null>(null)
const mapMarker = ref<AMapMarker | null>(null)
const mapLoadError = ref(false)
const isLoadingLocation = ref(false)

// 高德地图Key
const AMAP_KEY = import.meta.env.VITE_AMAP_KEY || ''

// 内部位置状态（用于编辑）
const internalLocation = computed<Location | null>({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

// 签到半径
const checkinRadius = computed({
  get: () => props.radius ?? 100,
  set: (val) => emit('update:radius', val)
})

// 检查高德地图是否加载完成
const checkAMapLoaded = (): Promise<boolean> => {
  return new Promise((resolve) => {
    let attempts = 0
    const maxAttempts = 50 // 最多等待5秒

    const check = () => {
      attempts++
      if (window.AMap && window.AMap.Map) {
        resolve(true)
      } else if (attempts >= maxAttempts) {
        resolve(false)
      } else {
        setTimeout(check, 100)
      }
    }

    check()
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

  const center = internalLocation.value
    ? [internalLocation.value.lng, internalLocation.value.lat]
    : [116.397428, 39.90923] // 默认北京中心

  try {
    mapInstance.value = new window.AMap.Map(mapContainer.value, {
      zoom: 16,
      center: center as [number, number],
      viewMode: '2D',
      resizeEnable: true
    })

    // 如果已有选中位置，添加标记
    if (internalLocation.value) {
      addMarker(internalLocation.value.lng, internalLocation.value.lat)
    }

    // 点击地图事件
    mapInstance.value.on('click', (e: AMapMapClickEvent) => {
      const lng = e.lnglat.getLng()
      const lat = e.lnglat.getLat()

      internalLocation.value = {
        lat,
        lng,
        name: '选择的位置'
      }

      addMarker(lng, lat)
      reverseGeocode(lat, lng)
    })

    // 强制刷新地图尺寸
    setTimeout(() => {
      mapInstance.value?.resize()
    }, 200)
  } catch (error) {
    console.error('地图初始化失败:', error)
    mapLoadError.value = true
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

// 反向地理编码
const reverseGeocode = (lat: number, lng: number) => {
  if (!AMAP_KEY) {
    if (internalLocation.value) {
      internalLocation.value.name = `${lat.toFixed(4)}, ${lng.toFixed(4)}`
    }
    return
  }

  fetch(`https://restapi.amap.com/v3/geocode/regeo?key=${AMAP_KEY}&location=${lng},${lat}&extensions=all&radius=100`)
    .then(res => res.json())
    .then(data => {
      if (data.status === '1' && data.regeocode && internalLocation.value) {
        const address = data.regeocode.formatted_address
        const poi = data.regeocode.pois?.[0]?.name
        const street = data.regeocode.addressComponent?.street || ''
        const township = data.regeocode.addressComponent?.township || ''
        const district = data.regeocode.addressComponent?.district || ''
        const city = data.regeocode.addressComponent?.city || ''

        let locationName = poi
        if (!locationName) {
          const parts = [city, district, township, street].filter(Boolean)
          locationName = parts.join('') || address
        }

        internalLocation.value.name = locationName || `${lat.toFixed(4)}, ${lng.toFixed(4)}`
      } else if (internalLocation.value) {
        internalLocation.value.name = `${lat.toFixed(4)}, ${lng.toFixed(4)}`
      }
    })
    .catch(() => {
      if (internalLocation.value) {
        internalLocation.value.name = `${lat.toFixed(4)}, ${lng.toFixed(4)}`
      }
    })
}

// 获取当前位置
const getCurrentPosition = () => {
  if (!navigator.geolocation) {
    // 使用默认位置
    internalLocation.value = {
      lat: 39.90923,
      lng: 116.397428,
      name: '默认位置'
    }
    return
  }

  isLoadingLocation.value = true
  navigator.geolocation.getCurrentPosition(
    (position) => {
      internalLocation.value = {
        lat: position.coords.latitude,
        lng: position.coords.longitude,
        name: '当前位置'
      }
      reverseGeocode(position.coords.latitude, position.coords.longitude)
      isLoadingLocation.value = false

      // 更新地图中心
      if (mapInstance.value && internalLocation.value) {
        mapInstance.value.setCenter([internalLocation.value.lng, internalLocation.value.lat])
        addMarker(internalLocation.value.lng, internalLocation.value.lat)
      }
    },
    () => {
      // 定位失败，使用默认位置
      internalLocation.value = {
        lat: 39.90923,
        lng: 116.397428,
        name: '默认位置'
      }
      isLoadingLocation.value = false
    },
    { timeout: 5000 }
  )
}

// 初始化
const initialize = async () => {
  mapLoadError.value = false

  // 等待高德地图脚本加载
  const loaded = await checkAMapLoaded()
  if (!loaded) {
    console.error('高德地图脚本加载超时')
    mapLoadError.value = true
    return
  }

  // 等待DOM更新和对话框动画完成后初始化地图
  setTimeout(() => {
    initMap()
  }, 300)
}

// 监听显示状态
watch(() => props.modelValue, (newVal) => {
  if (newVal && mapInstance.value) {
    mapInstance.value.setCenter([newVal.lng, newVal.lat])
    addMarker(newVal.lng, newVal.lat)
  }
})

// 暴露方法给父组件
defineExpose({
  initialize,
  getCurrentPosition
})
</script>

<template>
  <div class="space-y-4">
    <!-- 位置显示 -->
    <div
      v-if="internalLocation"
      class="rounded-lg border border-blue-500/20 bg-blue-500/5 p-3"
    >
      <div class="flex items-center gap-2 text-sm text-blue-400">
        <MapPin class="h-4 w-4" />
        <span>{{ internalLocation.name }}</span>
      </div>
      <div class="mt-1 text-xs text-white/40">
        坐标: {{ internalLocation.lat.toFixed(6) }}, {{ internalLocation.lng.toFixed(6) }}
      </div>
    </div>

    <div
      v-else-if="isLoadingLocation"
      class="text-center py-8 text-white/60"
    >
      <Loader2 class="mx-auto h-8 w-8 animate-spin mb-2" />
      <p>正在获取位置...</p>
    </div>

    <div
      v-else
      class="text-center py-4 text-white/60"
    >
      <MapPin class="mx-auto h-6 w-6 mb-1 opacity-50" />
      <p class="text-sm">
        点击地图选择签到位置
      </p>
    </div>

    <!-- 地图容器 -->
    <div class="relative">
      <div
        v-if="!mapLoadError"
        ref="mapContainer"
        class="w-full rounded-lg border border-white/20"
        style="height: 300px; background: linear-gradient(135deg, #1e3a5f 0%, #2d3748 100%);"
      />
      <!-- 地图加载提示 -->
      <div
        v-if="!mapInstance && !internalLocation && !mapLoadError"
        class="absolute inset-0 flex flex-col items-center justify-center text-white/60 pointer-events-none"
      >
        <MapPin class="h-8 w-8 mb-2" />
        <p class="text-sm">
          点击地图选择位置
        </p>
      </div>
    </div>

    <!-- 手动输入（备选） -->
    <div class="rounded-lg border border-white/10 bg-white/5 p-3">
      <label class="block text-xs text-white/40 mb-2">手动调整（可选）</label>
      <div class="grid grid-cols-2 gap-2">
        <Input
          v-model="internalLocation!.lat"
          type="number"
          step="0.000001"
          placeholder="纬度"
          size="sm"
        />
        <Input
          v-model="internalLocation!.lng"
          type="number"
          step="0.000001"
          placeholder="经度"
          size="sm"
        />
      </div>
      <Input
        v-model="internalLocation!.name"
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
      >
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
        @click="$emit('cancel')"
      >
        取消
      </Button>
      <Button
        class="flex-1"
        :loading="loading"
        :disabled="!internalLocation"
        @click="$emit('confirm')"
      >
        确认位置
      </Button>
    </div>
  </div>
</template>