/**
 * 测试高德地图类型定义 - TypeScript 编译时检查
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

describe('AMap 类型定义', () => {
  beforeEach(() => {
    // 模拟 window.AMap
    window.AMap = {
      Map: vi.fn().mockImplementation(() => ({
        destroy: vi.fn(),
        resize: vi.fn(),
        setCenter: vi.fn(),
        setZoom: vi.fn(),
        getCenter: vi.fn().mockReturnValue({ getLng: () => 116.397428, getLat: () => 39.90923 }),
        getZoom: vi.fn().mockReturnValue(16),
        add: vi.fn(),
        remove: vi.fn(),
        clearMap: vi.fn(),
        on: vi.fn(),
        off: vi.fn(),
      })),
      Marker: vi.fn().mockImplementation(() => ({
        setPosition: vi.fn(),
        getPosition: vi.fn().mockReturnValue({ getLng: () => 116.397428, getLat: () => 39.90923 }),
        setTitle: vi.fn(),
        setDraggable: vi.fn(),
        show: vi.fn(),
        hide: vi.fn(),
      })),
      Pixel: vi.fn().mockImplementation((x: number, y: number) => ({ x, y })),
      Size: vi.fn().mockImplementation((width: number, height: number) => ({ width, height })),
      Icon: vi.fn().mockImplementation((options) => ({ ...options })),
    } as unknown as AMapConstructor
  })

  it('应该能创建地图实例', () => {
    const container = document.createElement('div')
    const map = new window.AMap.Map(container, {
      zoom: 16,
      center: [116.397428, 39.90923],
      viewMode: '2D',
      resizeEnable: true,
    })

    expect(map).toBeDefined()
    expect(window.AMap.Map).toHaveBeenCalledWith(container, {
      zoom: 16,
      center: [116.397428, 39.90923],
      viewMode: '2D',
      resizeEnable: true,
    })
  })

  it('应该能创建标记', () => {
    const marker = new window.AMap.Marker({
      position: [116.397428, 39.90923],
      title: '测试标记',
    })

    expect(marker).toBeDefined()
    expect(window.AMap.Marker).toHaveBeenCalledWith({
      position: [116.397428, 39.90923],
      title: '测试标记',
    })
  })

  it('地图方法应该有正确类型', () => {
    const container = document.createElement('div')
    const map = new window.AMap.Map(container)

    // 验证方法存在且可调用
    expect(typeof map.destroy).toBe('function')
    expect(typeof map.resize).toBe('function')
    expect(typeof map.setCenter).toBe('function')
    expect(typeof map.setZoom).toBe('function')
    expect(typeof map.getCenter).toBe('function')
    expect(typeof map.getZoom).toBe('function')
    expect(typeof map.add).toBe('function')
    expect(typeof map.remove).toBe('function')
    expect(typeof map.clearMap).toBe('function')
    expect(typeof map.on).toBe('function')
    expect(typeof map.off).toBe('function')
  })

  it('标记方法应该有正确类型', () => {
    const marker = new window.AMap.Marker()

    expect(typeof marker.setPosition).toBe('function')
    expect(typeof marker.getPosition).toBe('function')
    expect(typeof marker.setTitle).toBe('function')
    expect(typeof marker.setDraggable).toBe('function')
    expect(typeof marker.show).toBe('function')
    expect(typeof marker.hide).toBe('function')
  })

  it('应该能绑定点击事件', () => {
    const container = document.createElement('div')
    const map = new window.AMap.Map(container)

    const clickHandler = (e: AMapMapClickEvent) => {
      const lng = e.lnglat.getLng()
      const lat = e.lnglat.getLat()
      console.log(lng, lat)
    }

    map.on('click', clickHandler)
    expect(map.on).toHaveBeenCalledWith('click', clickHandler)
  })

  it('经纬度对象应该有正确方法', () => {
    const mockLngLat: AMapLngLat = {
      getLng: vi.fn().mockReturnValue(116.397428),
      getLat: vi.fn().mockReturnValue(39.90923),
    }

    expect(mockLngLat.getLng()).toBe(116.397428)
    expect(mockLngLat.getLat()).toBe(39.90923)
  })

  it('应该支持 Pixel 和 Size 类', () => {
    const pixel = new window.AMap.Pixel(10, 20)
    expect(pixel).toEqual({ x: 10, y: 20 })

    const size = new window.AMap.Size(100, 200)
    expect(size).toEqual({ width: 100, height: 200 })
  })
})
