<template>
  <div class="public-home">
    <!-- 背景装饰 -->
    <div class="bg-decoration">
      <div class="glow-orb orb-1"></div>
      <div class="glow-orb orb-2"></div>
      <div class="glow-orb orb-3"></div>
    </div>

    <!-- 顶部导航 -->
    <nav class="top-nav">
      <div class="nav-brand">
        <div class="brand-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 2L2 7l10 5 10-5-10-5z"/>
            <path d="M2 17l10 5 10-5"/>
            <path d="M2 12l10 5 10-5"/>
          </svg>
        </div>
        <span class="brand-text">Class<span class="brand-highlight">Hub</span></span>
      </div>
      <div class="nav-actions">
        <button class="btn-ghost" @click="$router.push('/login')">
          <span>教师入口</span>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/>
            <polyline points="10 17 15 12 10 7"/>
            <line x1="15" y1="12" x2="3" y2="12"/>
          </svg>
        </button>
      </div>
    </nav>

    <!-- 主要内容 -->
    <main class="hero-section">
      <div class="hero-content">
        <div class="hero-badge">
          <span class="badge-dot"></span>
          <span>智能班级管理</span>
        </div>
        
        <h1 class="hero-title">
          <span class="title-line">让课堂管理</span>
          <span class="title-line gradient">更轻松高效</span>
        </h1>
        
        <p class="hero-desc">
          一站式学生签到、分数管理与课堂互动平台，支持实时数据统计与智能分析
        </p>
        
        <div class="hero-actions">
          <button class="btn-primary" @click="$router.push('/checkin')">
            <span>学生签到</span>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
              <line x1="16" y1="13" x2="8" y2="13"/>
              <line x1="16" y1="17" x2="8" y2="17"/>
              <polyline points="10 9 9 9 8 9"/>
            </svg>
          </button>
          
          <button class="btn-secondary" @click="$router.push('/home')">
            <span>查看统计</span>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M3 3v18h18"/>
              <path d="M18.7 8l-5.1 5.2-2.8-2.7L7 14.3"/>
            </svg>
          </button>
        </div>
      </div>

      <!-- 实时统计卡片 -->
      <div class="stats-grid">
        <div class="stat-card" v-for="(stat, index) in stats" :key="index">
          <div class="stat-icon" :class="stat.type">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path v-if="stat.type === 'students'" d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
              <circle v-if="stat.type === 'students'" cx="9" cy="7" r="4"/>
              <path v-if="stat.type === 'students'" d="M23 21v-2a4 4 0 0 0-3-3.87"/>
              <path v-if="stat.type === 'students'" d="M16 3.13a4 4 0 0 1 0 7.75"/>
              
              <path v-if="stat.type === 'checkin'" d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
              <polyline v-if="stat.type === 'checkin'" points="22 4 12 14.01 9 11.01"/>
              
              <path v-if="stat.type === 'classes'" d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>
              <path v-if="stat.type === 'classes'" d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
            </svg>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stat.value }}</div>
            <div class="stat-label">{{ stat.label }}</div>
          </div>
        </div>
      </div>
    </main>

    <!-- 功能特性 -->
    <section class="features-section">
      <div class="section-header">
        <span class="section-tag">功能特性</span>
        <h2>为什么选择 <span class="gradient">ClassHub</span></h2>
      </div>
      
      <div class="features-grid">
        <div class="feature-card" v-for="(feature, index) in features" :key="index">
          <div class="feature-number">0{{ index + 1 }}</div>
          <div class="feature-content">
            <h3>{{ feature.title }}</h3>
            <p>{{ feature.desc }}</p>
          </div>
          <div class="feature-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path v-if="feature.icon === 'checkin'" d="M9 11l3 3L22 4"/>
              <path v-if="feature.icon === 'checkin'" d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/>
              
              <path v-if="feature.icon === 'score'" d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
              
              <path v-if="feature.icon === 'data'" d="M21.21 15.89A10 10 0 118 2.83"/>
              <path v-if="feature.icon === 'data'" d="M22 12A10 10 0 0012 2v10z"/>
            </svg>
          </div>
        </div>
      </div>
    </section>

    <!-- 页脚 -->
    <footer class="footer">
      <p>© 2025 ClassHub 班级管理系统</p>
    </footer>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getStats } from '../api'

