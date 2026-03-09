<template>
  <div class="home-container">
    <div class="hero-section">
      <h1>📚 班级管理系统</h1>
      <p class="subtitle">便捷的学生管理、签到、分数统计工具</p>
      
      <div class="action-buttons">
        <el-button type="primary" size="large" @click="$router.push('/checkin')">
          📝 学生签到
        </el-button>
        <el-button type="success" size="large" @click="$router.push('/admin')">
          👨‍🏫 教师入口
        </el-button>
      </div>
    </div>
    
    <el-row :gutter="20" class="features">
      <el-col :span="8">
        <el-card class="feature-card">
          <template #header>
            <span>📊 学生管理</span>
          </template>
          <p>支持单个添加、批量导入、班级分组管理</p>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="feature-card">
          <template #header>
            <span>📝 签到系统</span>
          </template>
          <p>在线签到，实时统计</p>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="feature-card">
          <template #header>
            <span>🎯 分数管理</span>
          </template>
          <p>分数增减记录、操作日志、一键重置</p>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.home-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 40px 20px;
}

.hero-section {
  text-align: center;
  color: white;
  padding: 60px 20px;
}

.hero-section h1 {
  font-size: 48px;
  margin-bottom: 20px;
}

.subtitle {
  font-size: 20px;
  opacity: 0.9;
  margin-bottom: 40px;
}

.action-buttons {
  display: flex;
  justify-content: center;
  gap: 20px;
}

.action-buttons .el-button {
  font-size: 18px;
  padding: 20px 40px;
}

.features {
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px;
}

.feature-card {
  text-align: center;
  height: 100%;
}

.feature-card p {
  color: #666;
  line-height: 1.6;
}
</style>
