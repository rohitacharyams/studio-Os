import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import type { Conversation, Message } from '@/types'
import {
  ArrowLeft,
  Star,
  Archive,
  Send,
  Sparkles,
  User,
  Mail,
  Phone,
  MessageCircle,
  Instagram
} from 'lucide-react'
import { format } from 'date-fns'
import clsx from 'clsx'
import toast from 'react-hot-toast'

const channelIcons = {
  EMAIL: Mail,
  WHATSAPP: MessageCircle,
  INSTAGRAM: Instagram,
}

export default function ConversationPage() {
  const { conversationId } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [newMessage, setNewMessage] = useState('')
  const [isGeneratingAI, setIsGeneratingAI] = useState(false)

  // Fetch conversation with messages
  const { data: conversationData, isLoading } = useQuery({
    queryKey: ['conversation', conversationId],
    queryFn: async () => {
      const response = await api.get(`/conversations/${conversationId}`)
      return response.data.conversation as Conversation
    },
    enabled: !!conversationId,
  })

  // Send message mutation
  const sendMessageMutation = useMutation({
    mutationFn: async (content: string) => {
      const response = await api.post(`/messages/${conversationId}`, { content })
      return response.data.message
    },
    onSuccess: () => {
      setNewMessage('')
      queryClient.invalidateQueries({ queryKey: ['conversation', conversationId] })
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
      toast.success('Message sent!')
    },
    onError: () => {
      toast.error('Failed to send message')
    },
  })

  // Update conversation mutation
  const updateConversationMutation = useMutation({
    mutationFn: async (data: Partial<Conversation>) => {
      const response = await api.put(`/conversations/${conversationId}`, data)
      return response.data.conversation
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversation', conversationId] })
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
    },
  })

  // Generate AI draft
  const generateAIDraft = async () => {
    setIsGeneratingAI(true)
    try {
      const response = await api.post('/ai/draft-reply', {
        conversation_id: conversationId,
        tone: 'friendly',
      })
      setNewMessage(response.data.draft)
      toast.success('AI draft generated!')
    } catch {
      toast.error('Failed to generate AI draft')
    } finally {
      setIsGeneratingAI(false)
    }
  }

  const handleSend = () => {
    if (!newMessage.trim()) return
    sendMessageMutation.mutate(newMessage)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
      </div>
    )
  }

  if (!conversationData) {
    return (
      <div className="flex flex-col items-center justify-center h-screen text-gray-500">
        <p>Conversation not found</p>
        <button
          onClick={() => navigate('/inbox')}
          className="mt-4 text-primary-600 hover:text-primary-700"
        >
          Back to Inbox
        </button>
      </div>
    )
  }

  const conversation = conversationData
  const contact = conversation.contact
  const messages = conversation.messages || []
  const ChannelIcon = channelIcons[conversation.channel]

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <header className="flex-shrink-0 bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/inbox')}
              className="p-2 -ml-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center">
                <User className="w-5 h-5 text-gray-500" />
              </div>
              <div>
                <h1 className="font-semibold text-gray-900">
                  {contact?.name || contact?.email || contact?.phone || 'Unknown'}
                </h1>
                <div className="flex items-center gap-2 text-sm text-gray-500">
                  <ChannelIcon className="w-4 h-4" />
                  <span>{conversation.channel}</span>
                  {conversation.subject && (
                    <>
                      <span>•</span>
                      <span className="truncate max-w-[200px]">{conversation.subject}</span>
                    </>
                  )}
                </div>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => updateConversationMutation.mutate({ is_starred: !conversation.is_starred })}
              className={clsx(
                'p-2 rounded-lg transition-colors',
                conversation.is_starred
                  ? 'text-yellow-500 hover:bg-yellow-50'
                  : 'text-gray-400 hover:bg-gray-100 hover:text-gray-600'
              )}
            >
              <Star className={clsx('w-5 h-5', conversation.is_starred && 'fill-yellow-500')} />
            </button>
            <button
              onClick={() => {
                updateConversationMutation.mutate({ is_archived: !conversation.is_archived })
                if (!conversation.is_archived) {
                  toast.success('Conversation archived')
                  navigate('/inbox')
                }
              }}
              className="p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-600 rounded-lg transition-colors"
            >
              <Archive className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Contact info */}
        {contact && (
          <div className="mt-4 flex flex-wrap gap-4 text-sm text-gray-600">
            {contact.email && (
              <div className="flex items-center gap-1">
                <Mail className="w-4 h-4" />
                <span>{contact.email}</span>
              </div>
            )}
            {contact.phone && (
              <div className="flex items-center gap-1">
                <Phone className="w-4 h-4" />
                <span>{contact.phone}</span>
              </div>
            )}
            <div className="flex items-center gap-1">
              <span className="px-2 py-0.5 bg-gray-100 rounded text-xs font-medium">
                {contact.lead_status?.replace('_', ' ')}
              </span>
            </div>
          </div>
        )}
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4 bg-gray-50">
        {messages.map((message: Message) => (
          <div
            key={message.id}
            className={clsx(
              'flex',
              message.direction === 'OUTBOUND' ? 'justify-end' : 'justify-start'
            )}
          >
            <div
              className={clsx(
                'max-w-[70%] px-4 py-3 rounded-2xl',
                message.direction === 'OUTBOUND'
                  ? 'bg-primary-500 text-white rounded-br-sm'
                  : 'bg-white text-gray-900 rounded-bl-sm shadow-sm'
              )}
            >
              <p className="whitespace-pre-wrap">{message.content}</p>
              <div
                className={clsx(
                  'flex items-center gap-2 mt-1 text-xs',
                  message.direction === 'OUTBOUND' ? 'text-primary-100' : 'text-gray-400'
                )}
              >
                <span>
                  {format(new Date(message.created_at), 'MMM d, h:mm a')}
                </span>
                {message.is_ai_generated && (
                  <span className="flex items-center gap-1">
                    <Sparkles className="w-3 h-3" />
                    AI
                  </span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Message input */}
      <div className="flex-shrink-0 bg-white border-t border-gray-200 p-4">
        <div className="flex items-end gap-3">
          <div className="flex-1">
            <textarea
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type your message..."
              rows={3}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
            />
          </div>
          <div className="flex flex-col gap-2">
            <button
              onClick={generateAIDraft}
              disabled={isGeneratingAI}
              className="p-3 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
              title="Generate AI draft"
            >
              {isGeneratingAI ? (
                <div className="w-5 h-5 border-2 border-gray-400 border-t-transparent rounded-full animate-spin" />
              ) : (
                <Sparkles className="w-5 h-5" />
              )}
            </button>
            <button
              onClick={handleSend}
              disabled={!newMessage.trim() || sendMessageMutation.isPending}
              className="p-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {sendMessageMutation.isPending ? (
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
