<template>
  <div class="login-container">
    <!-- 动态背景粒子 -->
    <div class="particles">
      <div v-for="n in 20" :key="n" class="particle" :style="getParticleStyle(n)"></div>
    </div>
    
    <!-- 渐变光晕 -->
    <div class="glow glow-1"></div>
    <div class="glow glow-2"></div>
    <div class="glow glow-3"></div>

    <!-- 返回按钮 -->
    <button class="back-btn" @click="$router.push('/')">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M19 12H5M12 19l-7-7 7-7"/>
      </svg>
      <span>返回首页</span>
    </button>

    <!-- 主卡片 -->
    <div class="login-card">
      <!-- 左侧品牌区 -->
      <div class="brand-section">
        <div class="brand-content">
          <div class="logo">
            <div class="logo-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                <path d="M2 17l10 5 10-5"/>
                <path d="M2 12l10 5 10-5"/>
              </svg>
            </div>
            <div class="logo-text">
              <h1>ClassHub</h1>
              <p>智能班级管理系统</p>
            </div>
          </div>
          
          <div class="features">
            <div class="feature" v-for="(item, i) in features" :key="i">
              <div class="feature-dot"></div>
              <span>{{ item }}</span>
            </div>
          </div>
        </div>
        
        <!-- 装饰圆环 -->
        <div class="orbit">
          <div class="orbit-ring ring-1"></div>
          <div class="orbit-ring ring-2"></div>
          <div class="orbit-ring ring-3"></div>
        </div>
      </div>

      <!-- 右侧表单区 -->
      <div class="form-section">
        <div class="form-header">
          <h2>欢迎回来</h2>
          <p>登录您的管理账户</p>
        </div>

        <form @submit.prevent="handleLogin" class="form-body">
          <div class="input-group" :class="{ focused: focused === 'username' }">
            <label>用户名</label>
            <div class="input-wrapper">
              <svg class="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                <circle cx="12" cy="7" r="4"/>
              </svg>
              <input
                v-model="form.username"
                type="text"
                placeholder="请输入用户名"
                @focus="focused = 'username'"
                @blur="focused = null"
                ref="usernameInput"
              />
            </div>
          </div>

          <div class="input-group" :class="{ focused: focused === 'password' }">
            <label>密码</label>
            <div class="input-wrapper">
              <svg class="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
              </svg>
              <input
                v-model="form.password"
                :type="showPassword ? 'text' : 'password'"
                placeholder="请输入密码"
                @focus="focused = 'password'"
                @blur="focused = null"
              />
              <button type="button" class="toggle-btn" @click="showPassword = !showPassword">
                <svg v-if="!showPassword" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                  <circle cx="12" cy="12" r="3"/>
                </svg>
                <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
                  <line x1="1" y1="1" x2="23" y2="23"/>
                </svg>
              </button>
            </div>
          </div>

          <div class="form-options">
            <label class="remember">
              <input type="checkbox" v-model="rememberMe" />
              <span class="checkmark"></span>
              <span class="label-text">记住我</span>
            </label>
          </div>

          <button type="submit" class="submit-btn" :disabled="loading">
            <span class="btn-text" v-if="!loading">登录</span>
            <span class="btn-loader" v-else></span>
            <svg class="btn-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M5 12h14M12 5l7 7-7 7"/>
            </svg>
          </button>
        </form>

        <div class="form-footer">
          <p>默认账号 <span class="highlight">admin / admin123</span></p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { login } from '@/api'

const router = useRouter()
const userStore = useUserStore()
const message = useMessage()

const showPassword = ref(false)
const rememberMe = ref(false)
const loading = ref(false)
const focused = ref(null)
const usernameInput = ref(null)

const form = reactive({
  username: '',
  password: ''
})

const features = [
  '学生签到管理',
  '实时分数统计', 
  '班级数据分析',
  '智能排名系统'
]

const getParticleStyle = (n) => {
  const size = Math.random() * 4 + 2
  const left = Math.random() * 100
  const delay = Math.random() * 20
  const duration = Math.random() * 20 + 10
  return {
    width: `${size}px`,
    height: `${size}px`,
    left: `${left}%`,
    animationDelay: `${delay}s`,
    animationDuration: `${duration}s`
  }
}

