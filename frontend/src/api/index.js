import request from './request'

// 用户相关
export const login = (data) => request.post('/login', data)
export const logout = () => request.post('/logout')
export const getUserInfo = () => request.get('/me')
export const changePassword = (data) => request.post('/change-password', data)
export const createUser = (data) => request.post('/admin/users', data)

// 学生管理
export const getStudents = () => request.get('/students')
export const getStudentsWithCheckin = () => request.get('/students?with_checkin=true')
export const addStudent = (data) => request.post('/students', data)
export const deleteStudent = (id) => request.delete(`/students/${id}`)
export const updateScore = (id, data) => request.post(`/students/${id}/score`, data)
export const importStudents = (data) => request.post('/students/import', data, {
  headers: { 'Content-Type': 'multipart/form-data' }
})

// 班级管理
export const deleteClass = (className) => request.delete(`/class/${encodeURIComponent(className)}`)

// 签到相关
export const checkin = (data) => request.post('/checkin', data)
export const getCheckinRecords = (params) => request.get('/checkin/records', { params })
export const teacherCheckin = (data) => request.post('/teacher-checkin', data)

// 上课状态
export const getClassSession = () => request.get('/class-session')
export const setClassSession = (data) => request.post('/class-session', data)
export const getClassSessionStudents = () => request.get('/class-session/students')

// 分数日志
export const getScoreLogs = (params) => request.get('/score/logs', { params })

// 分数重置
export const resetAllScores = (data) => request.post('/admin/reset-scores', data)

// 数据库信息
export const getDbInfo = () => request.get('/db-info')

// 首页统计
export const getStats = () => request.get('/stats')

// 学生查询（查看自己的分数、排名和记录）
export const queryStudent = (data) => request.post('/student/query', data)
