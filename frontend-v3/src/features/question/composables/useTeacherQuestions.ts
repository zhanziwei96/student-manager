import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { computed, type Ref } from 'vue'
import {
  getTeacherQuestions,
  createQuestion,
  closeQuestion,
} from '@/api/question'
import type { CreateQuestionRequest } from '@/types/question'

const TEACHER_QUESTIONS_KEY = 'teacher-questions'

export function useTeacherQuestions(filters?: { class_id?: number; status?: Ref<string> }) {
  const queryClient = useQueryClient()

  const queryKey = computed(() => [
    TEACHER_QUESTIONS_KEY,
    filters?.class_id,
    filters?.status?.value,
  ])

  const { data: questions, isLoading, error } = useQuery({
    queryKey,
    queryFn: () => getTeacherQuestions({
      class_id: filters?.class_id,
      status: filters?.status?.value || undefined,
    }),
  })

  const createMutation = useMutation({
    mutationFn: (data: CreateQuestionRequest) => createQuestion(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [TEACHER_QUESTIONS_KEY] })
    },
  })

  const closeMutation = useMutation({
    mutationFn: (questionId: number) => closeQuestion(questionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [TEACHER_QUESTIONS_KEY] })
    },
  })

  return {
    questions,
    isLoading,
    error,
    createQuestion: createMutation.mutateAsync,
    closeQuestion: closeMutation.mutateAsync,
    isCreating: computed(() => createMutation.isPending.value),
    isClosing: computed(() => closeMutation.isPending.value),
  }
}
