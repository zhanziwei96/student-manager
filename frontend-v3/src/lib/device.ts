/**
 * 设备指纹工具 - 用于防代签验证
 */

/**
 * 生成设备指纹
 * 使用浏览器特征生成唯一标识
 */
export async function getDeviceFingerprint(): Promise<string> {
  // 1. 检查 localStorage 中是否已有 device_id
  let deviceId = localStorage.getItem('checkin_device_id')
  if (deviceId) return deviceId

  // 2. 收集设备特征
  const components = [
    navigator.userAgent,
    navigator.language,
    screen.width + 'x' + screen.height + 'x' + screen.colorDepth,
    new Date().getTimezoneOffset(),
    !!window.sessionStorage,
    !!window.localStorage,
    !!window.indexedDB,
    navigator.hardwareConcurrency || 'unknown',
    navigator.platform || 'unknown',
  ]

  // 3. Canvas 指纹
  try {
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')
    if (ctx) {
      ctx.textBaseline = 'top'
      ctx.font = '14px Arial'
      ctx.fillStyle = '#f60'
      ctx.fillRect(0, 0, 10, 10)
      ctx.fillStyle = '#069'
      ctx.fillText('Device Fingerprint 中文', 2, 2)
      components.push(canvas.toDataURL())
    }
  } catch {
    components.push('canvas-not-supported')
  }

  // 4. WebGL 指纹
  try {
    const canvas = document.createElement('canvas')
    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl')
    if (gl) {
      const debugInfo = (gl as WebGLRenderingContext).getExtension('WEBGL_debug_renderer_info')
      if (debugInfo) {
        components.push((gl as WebGLRenderingContext).getParameter(debugInfo.UNMASKED_VENDOR_WEBGL) || '')
        components.push((gl as WebGLRenderingContext).getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) || '')
      }
    }
  } catch {
    components.push('webgl-not-supported')
  }

  // 5. 生成哈希
  deviceId = await hashString(components.join('::'))
  localStorage.setItem('checkin_device_id', deviceId)
  return deviceId
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
 * 字符串哈希（SHA-256 简化版）
 */
async function hashString(str: string): Promise<string> {
  try {
    const encoder = new TextEncoder()
    const data = encoder.encode(str)
    const hashBuffer = await crypto.subtle.digest('SHA-256', data)
    const hashArray = Array.from(new Uint8Array(hashBuffer))
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('').slice(0, 32)
  } catch {
    // 如果 crypto 不可用，使用简单哈希
    let hash = 0
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i)
      hash = ((hash << 5) - hash) + char
      hash = hash & hash
    }
    return Math.abs(hash).toString(16).padStart(32, '0').slice(0, 32)
  }
}

/**
 * 清除设备ID（调试用）
 */
export function clearDeviceId(): void {
  localStorage.removeItem('checkin_device_id')
}
