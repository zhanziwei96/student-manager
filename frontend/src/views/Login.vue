<template>
  <div class="login-page">
    <!-- 动态背景 -->
    <div class="bg-animation">
      <div class="gradient-mesh"></div>
      <div class="floating-shapes">
        <div v-for="n in 6" :key="n" class="shape" :class="`shape-${n}`"></div>
      </div>
    </div>

    <!-- 返回按钮 -->
    <button class="back-btn" @click="$router.push('/')">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M19 12H5M12 19l-7-7 7-7"/>
      </svg>
      <span>返回首页</span>
    </button>

    <!-- 登录卡片 -->
    <div class="login-container">
      <div class="login-card">
        <!-- 左侧装饰 -->
        <div class="card-visual">
          <div class="visual-content">
            <div class="logo-badge">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                <path d="M2 17l10 5 10-5"/>
                <path d="M2 12l10 5 10-5"/>
              </svg>
            </div>
            <h2>ClassHub</h2>
            <p>智能班级管理平台</p>
            
            <div class="feature-list">
              <div class="feature-item" v-for="(item, i) in features" :key="i">
                <div class="feature-check">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                </div>
                <span>{{ item }}</span>
              </div>
            </div>
          </div>
          
          <div class="visual-glow"></div>
        </div>

        <!-- 右侧表单 -->
        <div class="card-form">
          <div class="form-header">
            <h1>欢迎回来</h1>
            <p>请输入您的账号信息</p>
          </div>

          <form @submit.prevent="handleLogin" class="form-body">
            <div class="input-group" :class="{ 'focused': focused === 'username', 'filled': form.username }">
              <label class="input-label">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                  <circle cx="12" cy="7" r="4"/>
                </svg>
                <span>用户名</span>
              </label>
              <input
                v-model="form.username"
                type="text"
                placeholder="请输入用户名"
                @focus="focused = 'username'"
                @blur="focused = null"
                ref="usernameInput"
              />
            </div>

            <div class="input-group" :class="{ 'focused': focused === 'password', 'filled': form.password }">
              <label class="input-label">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                  <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                </svg>
                <span>密码</span>
              </label>
              <div class="password-wrapper">
                <input
                  v-model="form.password"
                  :type="showPassword ? 'text' : 'password'"
                  placeholder="请输入密码"
                  @focus="focused = 'password'"
                  @blur="focused = null"
                />
                <button type="button" class="toggle-password" @click="showPassword = !showPassword">
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
              <label class="remember-me">
                <input type="checkbox" v-model="rememberMe" />
                <span class="checkmark"></span>
                <span>记住我</span>
              </label>
            </div>

            <button type="submit" class="submit-btn" :class="{ 'loading': loading }" :disabled="loading">
              <span class="btn-text">{{ loading ? '登录中...' : '登录' }}</span>
              <span class="btn-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M5 12h14M12 5l7 7-7 7"/>
                </svg>
              </span>
              <div class="btn-loader"></div>
            </button>
          </form>

          <div class="form-footer">
            <p>默认账号：<span class="highlight">admin / admin123</span></p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import Cookies from 'js-cookie'
import { login } from '../api'

const router = useRouter()
const focused = ref(null)
const showPassword = ref(false)
const rememberMe = ref(false)
const loading = ref(false)
const usernameInput = ref(null)

const form = reactive({
  username: '',
  password: ''
})

const features = [
  '学生签到管理',
  '实时分数统计',
  '班级数据分析',
  '操作日志记录'
]

const handleLogin = async () => {
  // 防止重复提交
  if (loading.value) return
  if (!form.username.trim()) {
    ElMessage.warning('请输入用户名')
    return
  }
  if (!form.password) {
    ElMessage.warning('请输入密码')
    return
  }

  loading.value = true
  try {
    const res = await login({
      username: form.username.trim(),
      password: form.password
    })
    
    if (res.success) {
      // 设置Cookie安全属性（sameSite防止CSRF，path确保全局可访问）
      const cookieOptions = { 
        expires: rememberMe.value ? 7 : 1,
        sameSite: 'strict',  // 禁止跨站携带，防止CSRF
        path: '/'            // 全局路径可访问
        // 生产环境建议添加: secure: true （仅HTTPS传输）
      }
      Cookies.set('user_id', res.user.id, cookieOptions)
      Cookies.set('username', res.user.username, cookieOptions)
      Cookies.set('name', res.user.name, cookieOptions)
      ElMessage.success('登录成功')
      router.push('/admin')
    } else {
      ElMessage.error(res.message || '登录失败')
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '网络错误')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  usernameInput.value?.focus()
})
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0a0a0f 0%, #12121a 50%, #0d0d14 100%);
  position: relative;
  overflow: hidden;
  padding: 40px 20px;
}

