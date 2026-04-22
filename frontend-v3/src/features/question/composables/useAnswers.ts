import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { computed, type Ref } from 'vue'
import {
  getAnswers,
  createAnswer,
  updateAnswer,
  deleteAnswer,
  replyAnswer,
  starAnswer,
} from '@/api/question'
import type {
  CreateAnswerRequest,
  UpdateAnswerRequest,
  CreateReplyRequest,
} from '@/types/question'

const ANSWERS_KEY = 'answers'

export function useAnswers(questionId: Ref<number>) {
  const queryClient = useQueryClient()

  const queryKey = computed(() => [ANSWERS_KEY, questionId.value])

  const { data: answers, isLoading, error } = useQuery({
    queryKey,
    queryFn: () => getAnswers(questionId.value),
    enabled: computed(() => questionId.value > 0),
  })

  const createMutation = useMutation({
    mutationFn: (data: CreateAnswerRequest) => createAnswer(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [ANSWERS_KEY] })
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateAnswerRequest }) => updateAnswer(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [ANSWERS_KEY] })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (answerId: number) => deleteAnswer(answerId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [ANSWERS_KEY] })
    },
  })

  const replyMutation = useMutation({
    mutationFn: ({ answerId, data }: { answerId: number; data: CreateReplyRequest }) =>
      replyAnswer(answerId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [ANSWERS_KEY] })
    },
  })

  const starMutation = useMutation({
    mutationFn: ({ answerId, starred }: { answerId: number; starred: boolean }) =>
      starAnswer(answerId, starred),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [ANSWERS_KEY] })
    },
  })

  return {
    answers,
    isLoading,
    error,
    createAnswer: createMutation.mutateAsync,
    updateAnswer: updateMutation.mutateAsync,
    deleteAnswer: deleteMutation.mutateAsync,
    replyAnswer: replyMutation.mutateAsync,
    starAnswer: starMutation.mutateAsync,
    isCreating: computed(() => createMutation.isPending.value),
    isUpdating: computed(() => updateMutation.isPending.value),
    isDeleting: computed(() => deleteMutation.isPending.value),
    isReplying: computed(() => replyMutation.isPending.value),
    isStarring: computed(() => starMutation.isPending.value),
  }
}
