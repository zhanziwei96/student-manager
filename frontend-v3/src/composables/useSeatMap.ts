import { computed, type Ref } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import { classroomsApi } from '@/api/seats'

/** 座位图查询：classroomId 与 sessionId 都有值才拉取，10s 轮询。 */
export function useSeatMap(classroomId: Ref<number | null>, sessionId: Ref<number | null>) {
  const enabled = computed(() => classroomId.value != null && sessionId.value != null)
  return useQuery({
    queryKey: computed(() => ['seat-map', classroomId.value, sessionId.value]),
    queryFn: () => classroomsApi.getSeats(classroomId.value!, sessionId.value),
    enabled,
    refetchInterval: 10_000,
  })
}