const stats = ref([
  { type: 'students', value: '...', label: '学生总数' },
  { type: 'checkin', value: '...', label: '今日签到' },
  { type: 'classes', value: '...', label: '班级数量' }
])

const features = [
  {
    title: '智能签到',
    desc: '支持学生自主签到，实时同步签到状态，教师端实时查看签到统计',
    icon: 'checkin'
  },
  {
    title: '分数管理',
    desc: '灵活的分数增减机制，完整的操作日志，支持一键重置',
    icon: 'score'
  },
  {
    title: '数据可视化',
    desc: '直观的排行榜展示，实时数据更新，支持历史记录查询',
    icon: 'data'
  }
]

onMounted(async () => {
  try {
    const res = await getStats()
    if (res.data) {
      stats.value[0].value = res.data.student_count || 0
      stats.value[1].value = res.data.today_checkin || 0
      stats.value[2].value = res.data.class_count || 0
    }
  } catch (e) {
    console.log('获取统计失败')
  }
})
</script>

<style scoped>
.public-home {
  min-height: 100vh;
  background: linear-gradient(135deg, #0a0a0f 0%, #12121a 50%, #0a0a0f 100%);
  position: relative;
  overflow-x: hidden;
}

/* 背景装饰 */
.bg-decoration {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 0;
}

.glow-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.5;
  animation: float 8s ease-in-out infinite;
}

.orb-1 {
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, rgba(99, 102, 241, 0.4) 0%, transparent 70%);
  top: -100px;
  right: -100px;
  animation-delay: 0s;
}

.orb-2 {
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, rgba(0, 245, 212, 0.3) 0%, transparent 70%);
  bottom: 20%;
  left: -50px;
  animation-delay: -2s;
}

.orb-3 {
  width: 250px;
  height: 250px;
  background: radial-gradient(circle, rgba(139, 92, 246, 0.3) 0%, transparent 70%);
  bottom: -50px;
  right: 20%;
  animation-delay: -4s;
}

/* 导航 */
.top-nav {
  position: relative;
  z-index: 10;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 40px;
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border-radius: 10px;
  color: white;
}

.brand-icon svg {
  width: 24px;
  height: 24px;
}

.brand-text {
  font-family: 'Orbitron', sans-serif;
  font-size: 1.5rem;
  font-weight: 700;
  color: white;
}

.brand-highlight {
  background: linear-gradient(135deg, #00f5d4, #00bbf9);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.btn-ghost {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.95rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-ghost:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.2);
  color: white;
}

.btn-ghost svg {
  width: 18px;
  height: 18px;
}

/* Hero Section */
.hero-section {
  position: relative;
  z-index: 1;
  max-width: 1200px;
  margin: 0 auto;
  padding: 80px 40px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 60px;
  align-items: center;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: rgba(99, 102, 241, 0.1);
  border: 1px solid rgba(99, 102, 241, 0.3);
  border-radius: 20px;
  font-size: 0.9rem;
  color: #818cf8;
  margin-bottom: 24px;
}

.badge-dot {
  width: 8px;
  height: 8px;
  background: #00f5d4;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.hero-title {
  font-size: 3.5rem;
  font-weight: 700;
  line-height: 1.2;
  margin-bottom: 20px;
}

.title-line {
  display: block;
  color: white;
}

.title-line.gradient {
  background: linear-gradient(135deg, #6366f1 0%, #00f5d4 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-desc {
  font-size: 1.1rem;
  color: rgba(255, 255, 255, 0.6);
  line-height: 1.8;
  margin-bottom: 32px;
  max-width: 480px;
}

.hero-actions {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
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
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 30px rgba(99, 102, 241, 0.4);
}

.btn-primary svg {
  width: 20px;
  height: 20px;
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
  width: 20px;
  height: 20px;
}

/* 统计卡片 */
.stats-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 24px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  transition: all 0.3s ease;
}

.stat-card:hover {
  background: rgba(255, 255, 255, 0.06);
  border-color: rgba(99, 102, 241, 0.3);
  transform: translateX(8px);
}

.stat-icon {
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
}

.stat-icon.students {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(99, 102, 241, 0.1));
  color: #818cf8;
}