const handleLogin = async () => {
  if (loading.value) return
  
  if (!form.username.trim()) {
    return message.warning('请输入用户名')
  }
  if (!form.password) {
    return message.warning('请输入密码')
  }

  loading.value = true
  try {
    const res = await login({
      username: form.username.trim(),
      password: form.password
    })
    
    if (res.success) {
      userStore.setUser(res.user.id, res.user.username, res.user.name)
      message.success('登录成功')
      router.push('/admin')
    } else {
      message.error(res.message || '登录失败')
    }
  } catch (error) {
    message.error('网络错误')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  usernameInput.value?.focus()
})
</script>

<style scoped>
/* 深色主题配色 */
:root {
  --primary: #6366f1;
  --primary-light: #818cf8;
  --primary-dark: #4f46e5;
  --accent: #06b6d4;
  --bg-dark: #0a0a0f;
  --bg-card: #13131f;
  --bg-input: #1a1a2e;
  --text-primary: #ffffff;
  --text-secondary: #94a3b8;
  --text-muted: #64748b;
  --border: rgba(255, 255, 255, 0.08);
}

.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-dark);
  position: relative;
  overflow: hidden;
  padding: 20px;
}

/* 粒子背景 */
.particles {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
}

.particle {
  position: absolute;
  background: linear-gradient(135deg, var(--primary), var(--accent));
  border-radius: 50%;
  opacity: 0.3;
  animation: float-up linear infinite;
  filter: blur(1px);
}

@keyframes float-up {
  0% {
    transform: translateY(100vh) scale(0);
    opacity: 0;
  }
  10% {
    opacity: 0.3;
  }
  90% {
    opacity: 0.3;
  }
  100% {
    transform: translateY(-100px) scale(1);
    opacity: 0;
  }
}

/* 渐变光晕 */
.glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.4;
  animation: pulse-glow 8s ease-in-out infinite;
}

.glow-1 {
  width: 600px;
  height: 600px;
  background: radial-gradient(circle, var(--primary) 0%, transparent 70%);
  top: -200px;
  left: -200px;
  animation-delay: 0s;
}

.glow-2 {
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, var(--accent) 0%, transparent 70%);
  bottom: -150px;
  right: -150px;
  animation-delay: -2s;
}

.glow-3 {
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, #8b5cf6 0%, transparent 70%);
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation-delay: -4s;
  opacity: 0.2;
}

@keyframes pulse-glow {
  0%, 100% { transform: scale(1); opacity: 0.4; }
  50% { transform: scale(1.1); opacity: 0.6; }
}

/* 返回按钮 */
.back-btn {
  position: absolute;
  top: 32px;
  left: 32px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border);
  border-radius: 12px;
  color: var(--text-secondary);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
  z-index: 10;
}

.back-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.15);
  color: var(--text-primary);
  transform: translateX(-4px);
}

.back-btn svg {
  width: 18px;
  height: 18px;
}

/* 主卡片 */
.login-card {
  display: grid;
  grid-template-columns: 1fr 1.2fr;
  width: 100%;
  max-width: 1000px;
  min-height: 580px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 24px;
  overflow: hidden;
  position: relative;
  z-index: 1;
  box-shadow: 
    0 0 0 1px rgba(99, 102, 241, 0.1),
    0 20px 60px rgba(0, 0, 0, 0.5);
}

/* 品牌区域 */
.brand-section {
  position: relative;
  padding: 48px;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(6, 182, 212, 0.05) 100%);
  display: flex;
  flex-direction: column;
  justify-content: center;
  overflow: hidden;
}

.brand-content {
  position: relative;
  z-index: 2;
}

.logo {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 48px;
}

.logo-icon {
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--primary) 0%, var(--accent) 100%);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(99, 102, 241, 0.4);
}

.logo-icon svg {
  width: 28px;
  height: 28px;
  color: white;
}

.logo-text h1 {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.5px;
  margin-bottom: 4px;
}

.logo-text p {
  font-size: 14px;
  color: var(--text-secondary);
}

/* 特性列表 */
.features {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.feature {
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--text-secondary);
  font-size: 15px;
}

