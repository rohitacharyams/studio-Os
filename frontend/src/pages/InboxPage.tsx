import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { useInboxStore } from '@/store/inboxStore'
import api from '@/lib/api'
import type { Conversation, ConversationStats, Channel } from '@/types'
import { Mail, MessageCircle, Instagram, Star, Archive, Search, Filter } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import clsx from 'clsx'

const channelIcons: Record<Channel, React.ElementType> = {
  EMAIL: Mail,
  WHATSAPP: MessageCircle,
  INSTAGRAM: Instagram,
}

const channelColors: Record<Channel, string> = {
  EMAIL: 'bg-blue-100 text-blue-600',
  WHATSAPP: 'bg-green-100 text-green-600',
  INSTAGRAM: 'bg-pink-100 text-pink-600',
}

export default function InboxPage() {
  const navigate = useNavigate()
  const {
    selectedChannel,
    showUnreadOnly,
    showArchived,
    showStarredOnly,
    searchQuery,
    setSelectedChannel,
    setShowUnreadOnly,
    setShowArchived,
    setShowStarredOnly,
    setSearchQuery,
  } = useInboxStore()

  // Fetch conversations
  const { data: conversationsData, isLoading } = useQuery({
    queryKey: ['conversations', selectedChannel, showUnreadOnly, showArchived, showStarredOnly, searchQuery],
    queryFn: async () => {
      const params: Record<string, string> = {}
      if (selectedChannel !== 'ALL') params.channel = selectedChannel
      if (showUnreadOnly) params.is_unread = 'true'
      params.is_archived = showArchived ? 'true' : 'false'
      if (showStarredOnly) params.is_starred = 'true'
      if (searchQuery) params.search = searchQuery

      const response = await api.get('/conversations', { params })
      return response.data
    },
  })

  // Fetch stats
  const { data: statsData } = useQuery({
    queryKey: ['conversation-stats'],
    queryFn: async () => {
      const response = await api.get('/conversations/stats')
      return response.data.stats as ConversationStats
    },
  })

  const conversations: Conversation[] = conversationsData?.conversations || []
  const stats = statsData

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <header className="flex-shrink-0 bg-white border-b border-gray-200">
        <div className="px-6 py-4">
          <h1 className="text-2xl font-bold text-gray-900">Inbox</h1>
          <p className="text-sm text-gray-500">
            {stats?.unread || 0} unread conversations
          </p>
        </div>

        {/* Filters */}
        <div className="px-6 pb-4 flex flex-wrap items-center gap-3">
          {/* Search */}
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search conversations..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>

          {/* Channel filter */}
          <select
            value={selectedChannel}
            onChange={(e) => setSelectedChannel(e.target.value as Channel | 'ALL')}
            className="px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="ALL">All Channels</option>
            <option value="EMAIL">Email ({stats?.by_channel?.EMAIL || 0})</option>
            <option value="WHATSAPP">WhatsApp ({stats?.by_channel?.WHATSAPP || 0})</option>
            <option value="INSTAGRAM">Instagram ({stats?.by_channel?.INSTAGRAM || 0})</option>
          </select>

          {/* Quick filters */}
          <button
            onClick={() => setShowUnreadOnly(!showUnreadOnly)}
            className={clsx(
              'px-3 py-2 text-sm rounded-lg border transition-colors',
              showUnreadOnly
                ? 'bg-primary-50 border-primary-200 text-primary-700'
                : 'border-gray-300 text-gray-700 hover:bg-gray-50'
            )}
          >
            Unread
          </button>
          <button
            onClick={() => setShowStarredOnly(!showStarredOnly)}
            className={clsx(
              'px-3 py-2 text-sm rounded-lg border transition-colors flex items-center gap-1',
              showStarredOnly
                ? 'bg-yellow-50 border-yellow-200 text-yellow-700'
                : 'border-gray-300 text-gray-700 hover:bg-gray-50'
            )}
          >
            <Star className="w-4 h-4" />
            Starred
          </button>
          <button
            onClick={() => setShowArchived(!showArchived)}
            className={clsx(
              'px-3 py-2 text-sm rounded-lg border transition-colors flex items-center gap-1',
              showArchived
                ? 'bg-gray-100 border-gray-300 text-gray-700'
                : 'border-gray-300 text-gray-700 hover:bg-gray-50'
            )}
          >
            <Archive className="w-4 h-4" />
            Archived
          </button>
        </div>
      </header>

      {/* Conversation list */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
          </div>
        ) : conversations.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-gray-500">
            <Mail className="w-12 h-12 mb-4 text-gray-300" />
            <p className="text-lg font-medium">No conversations found</p>
            <p className="text-sm">Messages will appear here when you receive them</p>
          </div>
        ) : (
          <ul className="divide-y divide-gray-100">
            {conversations.map((conversation) => {
              const ChannelIcon = channelIcons[conversation.channel]
              const contact = conversation.contact

              return (
                <li key={conversation.id}>
                  <button
                    onClick={() => navigate(`/inbox/${conversation.id}`)}
                    className={clsx(
                      'w-full px-6 py-4 flex items-start gap-4 hover:bg-gray-50 transition-colors text-left',
                      conversation.is_unread && 'bg-primary-50/50'
                    )}
                  >
                    {/* Channel icon */}
                    <div className={clsx('p-2 rounded-lg', channelColors[conversation.channel])}>
                      <ChannelIcon className="w-5 h-5" />
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2">
                        <span className={clsx(
                          'font-medium truncate',
                          conversation.is_unread ? 'text-gray-900' : 'text-gray-700'
                        )}>
                          {contact?.name || contact?.email || contact?.phone || 'Unknown'}
                        </span>
                        <div className="flex items-center gap-2 flex-shrink-0">
                          {conversation.is_starred && (
                            <Star className="w-4 h-4 text-yellow-500 fill-yellow-500" />
                          )}
                          <span className="text-xs text-gray-500">
                            {conversation.last_message_at
                              ? formatDistanceToNow(new Date(conversation.last_message_at), { addSuffix: true })
                              : 'No messages'}
                          </span>
                        </div>
                      </div>
                      {conversation.subject && (
                        <p className={clsx(
                          'text-sm truncate',
                          conversation.is_unread ? 'text-gray-700 font-medium' : 'text-gray-500'
                        )}>
                          {conversation.subject}
                        </p>
                      )}
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-xs text-gray-400">
                          {contact?.lead_status?.replace('_', ' ')}
                        </span>
                        {conversation.is_unread && (
                          <span className="w-2 h-2 bg-primary-500 rounded-full" />
                        )}
                      </div>
                    </div>
                  </button>
                </li>
              )
            })}
          </ul>
        )}
      </div>
    </div>
  )
}
