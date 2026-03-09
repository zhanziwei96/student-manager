/**
 * 数据缓存管理器
 * 支持内存缓存和 localStorage 持久化
 */

class CacheManager {
  constructor() {
    this.memoryCache = new Map()
    this.defaultTTL = 5 * 60 * 1000 // 默认5分钟
  }

  /**
   * 设置缓存
   * @param {string} key - 缓存键
   * @param {*} data - 缓存数据
   * @param {number} ttl - 过期时间（毫秒）
   */
  set(key, data, ttl = this.defaultTTL) {
    const cacheItem = {
      data,
      expireTime: Date.now() + ttl
    }
    
    // 内存缓存
    this.memoryCache.set(key, cacheItem)
    
    // localStorage 持久化（支持对象存储）
    try {
      localStorage.setItem(`cache_${key}`, JSON.stringify(cacheItem))
    } catch (e) {
      console.warn('localStorage 存储失败:', e)
    }
  }

  /**
   * 获取缓存
   * @param {string} key - 缓存键
   * @returns {*} 缓存数据或 null
   */
  get(key) {
    // 先检查内存缓存
    let cacheItem = this.memoryCache.get(key)
    
    // 内存中没有，尝试从 localStorage 恢复
    if (!cacheItem) {
      try {
        const stored = localStorage.getItem(`cache_${key}`)
        if (stored) {
          cacheItem = JSON.parse(stored)
          // 恢复到内存缓存
          this.memoryCache.set(key, cacheItem)
        }
      } catch (e) {
        console.warn('localStorage 读取失败:', e)
      }
    }

    // 检查是否过期
    if (cacheItem) {
      if (Date.now() < cacheItem.expireTime) {
        return cacheItem.data
      } else {
        // 过期删除
        this.delete(key)
      }
    }
    
    return null
  }

  /**
   * 删除缓存
   * @param {string} key - 缓存键
   */
  delete(key) {
    this.memoryCache.delete(key)
    try {
      localStorage.removeItem(`cache_${key}`)
    } catch (e) {
      console.warn('localStorage 删除失败:', e)
    }
  }

  /**
   * 清空所有缓存
   */
  clear() {
    this.memoryCache.clear()
    // 只清除本应用的缓存
    try {
      for (let i = localStorage.length - 1; i >= 0; i--) {
        const key = localStorage.key(i)
        if (key && key.startsWith('cache_')) {
          localStorage.removeItem(key)
        }
      }
    } catch (e) {
      console.warn('localStorage 清空失败:', e)
    }
  }

  /**
   * 获取缓存剩余有效时间
   * @param {string} key - 缓存键
   * @returns {number} 剩余毫秒数，-1 表示不存在或已过期
   */
  getTTL(key) {
    const cacheItem = this.memoryCache.get(key)
    if (cacheItem && Date.now() < cacheItem.expireTime) {
      return cacheItem.expireTime - Date.now()
    }
    return -1
  }

  /**
   * 检查缓存是否存在且有效
   * @param {string} key - 缓存键
   * @returns {boolean}
   */
  has(key) {
    return this.getTTL(key) > 0
  }
}

// 导出单例实例
export const cache = new CacheManager()

// 导出缓存键名常量
export const CACHE_KEYS = {
  STUDENTS: 'students',
  CLASS_LIST: 'class_list',
  STATS: 'stats',
  CHECKIN_RECORDS: 'checkin_records'
}

export default cache
