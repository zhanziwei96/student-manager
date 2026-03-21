<template>
  <div class="public-home">
    <!-- 背景动画 -->
    <div class="hero-bg">
      <div class="gradient-overlay"></div>
      <div class="particles">
        <div v-for="n in 15" :key="n" class="particle" :style="getParticleStyle(n)"></div>
      </div>
    </div>

    <!-- 顶部导航 -->
    <nav class="main-nav">
      <div class="nav-brand" @click="scrollToTop">
        <div class="brand-logo">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 2L2 7l10 5 10-5-10-5z"/>
            <path d="M2 17l10 5 10-5"/>
          </svg>
        </div>
        <span class="brand-text">ClassHub</span>
      </div>
      
      <div class="nav-links">
        <a href="#features" class="nav-link">功能</a>
        <a href="#about" class="nav-link">关于</a>
        <button class="nav-btn primary" @click="$router.push('/login')">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/>
            <polyline points="10 17 15 12 10 7"/>
          </svg>
          <span>教师入口</span>
        </button>
      </div>
    </nav>

    <!-- Hero Section -->
    <section class="hero-section">
      <div class="hero-content">
        <div class="hero-badge">
          <span class="badge-dot"></span>
          <span>智能班级管理平台</span>
        </div>
        
        <h1 class="hero-title">
          让班级管理
          <span class="gradient-text">更智能</span>
        </h1>
        
        <p class="hero-desc">
          一站式班级管理解决方案，支持学生签到、分数管理、成绩统计等功能
          <br>帮助教师高效管理班级，提升教学效率
        </p>
        
        <div class="hero-actions">
          <button class="btn-primary" @click="$router.push('/login')">
            <span>开始使用</span>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="5" y1="12" x2="19" y2="12"/>
              <polyline points="12 5 19 12 12 19"/>
            </svg>
          </button>
          
          <button class="btn-secondary" @click="$router.push('/checkin')">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
            </svg>
            <span>学生签到</span>
          </button>
        </div>
        
        <!-- 统计数据 -->
        <div class="hero-stats">
          <div class="stat-item">
            <span class="stat-number">{{ stats.students }}</span>
            <span class="stat-label">学生</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <span class="stat-number">{{ stats.classes }}</span>
            <span class="stat-label">班级</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <span class="stat-number">{{ stats.checkins }}</span>
            <span class="stat-label">今日签到</span>
          </div>
        </div>
      </div>
      
      <!-- 3D 装饰卡片 -->
      <div class="hero-visual">
        <div class="floating-card card-1">
          <div class="card-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
          </div>
          <div class="card-text">
            <span class="card-title">签到成功</span>
            <span class="card-subtitle">张三同学</span>
          </div>
        </div>
        
        <div class="floating-card card-2">
          <div class="card-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 20h9"/>
              <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/>
            </svg>
          </div>
          <div class="card-text">
            <span class="card-title">分数 +5</span>
            <span class="card-subtitle">主动回答问题</span>
          </div>
        </div>
        
        <div class="floating-card card-3">
          <div class="card-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
            </svg>
          </div>
          <div class="card-text">
            <span class="card-title">排名第 1</span>
            <span class="card-subtitle">表现优秀</span>
          </div>
        </div>
      </div>
    </section>

    <!-- Features Section -->
    <section id="features" class="features-section">
      <div class="section-header">
        <span class="section-badge">功能亮点</span>
        <h2 class="section-title">强大的班级管理功能</h2>
        <p class="section-desc">提供全方位的班级管理工具，让教学工作更加轻松高效</p>
      </div>
      
      <div class="features-grid">
        <div class="feature-card">
          <div class="feature-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
            </svg>
          </div>
          <h3>智能签到</h3>
          <p>支持实时签到，自动统计签到率，让课堂管理更轻松</p>
        </div>
        
        <div class="feature-card">
          <div class="feature-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 20h9"/>
              <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/>
            </svg>
          </div>
          <h3>分数管理</h3>
          <p>灵活的分数增减机制，支持自定义分数标签和变更记录</p>
        </div>
        
        <div class="feature-card">
          <div class="feature-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="20" x2="18" y2="10"/>
              <line x1="12" y1="20" x2="12" y2="4"/>
              <line x1="6" y1="20" x2="6" y2="14"/>
            </svg>
          </div>
          <h3>数据可视化</h3>
          <p>直观的数据展示和排行榜，实时掌握班级动态</p>
        </div>
        
        <div class="feature-card">
          <div class="feature-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
              <circle cx="9" cy="7" r="4"/>
              <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
            </svg>
          </div>
          <h3>批量导入</h3>
          <p>支持 Excel 批量导入学生信息，快速建立班级数据库</p>
        </div>
      </div>
    </section>

    <!-- About Section -->
    <section id="about" class="about-section">
      <div class="about-content">
        <div class="about-text">
          <span class="section-badge">关于系统</span>
          <h2 class="section-title">专为班级管理设计</h2>
          <p class="section-desc">
            ClassHub 是一款专业的班级管理工具，旨在帮助教师更好地管理学生、
            追踪学习进度、激励学生进步。通过数据化的管理方式，让班级管理更加科学高效。
          </p>
          
          <div class="about-features">
            <div class="about-item">
              <div class="item-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
              </div>
              <span>安全可靠的数据存储</span>
            </div>
            <div class="about-item">
              <div class="item-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
              </div>
              <span>实时同步的签到系统</span>
            </div>
            <div class="about-item">
              <div class="item-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
              </div>
              <span>灵活的分数管理</span>
            </div>
          </div>
        </div>
        
        <div class="about-image">
          <div class="dashboard-mockup">
            <div class="mockup-header">
              <div class="mockup-dot red"></div>
              <div class="mockup-dot yellow"></div>
              <div class="mockup-dot green"></div>
            </div>
            <div class="mockup-content">
              <div class="mockup-stats">
                <div class="mockup-stat">
                  <div class="stat-line"></div>
                  <div class="stat-line short"></div>
                </div>
                <div class="mockup-stat">
                  <div class="stat-line"></div>
                  <div class="stat-line short"></div>
                </div>
                <div class="mockup-stat">
                  <div class="stat-line"></div>
                  <div class="stat-line short"></div>
                </div>
              </div>
              <div class="mockup-list">
                <div class="mockup-row" v-for="n in 4" :key="n">
                  <div class="row-avatar"></div>
                  <div class="row-lines">
                    <div class="row-line"></div>
                    <div class="row-line short"></div>
                  </div>
                  <div class="row-score">{{ 85 + n * 3 }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Footer -->
    <footer class="main-footer">
      <div class="footer-content">
        <div class="footer-brand">
          <div class="brand-logo">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 2L2 7l10 5 10-5-10-5z"/>
              <path d="M2 17l10 5 10-5"/>
            </svg>
          </div>
          <span>ClassHub</span>
        </div>
        <p class="footer-text">© 2025 ClassHub. 智能班级管理平台</p>
        <div class="footer-links">
          <a href="#" class="footer-link">帮助</a>
          <a href="#" class="footer-link">隐私</a>
          <a href="#" class="footer-link">条款</a>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getStats } from '@/api'

