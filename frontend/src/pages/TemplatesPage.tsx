import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import type { MessageTemplate } from '@/types'
import { Plus, Edit, Trash2, X, Copy, Mail, MessageCircle, Download, Loader2 } from 'lucide-react'
import clsx from 'clsx'
import toast from 'react-hot-toast'

export default function TemplatesPage() {
  const queryClient = useQueryClient()
  const [showModal, setShowModal] = useState(false)
  const [editingTemplate, setEditingTemplate] = useState<MessageTemplate | null>(null)
  const [categoryFilter, setCategoryFilter] = useState<string>('ALL')

  // Fetch templates
  const { data: templatesData, isLoading } = useQuery({
    queryKey: ['templates', categoryFilter],
    queryFn: async () => {
      const params: Record<string, string> = {}
      if (categoryFilter !== 'ALL') params.category = categoryFilter

      const response = await api.get('/templates', { params })
      return response.data
    },
  })

  // Load default templates mutation
  const loadDefaultsMutation = useMutation({
    mutationFn: async () => {
      const response = await api.post('/templates/load-defaults', {})
      return response.data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['templates'] })
      toast.success(`Loaded ${data.created} templates${data.skipped > 0 ? ` (${data.skipped} already existed)` : ''}`)
    },
    onError: () => {
      toast.error('Failed to load default templates')
    },
  })

  // Delete template mutation
  const deleteTemplateMutation = useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/templates/${id}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] })
      toast.success('Template deleted')
    },
    onError: () => {
      toast.error('Failed to delete template')
    },
  })

  const templates: MessageTemplate[] = templatesData?.templates || []

  // Get unique categories
  const categories = [...new Set(templates.map((t) => t.category).filter(Boolean))]

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Message Templates</h1>
          <p className="text-sm text-gray-500">Reusable templates for quick responses</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => loadDefaultsMutation.mutate()}
            disabled={loadDefaultsMutation.isPending}
            className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors disabled:opacity-50"
          >
            {loadDefaultsMutation.isPending ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Download className="w-4 h-4" />
            )}
            Load Defaults
          </button>
          <button
            onClick={() => {
              setEditingTemplate(null)
              setShowModal(true)
            }}
            className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Create Template
          </button>
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
          {categories.map((cat) => cat && (
            <option key={cat} value={cat}>{cat}</option>
          ))}
        </select>
      </div>

      {/* Templates grid */}
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
        </div>
      ) : templates.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-64 text-gray-500 bg-white rounded-lg border border-gray-200">
          <p className="text-lg font-medium">No templates yet</p>
          <p className="text-sm">Create your first template to get started</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {templates.map((template) => (
            <div
              key={template.id}
              className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between mb-2">
                <div>
                  <h3 className="font-medium text-gray-900">{template.name}</h3>
                  {template.category && (
                    <span className="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded">
                      {template.category}
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(template.content)
                      toast.success('Template copied!')
                    }}
                    className="p-1 text-gray-400 hover:text-gray-600"
                    title="Copy content"
                  >
                    <Copy className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => {
                      setEditingTemplate(template)
                      setShowModal(true)
                    }}
                    className="p-1 text-gray-400 hover:text-gray-600"
                  >
                    <Edit className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => {
                      if (confirm('Delete this template?')) {
                        deleteTemplateMutation.mutate(template.id)
                      }
                    }}
                    className="p-1 text-gray-400 hover:text-red-600"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {template.subject && (
                <p className="text-sm text-gray-600 font-medium mb-1">
                  Subject: {template.subject}
                </p>
              )}

              <p className="text-sm text-gray-600 line-clamp-3 mb-3">
                {template.content}
              </p>

              <div className="flex items-center gap-2">
                {template.channels.includes('EMAIL') && (
                  <span className="flex items-center gap-1 text-xs text-blue-600 bg-blue-50 px-2 py-1 rounded">
                    <Mail className="w-3 h-3" />
                    Email
                  </span>
                )}
                {template.channels.includes('WHATSAPP') && (
                  <span className="flex items-center gap-1 text-xs text-green-600 bg-green-50 px-2 py-1 rounded">
                    <MessageCircle className="w-3 h-3" />
                    WhatsApp
                  </span>
                )}
              </div>

              {template.variables.length > 0 && (
                <div className="mt-2 text-xs text-gray-400">
                  Variables: {template.variables.map((v) => `{{${v}}}`).join(', ')}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Create/Edit Modal */}
      {showModal && (
        <TemplateModal
          template={editingTemplate}
          onClose={() => {
            setShowModal(false)
            setEditingTemplate(null)
          }}
        />
      )}
    </div>
  )
}

