import { create } from 'zustand'
import type { Conversation, Channel } from '@/types'

interface InboxState {
  // Filters
  selectedChannel: Channel | 'ALL'
  showUnreadOnly: boolean
  showArchived: boolean
  showStarredOnly: boolean
  searchQuery: string
  
  // Selected conversation
  selectedConversationId: string | null
  
  // Actions
  setSelectedChannel: (channel: Channel | 'ALL') => void
  setShowUnreadOnly: (show: boolean) => void
  setShowArchived: (show: boolean) => void
  setShowStarredOnly: (show: boolean) => void
  setSearchQuery: (query: string) => void
  setSelectedConversationId: (id: string | null) => void
  resetFilters: () => void
}

export const useInboxStore = create<InboxState>((set) => ({
  // Initial filter state
  selectedChannel: 'ALL',
  showUnreadOnly: false,
  showArchived: false,
  showStarredOnly: false,
  searchQuery: '',
  selectedConversationId: null,

  // Actions
  setSelectedChannel: (channel) => set({ selectedChannel: channel }),
  setShowUnreadOnly: (show) => set({ showUnreadOnly: show }),
  setShowArchived: (show) => set({ showArchived: show }),
  setShowStarredOnly: (show) => set({ showStarredOnly: show }),
  setSearchQuery: (query) => set({ searchQuery: query }),
  setSelectedConversationId: (id) => set({ selectedConversationId: id }),
  
  resetFilters: () => set({
    selectedChannel: 'ALL',
    showUnreadOnly: false,
    showArchived: false,
    showStarredOnly: false,
    searchQuery: '',
  }),
}))
