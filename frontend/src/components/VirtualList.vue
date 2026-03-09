<template>
  <div ref="containerRef" class="virtual-list-container" @scroll="handleScroll">
    <div class="virtual-list-phantom" :style="{ height: `${totalHeight}px` }"></div>
    <div class="virtual-list-content" :style="{ transform: `translateY(${offsetY}px)` }">
      <div
        v-for="item in visibleData"
        :key="item[keyProp]"
        class="virtual-list-item"
        :style="{ height: `${itemHeight}px` }"
      >
        <slot :item="item" :index="item._index"></slot>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'

const props = defineProps({
  data: {
    type: Array,
    required: true
  },
  itemHeight: {
    type: Number,
    default: 60
  },
  keyProp: {
    type: String,
    default: 'id'
  },
  buffer: {
    type: Number,
    default: 5
  }
})

const containerRef = ref(null)
const scrollTop = ref(0)
const containerHeight = ref(0)

// 计算总高度
const totalHeight = computed(() => props.data.length * props.itemHeight)

// 计算可视区域能显示的条目数
const visibleCount = computed(() => {
  return Math.ceil(containerHeight.value / props.itemHeight) + props.buffer * 2
})

// 计算起始索引
const startIndex = computed(() => {
  const start = Math.floor(scrollTop.value / props.itemHeight) - props.buffer
  return Math.max(0, start)
})

// 计算结束索引
const endIndex = computed(() => {
  const end = startIndex.value + visibleCount.value
  return Math.min(props.data.length, end)
})

// 计算可视数据
const visibleData = computed(() => {
  return props.data.slice(startIndex.value, endIndex.value).map((item, index) => ({
    ...item,
    _index: startIndex.value + index
  }))
})

// 计算偏移量
const offsetY = computed(() => startIndex.value * props.itemHeight)

// 处理滚动
const handleScroll = () => {
  if (containerRef.value) {
    scrollTop.value = containerRef.value.scrollTop
  }
}

// 初始化容器高度
const initContainerHeight = () => {
  if (containerRef.value) {
    containerHeight.value = containerRef.value.clientHeight
  }
}

// Resize 监听
let resizeObserver = null

onMounted(() => {
  initContainerHeight()
  
  // 使用 ResizeObserver 监听容器高度变化
  if (window.ResizeObserver) {
    resizeObserver = new ResizeObserver(() => {
      initContainerHeight()
    })
    resizeObserver.observe(containerRef.value)
  }
})

onUnmounted(() => {
  if (resizeObserver) {
    resizeObserver.disconnect()
  }
})

// 暴露方法给父组件
const scrollTo = (index) => {
  if (containerRef.value) {
    containerRef.value.scrollTop = index * props.itemHeight
  }
}

const scrollToTop = () => {
  scrollTo(0)
}

defineExpose({
  scrollTo,
  scrollToTop
})
</script>

<style scoped>
.virtual-list-container {
  position: relative;
  overflow-y: auto;
  height: 100%;
}

.virtual-list-phantom {
  position: absolute;
  left: 0;
  top: 0;
  right: 0;
  z-index: -1;
}

.virtual-list-content {
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
}

.virtual-list-item {
  box-sizing: border-box;
}
</style>