/* 背景动画 */
.bg-animation {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  overflow: hidden;
}

.gradient-mesh {
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: 
    radial-gradient(ellipse at 30% 20%, rgba(99, 102, 241, 0.15) 0%, transparent 50%),
    radial-gradient(ellipse at 70% 80%, rgba(0, 245, 212, 0.1) 0%, transparent 50%),
    radial-gradient(ellipse at 50% 50%, rgba(139, 92, 246, 0.08) 0%, transparent 60%);
  animation: meshMove 20s ease-in-out infinite;
}

@keyframes meshMove {
  0%, 100% { transform: translate(0, 0) rotate(0deg); }
  33% { transform: translate(2%, 2%) rotate(1deg); }
  66% { transform: translate(-1%, 1%) rotate(-1deg); }
}

.floating-shapes {
  position: absolute;
  width: 100%;
  height: 100%;
}

.shape {
  position: absolute;
  border-radius: 50%;
  filter: blur(60px);
  opacity: 0.4;
  animation: floatShape 15s ease-in-out infinite;
}

.shape-1 {
  width: 300px;
  height: 300px;
  background: rgba(99, 102, 241, 0.3);
  top: 10%;
  left: 10%;
  animation-delay: 0s;
}

.shape-2 {
  width: 200px;
  height: 200px;
  background: rgba(0, 245, 212, 0.2);
  top: 60%;
  right: 15%;
  animation-delay: -3s;
}

.shape-3 {
  width: 250px;
  height: 250px;
  background: rgba(139, 92, 246, 0.25);
  bottom: 20%;
  left: 20%;
  animation-delay: -6s;
}

.shape-4 {
  width: 180px;
  height: 180px;
  background: rgba(99, 102, 241, 0.2);
  top: 40%;
  right: 30%;
  animation-delay: -9s;
}

.shape-5 {
  width: 220px;
  height: 220px;
  background: rgba(0, 245, 212, 0.15);
  bottom: 30%;
  right: 10%;
  animation-delay: -12s;
}

.shape-6 {
  width: 150px;
  height: 150px;
  background: rgba(139, 92, 246, 0.2);
  top: 20%;
  left: 40%;
  animation-delay: -15s;
}

@keyframes floatShape {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(30px, -30px) scale(1.1); }
}

/* 返回按钮 */
.back-btn {
  position: absolute;
  top: 30px;
  left: 30px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.3s ease;
  z-index: 10;
}

.back-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.2);
  color: white;
  transform: translateX(-4px);
}

.back-btn svg {
  width: 18px;
  height: 18px;
}

/* 登录容器 */
.login-container {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 900px;
}

.login-card {
  display: grid;
  grid-template-columns: 1fr 1.2fr;
  background: rgba(15, 15, 25, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 24px;
  overflow: hidden;
  box-shadow: 
    0 25px 50px rgba(0, 0, 0, 0.5),
    0 0 0 1px rgba(255, 255, 255, 0.05) inset;
}

/* 左侧视觉 */
.card-visual {
  position: relative;
  padding: 48px;
  background: linear-gradient(180deg, rgba(99, 102, 241, 0.2) 0%, rgba(0, 245, 212, 0.1) 100%);
  display: flex;
  flex-direction: column;
  justify-content: center;
  overflow: hidden;
}

.visual-glow {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, rgba(99, 102, 241, 0.3) 0%, transparent 70%);
  filter: blur(40px);
  animation: pulse 4s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 0.5; transform: translate(-50%, -50%) scale(1); }
  50% { opacity: 0.8; transform: translate(-50%, -50%) scale(1.1); }
}