function TemplateModal({
  template,
  onClose,
}: {
  template: MessageTemplate | null
  onClose: () => void
}) {
  const queryClient = useQueryClient()
  const [formData, setFormData] = useState<{
    name: string;
    category: string;
    subject: string;
    content: string;
    channels: ('EMAIL' | 'WHATSAPP' | 'INSTAGRAM')[];
  }>({
    name: template?.name || '',
    category: template?.category || '',
    subject: template?.subject || '',
    content: template?.content || '',
    channels: template?.channels || ['EMAIL', 'WHATSAPP'],
  })

  const mutation = useMutation({
    mutationFn: async (data: typeof formData) => {
      if (template) {
        const response = await api.put(`/templates/${template.id}`, data)
        return response.data.template
      } else {
        const response = await api.post('/templates', data)
        return response.data.template
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] })
      toast.success(template ? 'Template updated' : 'Template created')
      onClose()
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error || 'Failed to save template')
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    mutation.mutate(formData)
  }

  const toggleChannel = (channel: 'EMAIL' | 'WHATSAPP' | 'INSTAGRAM') => {
    const channels = formData.channels.includes(channel)
      ? formData.channels.filter((c) => c !== channel)
      : [...formData.channels, channel]
    setFormData({ ...formData, channels })
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">
            {template ? 'Edit Template' : 'Create Template'}
          </h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Name *</label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary-500 focus:border-primary-500"
              placeholder="e.g., Welcome Message"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Category</label>
            <input
              type="text"
              value={formData.category}
              onChange={(e) => setFormData({ ...formData, category: e.target.value })}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary-500 focus:border-primary-500"
              placeholder="e.g., Welcome, Follow-up, Scheduling"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Subject (for emails)</label>
            <input
              type="text"
              value={formData.subject}
              onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary-500 focus:border-primary-500"
              placeholder="e.g., Welcome to {{studio_name}}!"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Content *</label>
            <textarea
              required
              rows={6}
              value={formData.content}
              onChange={(e) => setFormData({ ...formData, content: e.target.value })}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary-500 focus:border-primary-500"
              placeholder="Hi {{name}}, thank you for reaching out to {{studio_name}}..."
            />
            <p className="mt-1 text-xs text-gray-500">
              Use {'{{variable}}'} for dynamic content like {'{{name}}'}, {'{{studio_name}}'}
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Channels</label>
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={() => toggleChannel('EMAIL')}
                className={clsx(
                  'flex items-center gap-2 px-3 py-2 rounded-lg border transition-colors',
                  formData.channels.includes('EMAIL')
                    ? 'bg-blue-50 border-blue-200 text-blue-700'
                    : 'border-gray-300 text-gray-600'
                )}
              >
                <Mail className="w-4 h-4" />
                Email
              </button>
              <button
                type="button"
                onClick={() => toggleChannel('WHATSAPP')}
                className={clsx(
                  'flex items-center gap-2 px-3 py-2 rounded-lg border transition-colors',
                  formData.channels.includes('WHATSAPP')
                    ? 'bg-green-50 border-green-200 text-green-700'
                    : 'border-gray-300 text-gray-600'
                )}
              >
                <MessageCircle className="w-4 h-4" />
                WhatsApp
              </button>
            </div>
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
              {mutation.isPending ? 'Saving...' : template ? 'Update' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
