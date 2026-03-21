<template>
  <!-- 这个组件不需要渲染任何内容 -->
</template>

<script setup>
import { useMessage, useDialog, useNotification, useLoadingBar } from 'naive-ui'

// 设置全局消息实例（供 axios 拦截器使用）
const message = useMessage()
const dialog = useDialog()
const notification = useNotification()
const loadingBar = useLoadingBar()

window.$message = message
window.$dialog = dialog
window.$notification = notification
window.$loadingBar = loadingBar
</script>