const stats = ref({
  students: 0,
  classes: 0,
  checkins: 0
})

const getParticleStyle = (n) => {
  const size = Math.random() * 4 + 2
  const left = Math.random() * 100
  const delay = Math.random() * 8
  const duration = Math.random() * 10 + 10
  return {
    width: `${size}px`,
    height: `${size}px`,
    left: `${left}%`,
    animationDelay: `${delay}s`,
    animationDuration: `${duration}s`
  }
}

const scrollToTop = () => {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const loadStats = async () => {
  try {
    const res = await getStats()
    if (res.data) {
      stats.value = {
        students: res.data.student_count || 0,
        classes: res.data.class_count || 0,
        checkins: res.data.today_checkin || 0
      }
    }
  } catch (error) {
    // 静默失败
  }
}

onMounted(() => {
  loadStats()
})
</script>

<style scoped>
.public-home {
  min-height: 100vh;
  background: #0a0a0f;
  color: white;
  overflow-x: hidden;
}

/* Hero Background */
.hero-bg {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 100vh;
  pointer-events: none;
  z-index: 0;
}

.gradient-overlay {
  position: absolute;
  inset: 0;
  background: 
    radial-gradient(ellipse at 20% 20%, rgba(99, 102, 241, 0.15) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 80%, rgba(6, 182, 212, 0.1) 0%, transparent 50%);
}

.particles {
  position: absolute;
  inset: 0;
}

.particle {
  position: absolute;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  animation: float-up linear infinite;
  opacity: 0;
}

@keyframes float-up {
  0% {
    transform: translateY(100vh) rotate(0deg);
    opacity: 0;
  }
  10% {
    opacity: 0.5;
  }
  90% {
    opacity: 0.5;
  }
  100% {
    transform: translateY(-10vh) rotate(720deg);
    opacity: 0;
  }
}

/* Navigation */
.main-nav {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 40px;
  z-index: 100;
  background: rgba(10, 10, 15, 0.8);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
}

.brand-logo {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border-radius: 12px;
}

.brand-logo svg {
  width: 22px;
  height: 22px;
}

.brand-text {
  font-size: 1.25rem;
  font-weight: 700;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 8px;
}

.nav-link {
  padding: 10px 16px;
  color: rgba(255, 255, 255, 0.7);
  text-decoration: none;
  font-size: 0.95rem;
  border-radius: 10px;
  transition: all 0.3s ease;
}

.nav-link:hover {
  color: white;
  background: rgba(255, 255, 255, 0.05);
}

.nav-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  color: white;
  font-size: 0.95rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.nav-btn:hover {
  background: rgba(255, 255, 255, 0.1);
}

.nav-btn.primary {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border-color: transparent;
}

.nav-btn.primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(99, 102, 241, 0.4);
}

