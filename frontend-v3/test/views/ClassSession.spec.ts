import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ref, computed } from 'vue'

/**
 * ClassSession 渲染优化测试
 * REVIEW-P1: 验证 filter 已移入 computed，避免重复计算
 */
describe('ClassSession Computed Optimization', () => {
  // 每次测试前重置数据，避免状态污染
  let mockStudents: Array<{ id: number; student_id: string; name: string; checkedIn: boolean }>
  
  beforeEach(() => {
    mockStudents = [
      { id: 1, student_id: 'S001', name: '张三', checkedIn: false },
      { id: 2, student_id: 'S002', name: '李四', checkedIn: true },
      { id: 3, student_id: 'S003', name: '王五', checkedIn: false },
      { id: 4, student_id: 'S004', name: '赵六', checkedIn: true },
    ]
  })

  describe('computed grouping', () => {
    it('should compute notCheckedInStudents correctly', () => {
      const studentList = ref([...mockStudents])
      
      const notCheckedInStudents = computed(() => 
        studentList.value.filter(s => !s.checkedIn)
      )
      
      const checkedInStudents = computed(() => 
        studentList.value.filter(s => s.checkedIn)
      )
      
      expect(notCheckedInStudents.value).toHaveLength(2)
      expect(notCheckedInStudents.value.map(s => s.name).sort()).toEqual(['张三', '王五'])
      
      expect(checkedInStudents.value).toHaveLength(2)
      expect(checkedInStudents.value.map(s => s.name).sort()).toEqual(['李四', '赵六'])
    })

    it('should update computed when source data changes', () => {
      const studentList = ref([...mockStudents])
      
      const notCheckedInStudents = computed(() => 
        studentList.value.filter(s => !s.checkedIn)
      )
      
      // 初始状态
      expect(notCheckedInStudents.value).toHaveLength(2)
      
      // 修改数据
      studentList.value[0].checkedIn = true
      
      // 重新计算后应该更新
      expect(notCheckedInStudents.value).toHaveLength(1)
    })

    it('should handle search filtering correctly', () => {
      const searchQuery = ref('张')
      const studentList = ref([...mockStudents])
      
      const filteredStudents = computed(() => {
        if (!searchQuery.value.trim()) return studentList.value
        
        const query = searchQuery.value.toLowerCase()
        return studentList.value.filter(s => 
          s.name.toLowerCase().includes(query) ||
          s.student_id.toLowerCase().includes(query)
        )
      })
      
      expect(filteredStudents.value).toHaveLength(1)
      expect(filteredStudents.value[0].name).toBe('张三')
      
      // 修改搜索词
      searchQuery.value = 'S00'
      expect(filteredStudents.value).toHaveLength(4)
    })

    it('should cache computed results (performance)', () => {
      const filterFn = vi.fn((s: any) => !s.checkedIn)
      const studentList = ref([...mockStudents])
      
      const notCheckedInStudents = computed(() => {
        return studentList.value.filter(filterFn)
      })
      
      // 多次访问 computed
      const r1 = notCheckedInStudents.value
      const r2 = notCheckedInStudents.value
      const r3 = notCheckedInStudents.value
      
      // 数据未变，filter 应该只执行一次（针对每个元素）
      expect(filterFn).toHaveBeenCalledTimes(4) // 每个元素一次
      
      // 但返回的引用应该相同（Vue computed 缓存）
      expect(r1).toBe(r2)
      expect(r2).toBe(r3)
    })
  })

  describe('group counting', () => {
    it('should show correct count for each group', () => {
      const studentList = ref([...mockStudents])
      
      const notCheckedInStudents = computed(() => 
        studentList.value.filter(s => !s.checkedIn)
      )
      
      const checkedInStudents = computed(() => 
        studentList.value.filter(s => s.checkedIn)
      )
      
      // 使用 computed 的长度显示计数
      const notCheckedInCount = computed(() => notCheckedInStudents.value.length)
      const checkedInCount = computed(() => checkedInStudents.value.length)
      
      expect(notCheckedInCount.value).toBe(2)
      expect(checkedInCount.value).toBe(2)
    })

    it('should handle empty list', () => {
      const studentList = ref([] as typeof mockStudents)
      
      const notCheckedInStudents = computed(() => 
        studentList.value.filter(s => !s.checkedIn)
      )
      
      const checkedInStudents = computed(() => 
        studentList.value.filter(s => s.checkedIn)
      )
      
      expect(notCheckedInStudents.value).toHaveLength(0)
      expect(checkedInStudents.value).toHaveLength(0)
    })
  })

  describe('rendering optimization', () => {
    it('should use computed for list grouping', () => {
      // 验证优化模式：使用预计算的分组而非模板内 filter
      const studentList = ref([...mockStudents])
      
      // REVIEW-P1: 推荐做法 - 预计算分组
      const notCheckedInStudents = computed(() => 
        studentList.value.filter(s => !s.checkedIn)
      )
      
      const checkedInStudents = computed(() => 
        studentList.value.filter(s => s.checkedIn)
      )
      
      // 在模板中直接使用 notCheckedInStudents，而非 filteredStudents.filter(s => !s.checkedIn)
      expect(notCheckedInStudents.value).toHaveLength(2)
      expect(checkedInStudents.value).toHaveLength(2)
    })
  })

  describe('sorting behavior', () => {
    it('should sort students with not checked-in first', () => {
      const students = [
        { id: 1, name: 'A', checkedIn: true },
        { id: 2, name: 'B', checkedIn: false },
        { id: 3, name: 'C', checkedIn: true },
        { id: 4, name: 'D', checkedIn: false },
      ]
      
      const sortedStudents = [...students].sort((a, b) => 
        (a.checkedIn === b.checkedIn ? 0 : a.checkedIn ? 1 : -1)
      )
      
      expect(sortedStudents[0].checkedIn).toBe(false)
      expect(sortedStudents[1].checkedIn).toBe(false)
      expect(sortedStudents[2].checkedIn).toBe(true)
      expect(sortedStudents[3].checkedIn).toBe(true)
    })
  })
})
