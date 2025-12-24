import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'
import type { AnalyticsOverview, DailyAnalytics } from '@/types'
import {
  MessageSquare,
  Users,
  TrendingUp,
  Clock,
  Mail,
  MessageCircle,
  Instagram
} from 'lucide-react'
import { format, subDays } from 'date-fns'
import clsx from 'clsx'

export default function AnalyticsPage() {
  // Fetch dashboard analytics
  const { data, isLoading } = useQuery({
    queryKey: ['analytics-dashboard'],
    queryFn: async () => {
      const response = await api.get('/analytics/dashboard', { params: { days: 30 } })
      return response.data
    },
  })

  // Fetch lead analytics
  const { data: leadData } = useQuery({
    queryKey: ['analytics-leads'],
    queryFn: async () => {
      const response = await api.get('/analytics/leads')
      return response.data
    },
  })

  // Fetch channel analytics
  const { data: channelData } = useQuery({
    queryKey: ['analytics-channels'],
    queryFn: async () => {
      const response = await api.get('/analytics/channels')
      return response.data
    },
  })

  const overview: AnalyticsOverview = data?.overview || {}
  const daily: DailyAnalytics[] = data?.daily || []

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
      </div>
    )
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
        <p className="text-sm text-gray-500">Last 30 days overview</p>
      </div>

      {/* Stats cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard
          title="Total Contacts"
          value={overview.total_contacts || 0}
          icon={Users}
          color="bg-blue-500"
        />
        <StatCard
          title="Messages Received"
          value={overview.messages_received || 0}
          icon={MessageSquare}
          color="bg-green-500"
        />
        <StatCard
          title="New Leads"
          value={overview.new_leads || 0}
          icon={TrendingUp}
          color="bg-purple-500"
        />
        <StatCard
          title="Avg Response Time"
          value={overview.avg_response_time_minutes
            ? `${Math.round(overview.avg_response_time_minutes)}m`
            : 'N/A'}
          icon={Clock}
          color="bg-orange-500"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Lead Status Distribution */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Lead Status Distribution</h3>
          {leadData?.status_distribution ? (
            <div className="space-y-3">
              {Object.entries(leadData.status_distribution).map(([status, count]) => {
                const total = Object.values(leadData.status_distribution as Record<string, number>)
                  .reduce((a, b) => a + b, 0)
                const percentage = total > 0 ? ((count as number) / total) * 100 : 0

                return (
                  <div key={status}>
                    <div className="flex items-center justify-between text-sm mb-1">
                      <span className="text-gray-600">{status.replace('_', ' ')}</span>
                      <span className="font-medium">{count as number}</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-primary-500 h-2 rounded-full transition-all"
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          ) : (
            <p className="text-gray-500 text-center py-8">No lead data available</p>
          )}
          
          {leadData && (
            <div className="mt-6 pt-4 border-t border-gray-200">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Conversion Rate</span>
                <span className="text-lg font-semibold text-primary-600">
                  {leadData.conversion_rate || 0}%
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Channel Distribution */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Messages by Channel</h3>
          {channelData?.messages_by_channel ? (
            <div className="space-y-4">
              {[
                { channel: 'EMAIL', icon: Mail, color: 'bg-blue-500' },
                { channel: 'WHATSAPP', icon: MessageCircle, color: 'bg-green-500' },
                { channel: 'INSTAGRAM', icon: Instagram, color: 'bg-pink-500' },
              ].map(({ channel, icon: Icon, color }) => {
                const count = channelData.messages_by_channel[channel] || 0
                const total = Object.values(channelData.messages_by_channel as Record<string, number>)
                  .reduce((a, b) => a + b, 0)
                const percentage = total > 0 ? (count / total) * 100 : 0

                return (
                  <div key={channel} className="flex items-center gap-4">
                    <div className={clsx('p-2 rounded-lg', color, 'bg-opacity-10')}>
                      <Icon className={clsx('w-5 h-5', color.replace('bg-', 'text-'))} />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between text-sm mb-1">
                        <span className="text-gray-600">{channel}</span>
                        <span className="font-medium">{count}</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className={clsx('h-2 rounded-full transition-all', color)}
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          ) : (
            <p className="text-gray-500 text-center py-8">No channel data available</p>
          )}
        </div>

        {/* Daily Activity */}
        <div className="bg-white rounded-lg border border-gray-200 p-6 lg:col-span-2">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Daily Activity</h3>
          {daily.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left text-xs font-medium text-gray-500 uppercase py-2">Date</th>
                    <th className="text-right text-xs font-medium text-gray-500 uppercase py-2">Received</th>
                    <th className="text-right text-xs font-medium text-gray-500 uppercase py-2">Sent</th>
                    <th className="text-right text-xs font-medium text-gray-500 uppercase py-2">New Leads</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {daily.slice(-14).reverse().map((day) => (
                    <tr key={day.date}>
                      <td className="py-3 text-sm text-gray-900">
                        {format(new Date(day.date), 'MMM d, yyyy')}
                      </td>
                      <td className="py-3 text-sm text-right text-gray-600">
                        {day.messages_received}
                      </td>
                      <td className="py-3 text-sm text-right text-gray-600">
                        {day.messages_sent}
                      </td>
                      <td className="py-3 text-sm text-right text-gray-600">
                        {day.new_leads}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-gray-500 text-center py-8">No daily data available yet</p>
          )}
        </div>
      </div>
    </div>
  )
}

function StatCard({
  title,
  value,
  icon: Icon,
  color,
}: {
  title: string
  value: number | string
  icon: React.ElementType
  color: string
}) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="flex items-center gap-4">
        <div className={clsx('p-3 rounded-lg', color, 'bg-opacity-10')}>
          <Icon className={clsx('w-6 h-6', color.replace('bg-', 'text-'))} />
        </div>
        <div>
          <p className="text-sm text-gray-500">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
        </div>
      </div>
    </div>
  )
}
