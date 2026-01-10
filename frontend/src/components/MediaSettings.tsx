import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuthStore } from '@/store/authStore'
import api from '@/lib/api'
import { Image, Video, Star, Plus, Trash2, X, Save } from 'lucide-react'
import toast from 'react-hot-toast'

export default function MediaSettings() {
  const queryClient = useQueryClient()
  const { studio } = useAuthStore()
  const [photos, setPhotos] = useState<string[]>(studio?.photos || [])
  const [videos, setVideos] = useState<string[]>(studio?.videos || [])
  const [testimonials, setTestimonials] = useState<Array<{name: string, text: string, rating: number}>>(
    studio?.testimonials || []
  )
  const [amenities, setAmenities] = useState<string[]>(studio?.amenities || [])
  const [socialLinks, setSocialLinks] = useState({
    instagram: studio?.social_links?.instagram || '',
    youtube: studio?.social_links?.youtube || '',
    facebook: studio?.social_links?.facebook || '',
  })
  const [newPhoto, setNewPhoto] = useState('')
  const [newVideo, setNewVideo] = useState('')
  const [newAmenity, setNewAmenity] = useState('')
  const [newTestimonial, setNewTestimonial] = useState({ name: '', text: '', rating: 5 })

  const mutation = useMutation({
    mutationFn: async (data: any) => {
      const response = await api.put('/studio', data)
      return response.data.studio
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['studio'] })
      toast.success('Media settings saved')
    },
    onError: () => {
      toast.error('Failed to save media settings')
    },
  })

  const handleSave = () => {
    mutation.mutate({
      photos,
      videos,
      testimonials,
      amenities,
      social_links: socialLinks,
    })
  }

  const addPhoto = () => {
    if (newPhoto && !photos.includes(newPhoto)) {
      setPhotos([...photos, newPhoto])
      setNewPhoto('')
    }
  }

  const addVideo = () => {
    if (newVideo && !videos.includes(newVideo)) {
      setVideos([...videos, newVideo])
      setNewVideo('')
    }
  }

  const addAmenity = () => {
    if (newAmenity && !amenities.includes(newAmenity)) {
      setAmenities([...amenities, newAmenity])
      setNewAmenity('')
    }
  }

  const addTestimonial = () => {
    if (newTestimonial.name && newTestimonial.text) {
      setTestimonials([...testimonials, newTestimonial])
      setNewTestimonial({ name: '', text: '', rating: 5 })
    }
  }

  return (
    <div className="max-w-2xl space-y-6">
      {/* Studio Photos */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center gap-2">
          <Image className="w-5 h-5 text-primary-600" />
          Studio Photos
        </h3>
        <p className="text-sm text-gray-500 mb-4">Add photos of your studio to showcase your space</p>
        
        <div className="flex gap-2 mb-4">
          <input
            type="url"
            value={newPhoto}
            onChange={(e) => setNewPhoto(e.target.value)}
            placeholder="Paste image URL"
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary-500 focus:border-primary-500"
          />
          <button type="button" onClick={addPhoto} className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700">
            <Plus className="w-4 h-4" />
          </button>
        </div>
        
        <div className="grid grid-cols-3 gap-3">
          {photos.map((url, idx) => (
            <div key={idx} className="relative group aspect-video">
              <img src={url} alt={`Studio ${idx + 1}`} className="w-full h-full object-cover rounded-lg" />
              <button
                onClick={() => setPhotos(photos.filter((_, i) => i !== idx))}
                className="absolute top-2 right-2 p-1 bg-red-500 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
              >
                <Trash2 className="w-3 h-3" />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Studio Videos */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center gap-2">
          <Video className="w-5 h-5 text-primary-600" />
          Videos
        </h3>
        
        <div className="flex gap-2 mb-4">
          <input
            type="url"
            value={newVideo}
            onChange={(e) => setNewVideo(e.target.value)}
            placeholder="Paste YouTube/Vimeo URL"
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary-500 focus:border-primary-500"
          />
          <button type="button" onClick={addVideo} className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700">
            <Plus className="w-4 h-4" />
          </button>
        </div>
        
        <div className="space-y-2">
          {videos.map((url, idx) => (
            <div key={idx} className="flex items-center gap-2 p-2 bg-gray-50 rounded-lg">
              <Video className="w-4 h-4 text-gray-400" />
              <span className="flex-1 text-sm text-gray-600 truncate">{url}</span>
              <button onClick={() => setVideos(videos.filter((_, i) => i !== idx))} className="text-red-500 hover:text-red-700">
                <X className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Testimonials */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center gap-2">
          <Star className="w-5 h-5 text-primary-600" />
          Student Testimonials
        </h3>
        
        <div className="space-y-3 mb-4">
          <input
            type="text"
            value={newTestimonial.name}
            onChange={(e) => setNewTestimonial({ ...newTestimonial, name: e.target.value })}
            placeholder="Student name"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary-500 focus:border-primary-500"
          />
          <textarea
            value={newTestimonial.text}
            onChange={(e) => setNewTestimonial({ ...newTestimonial, text: e.target.value })}
            placeholder="Their testimonial..."
            rows={2}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary-500 focus:border-primary-500"
          />
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1">
              {[1, 2, 3, 4, 5].map((star) => (
                <button
                  key={star}
                  type="button"
                  onClick={() => setNewTestimonial({ ...newTestimonial, rating: star })}
                  className={`w-6 h-6 ${star <= newTestimonial.rating ? 'text-yellow-400' : 'text-gray-300'}`}
                >
                  ★
                </button>
              ))}
            </div>
            <button type="button" onClick={addTestimonial} className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm">
              Add Testimonial
            </button>
          </div>
        </div>
        
        <div className="space-y-3">
          {testimonials.map((t, idx) => (
            <div key={idx} className="p-3 bg-gray-50 rounded-lg relative group">
              <div className="flex items-center gap-2 mb-1">
                <span className="font-medium text-gray-900">{t.name}</span>
                <span className="text-yellow-400 text-sm">{'★'.repeat(t.rating)}</span>
              </div>
              <p className="text-sm text-gray-600">{t.text}</p>
              <button onClick={() => setTestimonials(testimonials.filter((_, i) => i !== idx))} className="absolute top-2 right-2 text-red-500 opacity-0 group-hover:opacity-100">
                <X className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Amenities */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Studio Amenities</h3>
        
        <div className="flex gap-2 mb-4">
          <input
            type="text"
            value={newAmenity}
            onChange={(e) => setNewAmenity(e.target.value)}
            placeholder="e.g., Air Conditioning, Parking"
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary-500 focus:border-primary-500"
            onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); addAmenity(); } }}
          />
          <button type="button" onClick={addAmenity} className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700">
            <Plus className="w-4 h-4" />
          </button>
        </div>
        
        <div className="flex flex-wrap gap-2">
          {amenities.map((amenity, idx) => (
            <span key={idx} className="inline-flex items-center gap-1 px-3 py-1 bg-gray-100 rounded-full text-sm">
              {amenity}
              <button onClick={() => setAmenities(amenities.filter((_, i) => i !== idx))} className="text-gray-500 hover:text-gray-700">
                <X className="w-3 h-3" />
              </button>
            </span>
          ))}
        </div>
      </div>

      {/* Social Links */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Social Media Links</h3>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Instagram</label>
            <input
              type="url"
              value={socialLinks.instagram}
              onChange={(e) => setSocialLinks({ ...socialLinks, instagram: e.target.value })}
              placeholder="https://instagram.com/yourstudio"
              className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary-500 focus:border-primary-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">YouTube</label>
            <input
              type="url"
              value={socialLinks.youtube}
              onChange={(e) => setSocialLinks({ ...socialLinks, youtube: e.target.value })}
              placeholder="https://youtube.com/@yourstudio"
              className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary-500 focus:border-primary-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Facebook</label>
            <input
              type="url"
              value={socialLinks.facebook}
              onChange={(e) => setSocialLinks({ ...socialLinks, facebook: e.target.value })}
              placeholder="https://facebook.com/yourstudio"
              className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary-500 focus:border-primary-500"
            />
          </div>
        </div>
      </div>

      <button type="button" onClick={handleSave} disabled={mutation.isPending} className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50">
        <Save className="w-4 h-4" />
        {mutation.isPending ? 'Saving...' : 'Save Media Settings'}
      </button>
    </div>
  )
}