.nav-btn svg {
  width: 18px;
  height: 18px;
}

/* Hero Section */
.hero-section {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 100px 40px;
  gap: 60px;
}

.hero-content {
  max-width: 600px;
  text-align: center;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: rgba(99, 102, 241, 0.1);
  border: 1px solid rgba(99, 102, 241, 0.3);
  border-radius: 50px;
  font-size: 0.85rem;
  color: #818cf8;
  margin-bottom: 24px;
}

.badge-dot {
  width: 6px;
  height: 6px;
  background: #34d399;
  border-radius: 50%;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.hero-title {
  font-size: 4rem;
  font-weight: 800;
  line-height: 1.1;
  margin-bottom: 20px;
}

.gradient-text {
  background: linear-gradient(135deg, #6366f1, #06b6d4);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-desc {
  font-size: 1.1rem;
  color: rgba(255, 255, 255, 0.6);
  line-height: 1.8;
  margin-bottom: 32px;
}

.hero-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-bottom: 48px;
}

.btn-primary {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 28px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border: none;
  border-radius: 12px;
  color: white;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 30px rgba(99, 102, 241, 0.4);
}

.btn-primary svg {
  width: 18px;
  height: 18px;
}

.btn-secondary {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 28px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  color: white;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.2);
}

.btn-secondary svg {
  width: 18px;
  height: 18px;
}

.hero-stats {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 32px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stat-number {
  font-size: 2rem;
  font-weight: 700;
  color: white;
}

.stat-label {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.5);
}

.stat-divider {
  width: 1px;
  height: 40px;
  background: rgba(255, 255, 255, 0.1);
}

/* Hero Visual */
.hero-visual {
  position: relative;
  width: 400px;
  height: 500px;
}

.floating-card {
  position: absolute;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  backdrop-filter: blur(10px);
  animation: float 6s ease-in-out infinite;
}

.card-1 {
  top: 20%;
  left: 0;
  animation-delay: 0s;
}

.card-2 {
  top: 50%;
  right: 0;
  animation-delay: -2s;
}

.card-3 {
  bottom: 15%;
  left: 15%;
  animation-delay: -4s;
}

@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-15px); }
}

.card-icon {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border-radius: 12px;
}

.card-icon svg {
  width: 22px;
  height: 22px;
}

.card-text {
  display: flex;
  flex-direction: column;
}

.card-title {
  font-weight: 600;
  color: white;
}

.card-subtitle {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.5);
}

/* Features Section */
.features-section {
  position: relative;
  padding: 120px 40px;
  background: linear-gradient(180deg, transparent, rgba(99, 102, 241, 0.03));
}

.section-header {
  text-align: center;
  margin-bottom: 60px;
}

