// Types for Studio OS frontend

export interface User {
  id: string
  email: string
  name: string
  role: 'owner' | 'admin' | 'staff'
  is_active: boolean
  created_at: string
  last_login: string | null
  studio?: Studio
}

export interface Studio {
  id: string
  name: string
  email: string
  phone: string | null
  address: string | null
  timezone: string
  created_at: string
  updated_at: string
}

export type Channel = 'EMAIL' | 'WHATSAPP' | 'INSTAGRAM'

export type LeadStatus = 'NEW' | 'CONTACTED' | 'QUALIFIED' | 'TRIAL_SCHEDULED' | 'CONVERTED' | 'LOST'

export interface Contact {
  id: string
  studio_id: string
  name: string | null
  email: string | null
  phone: string | null
  instagram_handle: string | null
  lead_status: LeadStatus
  lead_source: string | null
  notes: string | null
  tags: string[]
  created_at: string
  updated_at: string
  conversations?: Conversation[]
}

export interface Conversation {
  id: string
  studio_id: string
  contact_id: string
  channel: Channel
  subject: string | null
  is_unread: boolean
  is_archived: boolean
  is_starred: boolean
  last_message_at: string | null
  created_at: string
  contact?: Contact
  messages?: Message[]
}

export interface Message {
  id: string
  conversation_id: string
  sender_id: string | null
  direction: 'INBOUND' | 'OUTBOUND'
  content: string
  content_html: string | null
  is_read: boolean
  is_ai_generated: boolean
  attachments: Attachment[]
  created_at: string
  sent_at: string | null
}

export interface Attachment {
  url: string
  filename?: string
  content_type: string
  size?: number
}

export interface MessageTemplate {
  id: string
  studio_id: string
  name: string
  category: string | null
  subject: string | null
  content: string
  variables: string[]
  channels: Channel[]
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface StudioKnowledge {
  id: string
  studio_id: string
  category: string
  title: string
  content: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface LeadStatusHistory {
  id: string
  contact_id: string
  from_status: LeadStatus | null
  to_status: LeadStatus
  changed_by_id: string | null
  notes: string | null
  created_at: string
}

export interface AnalyticsOverview {
  total_contacts: number
  unread_conversations: number
  messages_received: number
  messages_sent: number
  new_leads: number
  leads_converted: number
  avg_response_time_minutes: number | null
}

export interface DailyAnalytics {
  id: string
  studio_id: string
  date: string
  messages_received: number
  messages_sent: number
  new_leads: number
  leads_converted: number
  channel_breakdown: Record<Channel, number>
  avg_response_time_minutes: number | null
}

// API Response types
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  limit: number
  total_pages: number
}

export interface ConversationStats {
  total: number
  unread: number
  starred: number
  by_channel: Record<Channel, number>
}
