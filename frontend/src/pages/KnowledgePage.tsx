import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import type { StudioKnowledge } from '@/types'
import { Plus, Edit, Trash2, X, BookOpen, FileText, HelpCircle, DollarSign, Calendar } from 'lucide-react'
import clsx from 'clsx'
import toast from 'react-hot-toast'

const categoryIcons: Record<string, React.ElementType> = {
  pricing: DollarSign,
  schedule: Calendar,
  policies: FileText,
  faq: HelpCircle,
}

const categoryColors: Record<string, string> = {
  pricing: 'bg-green-100 text-green-600',
  schedule: 'bg-blue-100 text-blue-600',
  policies: 'bg-yellow-100 text-yellow-600',
  faq: 'bg-purple-100 text-purple-600',
}

export default function KnowledgePage() {
  const queryClient = useQueryClient()
  const [showModal, setShowModal] = useState(false)
  const [editingItem, setEditingItem] = useState<StudioKnowledge | null>(null)
  const [categoryFilter, setCategoryFilter] = useState<string>('ALL')

  // Fetch knowledge items
  const { data: knowledgeData, isLoading } = useQuery({
    queryKey: ['knowledge', categoryFilter],
    queryFn: async () => {
      const params: Record<string, string> = {}
      if (categoryFilter !== 'ALL') params.category = categoryFilter

      const response = await api.get('/studio/knowledge', { params })
      return response.data
    },
  })

  // Delete item mutation
  const deleteItemMutation = useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/studio/knowledge/${id}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge'] })
      toast.success('Knowledge item deleted')
    },
    onError: () => {
      toast.error('Failed to delete item')
    },
  })

  const items: StudioKnowledge[] = knowledgeData?.knowledge || []

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Knowledge Base</h1>
          <p className="text-sm text-gray-500">Information for AI-powered responses</p>
        </div>
        <button
          onClick={() => {
            setEditingItem(null)
            setShowModal(true)
          }}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
        >
          <Plus className="w-4 h-4" />
          Add Knowledge
        </button>
      </div>

      {/* Info banner */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <div className="flex gap-3">
          <BookOpen className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-medium text-blue-900">How it works</h3>
            <p className="text-sm text-blue-700 mt-1">
              Add information about your studio (pricing, schedule, policies, FAQs) and our AI will use
              it to generate accurate, contextual responses to customer inquiries.
            </p>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4 mb-6">
        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
          className="px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
        >
          <option value="ALL">All Categories</option>
          <option value="pricing">Pricing</option>
          <option value="schedule">Schedule</option>
          <option value="policies">Policies</option>
          <option value="faq">FAQ</option>
        </select>
      </div>

      {/* Knowledge items */}
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
        </div>
      ) : items.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-64 text-gray-500 bg-white rounded-lg border border-gray-200">
          <BookOpen className="w-12 h-12 mb-4 text-gray-300" />
          <p className="text-lg font-medium">No knowledge items yet</p>
          <p className="text-sm">Add studio information to help AI generate better responses</p>
        </div>
      ) : (
        <div className="space-y-4">
          {items.map((item) => {
            const Icon = categoryIcons[item.category] || FileText
            const color = categoryColors[item.category] || 'bg-gray-100 text-gray-600'

            return (
              <div
                key={item.id}
                className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    <div className={clsx('p-2 rounded-lg', color)}>
                      <Icon className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-medium text-gray-900">{item.title}</h3>
                        {!item.is_active && (
                          <span className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded">
                            Inactive
                          </span>
                        )}
                      </div>
                      <span className="text-xs text-gray-500 capitalize">{item.category}</span>
                      <p className="text-sm text-gray-600 mt-2 whitespace-pre-wrap">
                        {item.content}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => {
                        setEditingItem(item)
                        setShowModal(true)
                      }}
                      className="p-1 text-gray-400 hover:text-gray-600"
                    >
                      <Edit className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => {
                        if (confirm('Delete this knowledge item?')) {
                          deleteItemMutation.mutate(item.id)
                        }
                      }}
                      className="p-1 text-gray-400 hover:text-red-600"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Create/Edit Modal */}
      {showModal && (
        <KnowledgeModal
          item={editingItem}
          onClose={() => {
            setShowModal(false)
            setEditingItem(null)
          }}
        />
      )}
    </div>
  )
}

function KnowledgeModal({
  item,
  onClose,
}: {
  item: StudioKnowledge | null
  onClose: () => void
}) {
  const queryClient = useQueryClient()
  const [formData, setFormData] = useState({
    category: item?.category || 'faq',
    title: item?.title || '',
    content: item?.content || '',
    is_active: item?.is_active ?? true,
  })

  const mutation = useMutation({
    mutationFn: async (data: typeof formData) => {
      if (item) {
        const response = await api.put(`/studio/knowledge/${item.id}`, data)
        return response.data.knowledge
      } else {
        const response = await api.post('/studio/knowledge', data)
        return response.data.knowledge
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge'] })
      toast.success(item ? 'Knowledge item updated' : 'Knowledge item created')
      onClose()
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error || 'Failed to save')
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    mutation.mutate(formData)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">
            {item ? 'Edit Knowledge' : 'Add Knowledge'}
          </h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Category *</label>
            <select
              required
              value={formData.category}
              onChange={(e) => setFormData({ ...formData, category: e.target.value })}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="pricing">Pricing</option>
              <option value="schedule">Schedule</option>
              <option value="policies">Policies</option>
              <option value="faq">FAQ</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Title *</label>
            <input
              type="text"
              required
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary-500 focus:border-primary-500"
              placeholder="e.g., Monthly Membership Pricing"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Content *</label>
            <textarea
              required
              rows={8}
              value={formData.content}
              onChange={(e) => setFormData({ ...formData, content: e.target.value })}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary-500 focus:border-primary-500"
              placeholder="Add detailed information that will help the AI answer customer questions..."
            />
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="is_active"
              checked={formData.is_active}
              onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
              className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
            />
            <label htmlFor="is_active" className="text-sm text-gray-700">
              Active (include in AI responses)
            </label>
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={mutation.isPending}
              className="px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 disabled:opacity-50"
            >
              {mutation.isPending ? 'Saving...' : item ? 'Update' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