.visual-content {
  position: relative;
  z-index: 1;
}

.logo-badge {
  width: 64px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #6366f1, #00f5d4);
  border-radius: 16px;
  margin-bottom: 24px;
  box-shadow: 0 10px 30px rgba(99, 102, 241, 0.4);
}

.logo-badge svg {
  width: 32px;
  height: 32px;
  color: white;
}

.visual-content h2 {
  font-family: 'Orbitron', sans-serif;
  font-size: 1.75rem;
  font-weight: 700;
  color: white;
  margin-bottom: 8px;
}

.visual-content p {
  font-size: 1rem;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 32px;
}

.feature-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 12px;
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.95rem;
}

.feature-check {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 245, 212, 0.2);
  border-radius: 6px;
  color: #00f5d4;
}

.feature-check svg {
  width: 14px;
  height: 14px;
}

/* 右侧表单 */
.card-form {
  padding: 48px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.form-header {
  margin-bottom: 32px;
}

.form-header h1 {
  font-size: 1.75rem;
  font-weight: 700;
  color: white;
  margin-bottom: 8px;
}

.form-header p {
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.95rem;
}

.form-body {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.input-group {
  position: relative;
}

.input-label {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.9rem;
  transition: color 0.3s ease;
}

.input-group.focused .input-label {
  color: #00f5d4;
}

.input-label svg {
  width: 18px;
  height: 18px;
}

.input-group input {
  width: 100%;
  padding: 14px 16px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  color: white;
  font-size: 1rem;
  transition: all 0.3s ease;
}

.input-group input::placeholder {
  color: rgba(255, 255, 255, 0.3);
}

.input-group input:focus {
  outline: none;
  border-color: #00f5d4;
  background: rgba(0, 245, 212, 0.05);
  box-shadow: 0 0 0 3px rgba(0, 245, 212, 0.1);
}

.password-wrapper {
  position: relative;
}

.password-wrapper input {
  padding-right: 50px;
}

.toggle-password {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.4);
  cursor: pointer;
  transition: all 0.3s ease;
}

.toggle-password:hover {
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.7);
}

.toggle-password svg {
  width: 20px;
  height: 20px;
}

.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.remember-me {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.9rem;
}

.remember-me input {
  display: none;
}

.checkmark {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-radius: 5px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.remember-me input:checked + .checkmark {
  background: linear-gradient(135deg, #6366f1, #00f5d4);
  border-color: transparent;
}

.remember-me input:checked + .checkmark::after {
  content: '';
  width: 6px;
  height: 10px;
  border: solid white;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
  margin-bottom: 2px;
}

.submit-btn {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 16px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border: none;
  border-radius: 12px;
  color: white;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  overflow: hidden;
  transition: all 0.3s ease;
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 30px rgba(99, 102, 241, 0.4);
}

.submit-btn:disabled {
  cursor: not-allowed;
  opacity: 0.8;
}

.btn-icon svg {
  width: 20px;
  height: 20px;
}

.btn-loader {
  position: absolute;
  width: 20px;
  height: 20px;
  border: 2px solid transparent;
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  opacity: 0;
}

.submit-btn.loading .btn-text,
.submit-btn.loading .btn-icon {
  opacity: 0;
}

.submit-btn.loading .btn-loader {
  opacity: 1;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.form-footer {
  margin-top: 24px;
  text-align: center;
}

.form-footer p {
  color: rgba(255, 255, 255, 0.4);
  font-size: 0.85rem;
}

.form-footer .highlight {
  color: #00f5d4;
  font-family: 'Orbitron', monospace;
}

/* 响应式 */
@media (max-width: 768px) {
  .login-card {
    grid-template-columns: 1fr;
  }
  
  .card-visual {
    display: none;
  }
  
  .card-form {
    padding: 32px;
  }
  
  .back-btn {
    top: 16px;
    left: 16px;
  }
}

@media (max-width: 480px) {
  .login-page {
    padding: 80px 16px 16px;
  }
  
  .card-form {
    padding: 24px;
  }
}
</style>