.feature-dot {
  width: 8px;
  height: 8px;
  background: linear-gradient(135deg, var(--primary), var(--accent));
  border-radius: 50%;
  box-shadow: 0 0 8px rgba(99, 102, 241, 0.6);
}

/* 轨道装饰 */
.orbit {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.orbit-ring {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  border: 1px solid rgba(255, 255, 255, 0.03);
  border-radius: 50%;
}

.ring-1 {
  width: 300px;
  height: 300px;
  animation: rotate 20s linear infinite;
}

.ring-2 {
  width: 400px;
  height: 400px;
  animation: rotate 30s linear infinite reverse;
}

.ring-3 {
  width: 500px;
  height: 500px;
  animation: rotate 40s linear infinite;
}

@keyframes rotate {
  from { transform: translate(-50%, -50%) rotate(0deg); }
  to { transform: translate(-50%, -50%) rotate(360deg); }
}

/* 表单区域 */
.form-section {
  padding: 48px 56px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.form-header {
  margin-bottom: 40px;
}

.form-header h2 {
  font-size: 32px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 8px;
  letter-spacing: -0.5px;
}

.form-header p {
  font-size: 15px;
  color: var(--text-secondary);
}

/* 表单 */
.form-body {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.input-group label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.input-icon {
  position: absolute;
  left: 16px;
  width: 20px;
  height: 20px;
  color: var(--text-muted);
  transition: color 0.3s ease;
  z-index: 2;
}

.input-group.focused .input-icon {
  color: var(--primary-light);
}

.input-wrapper input {
  width: 100%;
  padding: 14px 16px 14px 48px;
  background: var(--bg-input);
  border: 1px solid var(--border);
  border-radius: 12px;
  color: var(--text-primary);
  font-size: 15px;
  transition: all 0.3s ease;
}

.input-wrapper input:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15);
}

.input-wrapper input::placeholder {
  color: var(--text-muted);
}

.toggle-btn {
  position: absolute;
  right: 12px;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 8px;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.3s ease;
}

.toggle-btn:hover {
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-secondary);
}

.toggle-btn svg {
  width: 18px;
  height: 18px;
}

/* 记住我 */
.form-options {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.remember {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
}

.remember input {
  display: none;
}

.checkmark {
  width: 20px;
  height: 20px;
  border: 2px solid var(--border);
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.remember input:checked + .checkmark {
  background: linear-gradient(135deg, var(--primary), var(--accent));
  border-color: transparent;
}

.remember input:checked + .checkmark::after {
  content: '';
  width: 5px;
  height: 9px;
  border: solid white;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
  margin-bottom: 2px;
}

.label-text {
  font-size: 14px;
  color: var(--text-secondary);
}

/* 提交按钮 */
.submit-btn {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 16px 32px;
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
  border: none;
  border-radius: 12px;
  color: white;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  overflow: hidden;
  transition: all 0.3s ease;
  margin-top: 8px;
}

.submit-btn::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, var(--primary-light) 0%, var(--primary) 100%);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.submit-btn:hover::before {
  opacity: 1;
}

.submit-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(99, 102, 241, 0.4);
}

.submit-btn:disabled {
  cursor: not-allowed;
  opacity: 0.7;
}

.btn-text, .btn-arrow {
  position: relative;
  z-index: 1;
}

.btn-arrow {
  width: 18px;
  height: 18px;
  transition: transform 0.3s ease;
}

.submit-btn:hover .btn-arrow {
  transform: translateX(4px);
}

.btn-loader {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 页脚 */
.form-footer {
  margin-top: 32px;
  text-align: center;
}

.form-footer p {
  font-size: 13px;
  color: var(--text-muted);
}

.highlight {
  color: var(--accent);
  font-weight: 500;
  font-family: monospace;
}

/* 响应式 */
@media (max-width: 900px) {
  .login-card {
    grid-template-columns: 1fr;
    max-width: 480px;
  }
  
  .brand-section {
    display: none;
  }
  
  .form-section {
    padding: 40px 32px;
  }
}

@media (max-width: 480px) {
  .login-container {
    padding: 16px;
  }
  
  .back-btn {
    top: 16px;
    left: 16px;
  }
  
  .form-section {
    padding: 32px 24px;
  }
  
  .form-header h2 {
    font-size: 24px;
  }
}
</style>
