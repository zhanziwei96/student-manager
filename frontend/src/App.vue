<template>
  <n-config-provider :theme="darkTheme" :theme-overrides="themeOverrides">
    <n-message-provider>
      <n-dialog-provider>
        <n-notification-provider>
          <n-loading-bar-provider>
            <router-view v-slot="{ Component }">
              <transition name="fade" mode="out-in">
                <component :is="Component" />
              </transition>
            </router-view>
          </n-loading-bar-provider>
        </n-notification-provider>
      </n-dialog-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup>
import { darkTheme } from 'naive-ui'

// 主题覆盖配置
const themeOverrides = {
  common: {
    primaryColor: '#6366f1',
    primaryColorHover: '#818cf8',
    primaryColorPressed: '#4f46e5',
    primaryColorSuppl: '#6366f1',
    infoColor: '#6366f1',
    successColor: '#10b981',
    warningColor: '#f59e0b',
    errorColor: '#ef4444',
    textColorBase: '#ffffff',
    textColor1: '#ffffff',
    textColor2: 'rgba(255, 255, 255, 0.8)',
    textColor3: '#94a3b8',
    bodyColor: '#0a0a0f',
    cardColor: 'rgba(19, 19, 31, 0.8)',
    modalColor: '#1a1a25',
    popoverColor: '#1a1a25',
    borderColor: 'rgba(255, 255, 255, 0.08)',
    dividerColor: 'rgba(255, 255, 255, 0.08)',
    inputColor: 'rgba(255, 255, 255, 0.05)',
    inputColorDisabled: 'rgba(255, 255, 255, 0.03)',
    buttonColor2: 'rgba(255, 255, 255, 0.08)',
    buttonColor2Hover: 'rgba(255, 255, 255, 0.12)',
    buttonColor2Pressed: 'rgba(255, 255, 255, 0.05)',
  },
  Card: {
    color: 'rgba(19, 19, 31, 0.8)',
    borderColor: 'rgba(255, 255, 255, 0.08)',
  },
  Modal: {
    color: '#1a1a25',
    borderColor: 'rgba(255, 255, 255, 0.08)',
  },
  Input: {
    color: 'rgba(255, 255, 255, 0.05)',
    colorFocus: 'rgba(255, 255, 255, 0.08)',
    borderColor: 'rgba(255, 255, 255, 0.08)',
    borderHover: 'rgba(255, 255, 255, 0.15)',
    borderFocus: '#6366f1',
    placeholderColor: '#64748b',
  },
  Button: {
    color: 'rgba(255, 255, 255, 0.08)',
    colorHover: 'rgba(255, 255, 255, 0.12)',
    colorPressed: 'rgba(255, 255, 255, 0.05)',
    colorDisabled: 'rgba(255, 255, 255, 0.05)',
    textColor: 'rgba(255, 255, 255, 0.9)',
    textColorDisabled: 'rgba(255, 255, 255, 0.4)',
  },
  Select: {
    color: 'rgba(255, 255, 255, 0.05)',
    colorActive: 'rgba(99, 102, 241, 0.1)',
    colorDisabled: 'rgba(255, 255, 255, 0.03)',
    borderColor: 'rgba(255, 255, 255, 0.08)',
    borderHover: 'rgba(255, 255, 255, 0.15)',
    borderActive: '#6366f1',
  },
  Tag: {
    color: 'rgba(99, 102, 241, 0.15)',
    colorBordered: 'rgba(99, 102, 241, 0.15)',
    textColor: '#818cf8',
    textColorSuccess: '#34d399',
    textColorWarning: '#fbbf24',
    textColorError: '#f87171',
    textColorInfo: '#818cf8',
  },
  Table: {
    thColor: 'rgba(255, 255, 255, 0.03)',
    tdColor: 'transparent',
    borderColor: 'rgba(255, 255, 255, 0.05)',
  },
  Collapse: {
    dividerColor: 'rgba(255, 255, 255, 0.08)',
    titleTextColor: '#ffffff',
  },
  Alert: {
    color: 'rgba(19, 19, 31, 0.8)',
    border: '1px solid rgba(255, 255, 255, 0.08)',
  },
}
</script>

<style>
/* 页面过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.fade-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* 全局基础样式 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background: #0a0a0f;
  color: #ffffff;
}

/* 滚动条样式 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.03);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.15);
}
</style>