.stat-icon.checkin {
  background: linear-gradient(135deg, rgba(0, 245, 212, 0.2), rgba(0, 245, 212, 0.1));
  color: #00f5d4;
}

.stat-icon.classes {
  background: linear-gradient(135deg, rgba(251, 191, 36, 0.2), rgba(251, 191, 36, 0.1));
  color: #fbbf24;
}

.stat-icon svg {
  width: 28px;
  height: 28px;
}

.stat-value {
  font-family: 'Orbitron', monospace;
  font-size: 2rem;
  font-weight: 700;
  color: white;
}

.stat-label {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.5);
  margin-top: 4px;
}

/* 功能特性 */
.features-section {
  position: relative;
  z-index: 1;
  padding: 80px 40px;
  background: linear-gradient(180deg, transparent 0%, rgba(99, 102, 241, 0.05) 100%);
}

.section-header {
  text-align: center;
  margin-bottom: 60px;
}

.section-tag {
  display: inline-block;
  padding: 6px 16px;
  background: rgba(0, 245, 212, 0.1);
  border: 1px solid rgba(0, 245, 212, 0.3);
  border-radius: 20px;
  font-size: 0.85rem;
  color: #00f5d4;
  margin-bottom: 16px;
}

.section-header h2 {
  font-size: 2.5rem;
  font-weight: 700;
  color: white;
}

.gradient {
  background: linear-gradient(135deg, #6366f1, #00f5d4);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.features-grid {
  max-width: 1000px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
}

.feature-card {
  position: relative;
  padding: 32px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 20px;
  overflow: hidden;
  transition: all 0.3s ease;
}

.feature-card:hover {
  background: rgba(255, 255, 255, 0.06);
  border-color: rgba(99, 102, 241, 0.3);
  transform: translateY(-8px);
}

.feature-number {
  font-family: 'Orbitron', sans-serif;
  font-size: 3rem;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.1);
  margin-bottom: 16px;
}

.feature-content h3 {
  font-size: 1.25rem;
  font-weight: 600;
  color: white;
  margin-bottom: 12px;
}

.feature-content p {
  font-size: 0.95rem;
  color: rgba(255, 255, 255, 0.5);
  line-height: 1.6;
}

.feature-icon {
  position: absolute;
  bottom: 24px;
  right: 24px;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(0, 245, 212, 0.1));
  border-radius: 12px;
  color: #818cf8;
}

.feature-icon svg {
  width: 24px;
  height: 24px;
}

/* 页脚 */
.footer {
  text-align: center;
  padding: 40px;
  color: rgba(255, 255, 255, 0.3);
  font-size: 0.9rem;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

/* 响应式 */
@media (max-width: 968px) {
  .hero-section {
    grid-template-columns: 1fr;
    text-align: center;
    padding: 60px 20px;
  }
  
  .hero-title {
    font-size: 2.5rem;
  }
  
  .hero-desc {
    margin-left: auto;
    margin-right: auto;
  }
  
  .hero-actions {
    justify-content: center;
  }
  
  .features-grid {
    grid-template-columns: 1fr;
  }
  
  .top-nav {
    padding: 16px 20px;
  }
}

@media (max-width: 640px) {
  .hero-title {
    font-size: 2rem;
  }
  
  .hero-actions {
    flex-direction: column;
  }
  
  .btn-primary,
  .btn-secondary {
    width: 100%;
    justify-content: center;
  }
}
</style>