.section-badge {
  display: inline-block;
  padding: 8px 16px;
  background: rgba(99, 102, 241, 0.1);
  border: 1px solid rgba(99, 102, 241, 0.2);
  border-radius: 50px;
  font-size: 0.85rem;
  color: #818cf8;
  margin-bottom: 16px;
}

.section-title {
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 16px;
}

.section-desc {
  font-size: 1.1rem;
  color: rgba(255, 255, 255, 0.5);
  max-width: 500px;
  margin: 0 auto;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.feature-card {
  padding: 32px 24px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 20px;
  text-align: center;
  transition: all 0.3s ease;
}

.feature-card:hover {
  background: rgba(255, 255, 255, 0.06);
  border-color: rgba(99, 102, 241, 0.3);
  transform: translateY(-8px);
}

.feature-icon {
  width: 64px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(6, 182, 212, 0.1));
  border-radius: 16px;
  margin: 0 auto 20px;
}

.feature-icon svg {
  width: 28px;
  height: 28px;
  color: #818cf8;
}

.feature-card h3 {
  font-size: 1.1rem;
  font-weight: 600;
  margin-bottom: 10px;
}

.feature-card p {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.5);
  line-height: 1.6;
}

/* About Section */
.about-section {
  position: relative;
  padding: 120px 40px;
}

.about-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 80px;
  max-width: 1200px;
  margin: 0 auto;
  align-items: center;
}

.about-text {
  max-width: 480px;
}

.about-text .section-title {
  text-align: left;
}

.about-text .section-desc {
  text-align: left;
  margin: 0 0 32px 0;
}

.about-features {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.about-item {
  display: flex;
  align-items: center;
  gap: 12px;
  color: rgba(255, 255, 255, 0.8);
}

.item-icon {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(16, 185, 129, 0.2);
  border-radius: 6px;
  color: #34d399;
}

.item-icon svg {
  width: 14px;
  height: 14px;
}

/* Dashboard Mockup */
.about-image {
  display: flex;
  justify-content: center;
}

.dashboard-mockup {
  width: 380px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
}

.mockup-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.03);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.mockup-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.mockup-dot.red { background: #ef4444; }
.mockup-dot.yellow { background: #f59e0b; }
.mockup-dot.green { background: #10b981; }

.mockup-content {
  padding: 20px;
}

.mockup-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}

.mockup-stat {
  padding: 16px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12px;
}

.stat-line {
  height: 12px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  margin-bottom: 8px;
}

.stat-line.short {
  width: 60%;
  height: 8px;
}

.mockup-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 10px;
  margin-bottom: 8px;
}

.row-avatar {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border-radius: 50%;
}

.row-lines {
  flex: 1;
}

.row-line {
  height: 10px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 5px;
  margin-bottom: 6px;
}

.row-line.short {
  width: 50%;
}

.row-score {
  font-weight: 600;
  color: #06b6d4;
}

/* Footer */
.main-footer {
  padding: 40px;
  background: rgba(255, 255, 255, 0.02);
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.footer-content {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.footer-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  font-weight: 600;
}

.footer-text {
  color: rgba(255, 255, 255, 0.4);
  font-size: 0.9rem;
}

.footer-links {
  display: flex;
  gap: 24px;
}

.footer-link {
  color: rgba(255, 255, 255, 0.5);
  text-decoration: none;
  font-size: 0.9rem;
  transition: color 0.3s ease;
}

.footer-link:hover {
  color: white;
}

/* Responsive */
@media (max-width: 1024px) {
  .hero-section {
    flex-direction: column;
    text-align: center;
    padding-top: 140px;
  }
  
  .hero-visual {
    display: none;
  }
  
  .features-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .about-content {
    grid-template-columns: 1fr;
    gap: 40px;
  }
  
  .about-text {
    text-align: center;
  }
  
  .about-text .section-title,
  .about-text .section-desc {
    text-align: center;
  }
  
  .about-features {
    align-items: center;
  }
}

@media (max-width: 640px) {
  .main-nav {
    padding: 16px 20px;
  }
  
  .nav-links {
    gap: 4px;
  }
  
  .nav-link {
    display: none;
  }
  
  .hero-title {
    font-size: 2.5rem;
  }
  
  .features-grid {
    grid-template-columns: 1fr;
  }
  
  .footer-content {
    flex-direction: column;
    gap: 20px;
  }
}
</style>
