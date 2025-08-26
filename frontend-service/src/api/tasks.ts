import request from '../utils/request'
import type { Task, TaskCreateParams, TaskListResponse, TaskType } from '../types/task'

export interface TaskListParams {
  page?: number
  size?: number
  status?: string
  task_type?: TaskType
}

export interface TaskResultListResponse {
  items: any[]
  total: number
  page: number
  size: number
  pages: number
}

export interface TaskResultParams {
  page?: number
  size?: number
  skip?: number
  limit?: number
}

// 获取任务列表
export const getTasks = async (params: TaskListParams = {}): Promise<TaskListResponse> => {
  const response = await request.get<TaskListResponse>('/tasks', { params })
  return response.data
}

// 获取任务详情
export const getTaskById = async (id: string): Promise<Task> => {
  const response = await request.get<Task>(`/tasks/${id}`)
  return response.data
}

// 获取任务结果
export const getTaskResults = async (id: string, params: TaskResultParams = {}): Promise<TaskResultListResponse> => {
  const response = await request.get<TaskResultListResponse>(`/tasks/${id}/results`, { params })
  return response.data
}

// 创建任务
export const createTask = async (data: TaskCreateParams): Promise<Task> => {
  const response = await request.post<Task>('/tasks', data)
  return response.data
}

// 更新任务
export const updateTask = async (id: string, data: Partial<TaskCreateParams>): Promise<Task> => {
  const response = await request.put<Task>(`/tasks/${id}`, data)
  return response.data
}

// 删除任务
export const deleteTask = async (id: string): Promise<void> => {
  await request.delete(`/tasks/${id}`)
}

// 启动任务
export const startTask = async (id: string): Promise<Task> => {
  const response = await request.post<Task>(`/tasks/${id}/start`)
  return response.data
}

// 停止任务
export const stopTask = async (id: string): Promise<Task> => {
  const response = await request.post<Task>(`/tasks/${id}/stop`)
  return response.data
}

// 重启任务
export const restartTask = async (id: string): Promise<Task> => {
  const response = await request.post<Task>(`/tasks/${id}/restart`)
  return response.data
}

// 导出任务结果
export const exportTaskResults = async (id: string, format: 'json' | 'csv' = 'json'): Promise<Blob> => {
  const response = await request.get(`/tasks/${id}/export`, {
    params: { format },
    responseType: 'blob'
  })
  return response.data
} 