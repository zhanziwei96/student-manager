/**
 * 设备指纹工具 - 使用 FingerprintJS 生成高精度设备标识
 */
import FingerprintJS from '@fingerprintjs/fingerprintjs'

const STORAGE_KEY = 'checkin_device_id'

/**
 * 生成设备指纹
 * 使用 FingerprintJS 生成高精度 visitorId，并缓存到 localStorage
 */
export async function getDeviceFingerprint(): Promise<string> {
  // 1. 检查 localStorage 中是否已有 device_id
  const cachedId = localStorage.getItem(STORAGE_KEY)
  if (cachedId) return cachedId

  // 2. 使用 FingerprintJS 生成 visitorId
  const fp = await FingerprintJS.load()
  const result = await fp.get()

  // 3. 缓存并返回
  localStorage.setItem(STORAGE_KEY, result.visitorId)
  return result.visitorId
}

/**
 * 获取设备信息（用于记录）
 */
export function getDeviceInfo(): object {
  return {
    userAgent: navigator.userAgent,
    platform: navigator.platform,
    language: navigator.language,
    screen: {
      width: screen.width,
      height: screen.height,
      colorDepth: screen.colorDepth,
    },
    hardwareConcurrency: navigator.hardwareConcurrency,
    timezoneOffset: new Date().getTimezoneOffset(),
  }
}

/**
 * 清除设备ID（调试用）
 */
export function clearDeviceId(): void {
  localStorage.removeItem(STORAGE_KEY)
}
