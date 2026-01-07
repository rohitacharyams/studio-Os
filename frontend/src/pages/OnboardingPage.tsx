import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Building2, MessageSquare, Calendar, CreditCard, Link2, 
  Check, ChevronRight, ChevronLeft, Loader2, Upload,
  Instagram, Mail, Phone, Globe, MapPin, Clock
} from 'lucide-react';
import api from '../lib/api';

// Step indicator component
function StepIndicator({ currentStep, steps }: { currentStep: number; steps: string[] }) {
  return (
    <div className="flex items-center justify-center mb-8">
      {steps.map((step, index) => (
        <div key={step} className="flex items-center">
          <div className={`flex items-center justify-center w-10 h-10 rounded-full border-2 transition-all ${
            index < currentStep 
              ? 'bg-green-500 border-green-500 text-white' 
              : index === currentStep 
                ? 'bg-purple-600 border-purple-600 text-white'
                : 'bg-white border-gray-300 text-gray-400'
          }`}>
            {index < currentStep ? (
              <Check className="w-5 h-5" />
            ) : (
              <span className="text-sm font-semibold">{index + 1}</span>
            )}
          </div>
          {index < steps.length - 1 && (
            <div className={`w-16 h-1 mx-2 rounded ${
              index < currentStep ? 'bg-green-500' : 'bg-gray-200'
            }`} />
          )}
        </div>
      ))}
    </div>
  );
}

// WhatsApp icon component
function WhatsAppIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
    </svg>
  );
}

export default function OnboardingPage() {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  const steps = ['Studio Profile', 'Connect Channels', 'Set Up Classes', 'Payment Setup', 'Get Booking Link'];
  
  // Form state
  const [studioData, setStudioData] = useState({
    name: '',
    logo: '',
    address: '',
    city: '',
    phone: '',
    email: '',
    website: '',
    timezone: 'Asia/Kolkata',
    businessHours: {
      open: '09:00',
      close: '21:00'
    }
  });
  
  const [channels, setChannels] = useState({
    whatsapp: { connected: false, number: '' },
    gmail: { connected: false, email: '' },
    instagram: { connected: false, handle: '' }
  });
  
  const [classes, setClasses] = useState([
    { name: '', style: 'Salsa', level: 'Beginner', price: 500, duration: 60, capacity: 15 }
  ]);
  
  const [paymentSetup, setPaymentSetup] = useState({
    razorpayKeyId: '',
    razorpayKeySecret: '',
    bankAccount: '',
    ifscCode: '',
    accountName: ''
  });
  
  const [bookingLink, setBookingLink] = useState('');

  const handleNext = async () => {
    setError('');
    
    // Validate current step
    if (currentStep === 0) {
      if (!studioData.name || !studioData.phone || !studioData.email) {
        setError('Please fill in all required fields');
        return;
      }
    }
    
    if (currentStep === 2 && classes.some(c => !c.name || !c.price)) {
      setError('Please fill in all class details');
      return;
    }
    
    // Save progress
    if (currentStep === 0) {
      setLoading(true);
      try {
        await api.put('/studio/settings', {
          settings: {
            ...studioData,
            onboarding_step: 1
          }
        });
      } catch (err) {
        console.error('Failed to save studio settings:', err);
      } finally {
        setLoading(false);
      }
    }
    
    // Generate booking link on final step
    if (currentStep === 4) {
      const slug = studioData.name.toLowerCase().replace(/[^a-z0-9]/g, '-').replace(/-+/g, '-');
      setBookingLink(`${window.location.origin}/book/${slug}`);
    }
    
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const [showSetupModal, setShowSetupModal] = useState<'whatsapp' | 'gmail' | 'instagram' | null>(null);

  const handleConnectWhatsApp = async () => {
    // Show setup instructions modal
    setShowSetupModal('whatsapp');
  };

  const handleConnectGmail = async () => {
    // Show setup instructions modal  
    setShowSetupModal('gmail');
  };

  const handleConnectInstagram = async () => {
    // Show setup instructions modal
    setShowSetupModal('instagram');
  };

  const markChannelConnected = (channel: 'whatsapp' | 'gmail' | 'instagram') => {
    setChannels(prev => ({
      ...prev,
      [channel]: { 
        connected: true, 
        number: channel === 'whatsapp' ? studioData.phone : undefined,
        email: channel === 'gmail' ? studioData.email : undefined,
        handle: channel === 'instagram' ? '@yourstudio' : undefined
      }
    }));
    setShowSetupModal(null);
  };

  const addClass = () => {
    setClasses([...classes, { name: '', style: 'Salsa', level: 'Beginner', price: 500, duration: 60, capacity: 15 }]);
  };

  const removeClass = (index: number) => {
    setClasses(classes.filter((_, i) => i !== index));
  };

  const updateClass = (index: number, field: string, value: any) => {
    const updated = [...classes];
    updated[index] = { ...updated[index], [field]: value };
    setClasses(updated);
  };

  const handleFinish = async () => {
    setLoading(true);
    try {
      // Save classes
      for (const classData of classes) {
        if (classData.name) {
          await api.post('/scheduling/classes', {
            name: classData.name,
            style: classData.style,
            level: classData.level,
            drop_in_price: classData.price,
            duration_minutes: classData.duration,
            max_students: classData.capacity
          });
        }
      }
      
      // Mark onboarding complete
      await api.put('/studio/settings', {
        settings: {
          onboarding_complete: true,
          booking_slug: studioData.name.toLowerCase().replace(/[^a-z0-9]/g, '-')
        }
      });
      
      navigate('/inbox');
    } catch (err) {
      setError('Failed to complete setup. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 0: // Studio Profile
        return (
          <div className="space-y-6">
            <div className="text-center mb-8">
              <Building2 className="w-16 h-16 text-purple-600 mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-gray-900">Let's set up your studio</h2>
              <p className="text-gray-600 mt-2">Tell us about your dance studio</p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Studio Name *
                </label>
                <input
                  type="text"
                  value={studioData.name}
                  onChange={(e) => setStudioData({ ...studioData, name: e.target.value })}
                  placeholder="e.g., Rhythm Dance Academy"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <Phone className="w-4 h-4 inline mr-1" /> Phone Number *
                </label>
                <input
                  type="tel"
                  value={studioData.phone}
                  onChange={(e) => setStudioData({ ...studioData, phone: e.target.value })}
                  placeholder="+91 98765 43210"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <Mail className="w-4 h-4 inline mr-1" /> Email *
                </label>
                <input
                  type="email"
                  value={studioData.email}
                  onChange={(e) => setStudioData({ ...studioData, email: e.target.value })}
                  placeholder="hello@yourstudio.com"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>
              
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <MapPin className="w-4 h-4 inline mr-1" /> Address
                </label>
                <input
                  type="text"
                  value={studioData.address}
                  onChange={(e) => setStudioData({ ...studioData, address: e.target.value })}
                  placeholder="123 Dance Street, Mumbai 400001"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <Globe className="w-4 h-4 inline mr-1" /> Website (optional)
                </label>
                <input
                  type="url"
                  value={studioData.website}
                  onChange={(e) => setStudioData({ ...studioData, website: e.target.value })}
                  placeholder="https://yourstudio.com"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <Clock className="w-4 h-4 inline mr-1" /> Business Hours
                </label>
                <div className="flex items-center gap-2">
                  <input
                    type="time"
                    value={studioData.businessHours.open}
                    onChange={(e) => setStudioData({ 
                      ...studioData, 
                      businessHours: { ...studioData.businessHours, open: e.target.value }
                    })}
                    className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  />
                  <span className="text-gray-500">to</span>
                  <input
                    type="time"
                    value={studioData.businessHours.close}
                    onChange={(e) => setStudioData({ 
                      ...studioData, 
                      businessHours: { ...studioData.businessHours, close: e.target.value }
                    })}
                    className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  />
                </div>
              </div>
            </div>
          </div>
        );

      case 1: // Connect Channels
        return (
          <div className="space-y-6">
            <div className="text-center mb-8">
              <MessageSquare className="w-16 h-16 text-purple-600 mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-gray-900">Connect your channels</h2>
              <p className="text-gray-600 mt-2">Bring all your messages into one inbox</p>
            </div>
            
            <div className="space-y-4">
              {/* WhatsApp */}
              <div className={`p-6 rounded-xl border-2 transition-all ${
                channels.whatsapp.connected 
                  ? 'border-green-500 bg-green-50' 
                  : 'border-gray-200 hover:border-green-300'
              }`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-green-500 rounded-xl flex items-center justify-center">
                      <WhatsAppIcon className="w-7 h-7 text-white" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900">WhatsApp Business</h3>
                      <p className="text-sm text-gray-600">
                        {channels.whatsapp.connected 
                          ? `Connected: ${channels.whatsapp.number}` 
                          : 'Connect your WhatsApp Business account'}
                      </p>
                    </div>
                  </div>
                  {channels.whatsapp.connected ? (
                    <div className="flex items-center gap-2 text-green-600">
                      <Check className="w-5 h-5" />
                      <span className="font-medium">Connected</span>
                    </div>
                  ) : (
                    <button
                      onClick={handleConnectWhatsApp}
                      disabled={loading}
                      className="px-4 py-2 bg-green-500 text-white rounded-lg font-medium hover:bg-green-600 disabled:opacity-50"
                    >
                      {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Connect'}
                    </button>
                  )}
                </div>
              </div>

              {/* Gmail */}
              <div className={`p-6 rounded-xl border-2 transition-all ${
                channels.gmail.connected 
                  ? 'border-green-500 bg-green-50' 
                  : 'border-gray-200 hover:border-red-300'
              }`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-red-500 rounded-xl flex items-center justify-center">
                      <Mail className="w-7 h-7 text-white" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900">Gmail</h3>
                      <p className="text-sm text-gray-600">
                        {channels.gmail.connected 
                          ? `Connected: ${channels.gmail.email}` 
                          : 'Connect your Gmail account'}
                      </p>
                    </div>
                  </div>
                  {channels.gmail.connected ? (
                    <div className="flex items-center gap-2 text-green-600">
                      <Check className="w-5 h-5" />
                      <span className="font-medium">Connected</span>
                    </div>
                  ) : (
                    <button
                      onClick={handleConnectGmail}
                      disabled={loading}
                      className="px-4 py-2 bg-red-500 text-white rounded-lg font-medium hover:bg-red-600 disabled:opacity-50"
                    >
                      {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Connect'}
                    </button>
                  )}
                </div>
              </div>

              {/* Instagram */}
              <div className={`p-6 rounded-xl border-2 transition-all ${
                channels.instagram.connected 
                  ? 'border-green-500 bg-green-50' 
                  : 'border-gray-200 hover:border-pink-300'
              }`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-gradient-to-br from-purple-600 to-pink-500 rounded-xl flex items-center justify-center">
                      <Instagram className="w-7 h-7 text-white" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900">Instagram DMs</h3>
                      <p className="text-sm text-gray-600">
                        {channels.instagram.connected 
                          ? `Connected: ${channels.instagram.handle}` 
                          : 'Connect your Instagram Business account'}
                      </p>
                    </div>
                  </div>
                  {channels.instagram.connected ? (
                    <div className="flex items-center gap-2 text-green-600">
                      <Check className="w-5 h-5" />
                      <span className="font-medium">Connected</span>
                    </div>
                  ) : (
                    <button
                      onClick={handleConnectInstagram}
                      disabled={loading}
                      className="px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-500 text-white rounded-lg font-medium hover:opacity-90 disabled:opacity-50"
                    >
                      {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Connect'}
                    </button>
                  )}
                </div>
              </div>
            </div>
            
            <p className="text-center text-sm text-gray-500 mt-4">
              You can skip this step and connect channels later from Settings
            </p>
          </div>
        );

      case 2: // Set Up Classes
        return (
          <div className="space-y-6">
            <div className="text-center mb-8">
              <Calendar className="w-16 h-16 text-purple-600 mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-gray-900">Add your classes</h2>
              <p className="text-gray-600 mt-2">Set up the classes you offer</p>
            </div>
            
            <div className="space-y-4">
              {classes.map((classItem, index) => (
                <div key={index} className="p-6 bg-gray-50 rounded-xl">
                  <div className="flex items-center justify-between mb-4">
                    <h4 className="font-medium text-gray-900">Class {index + 1}</h4>
                    {classes.length > 1 && (
                      <button
                        onClick={() => removeClass(index)}
                        className="text-red-500 text-sm hover:text-red-700"
                      >
                        Remove
                      </button>
                    )}
                  </div>
                  
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    <div className="col-span-2 md:col-span-1">
                      <label className="block text-sm text-gray-600 mb-1">Class Name *</label>
                      <input
                        type="text"
                        value={classItem.name}
                        onChange={(e) => updateClass(index, 'name', e.target.value)}
                        placeholder="e.g., Beginner Salsa"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm text-gray-600 mb-1">Style</label>
                      <select
                        value={classItem.style}
                        onChange={(e) => updateClass(index, 'style', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                      >
                        <option value="Salsa">Salsa</option>
                        <option value="Bachata">Bachata</option>
                        <option value="Hip-Hop">Hip-Hop</option>
                        <option value="Contemporary">Contemporary</option>
                        <option value="Bollywood">Bollywood</option>
                        <option value="Classical">Classical</option>
                        <option value="Jazz">Jazz</option>
                        <option value="Ballet">Ballet</option>
                        <option value="Other">Other</option>
                      </select>
                    </div>
                    
                    <div>
                      <label className="block text-sm text-gray-600 mb-1">Level</label>
                      <select
                        value={classItem.level}
                        onChange={(e) => updateClass(index, 'level', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                      >
                        <option value="Beginner">Beginner</option>
                        <option value="Intermediate">Intermediate</option>
                        <option value="Advanced">Advanced</option>
                        <option value="All Levels">All Levels</option>
                      </select>
                    </div>
                    
                    <div>
                      <label className="block text-sm text-gray-600 mb-1">Price (₹) *</label>
                      <input
                        type="number"
                        value={classItem.price}
                        onChange={(e) => updateClass(index, 'price', parseInt(e.target.value))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm text-gray-600 mb-1">Duration (mins)</label>
                      <input
                        type="number"
                        value={classItem.duration}
                        onChange={(e) => updateClass(index, 'duration', parseInt(e.target.value))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm text-gray-600 mb-1">Max Capacity</label>
                      <input
                        type="number"
                        value={classItem.capacity}
                        onChange={(e) => updateClass(index, 'capacity', parseInt(e.target.value))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                      />
                    </div>
                  </div>
                </div>
              ))}
              
              <button
                onClick={addClass}
                className="w-full py-3 border-2 border-dashed border-gray-300 rounded-xl text-gray-600 hover:border-purple-500 hover:text-purple-600 transition-colors"
              >
                + Add Another Class
              </button>
            </div>
          </div>
        );

      case 3: // Payment Setup
        return (
          <div className="space-y-6">
            <div className="text-center mb-8">
              <CreditCard className="w-16 h-16 text-purple-600 mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-gray-900">Set up payments</h2>
              <p className="text-gray-600 mt-2">Connect Razorpay to accept online payments</p>
            </div>
            
            <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-6">
              <h4 className="font-medium text-blue-900 mb-2">💡 How it works</h4>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>• Payments go directly to YOUR Razorpay account</li>
                <li>• You keep 100% of the payment (minus Razorpay fees ~2%)</li>
                <li>• Studio OS does NOT take any commission</li>
                <li>• Settlement happens as per your Razorpay settings</li>
              </ul>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Razorpay Key ID
                </label>
                <input
                  type="text"
                  value={paymentSetup.razorpayKeyId}
                  onChange={(e) => setPaymentSetup({ ...paymentSetup, razorpayKeyId: e.target.value })}
                  placeholder="rzp_live_xxxxxxxxxxxxx"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Razorpay Key Secret
                </label>
                <input
                  type="password"
                  value={paymentSetup.razorpayKeySecret}
                  onChange={(e) => setPaymentSetup({ ...paymentSetup, razorpayKeySecret: e.target.value })}
                  placeholder="••••••••••••••••••••"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                />
              </div>
              
              <div className="pt-4 border-t">
                <p className="text-sm text-gray-600 mb-4">
                  Don't have a Razorpay account?{' '}
                  <a 
                    href="https://razorpay.com/signup/" 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-purple-600 font-medium hover:underline"
                  >
                    Create one here →
                  </a>
                </p>
              </div>
            </div>
            
            <p className="text-center text-sm text-gray-500">
              You can skip this and accept cash payments only
            </p>
          </div>
        );

      case 4: // Get Booking Link
        return (
          <div className="space-y-6">
            <div className="text-center mb-8">
              <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Check className="w-10 h-10 text-green-600" />
              </div>
              <h2 className="text-2xl font-bold text-gray-900">You're all set! 🎉</h2>
              <p className="text-gray-600 mt-2">Share your booking link with students</p>
            </div>
            
            <div className="bg-purple-50 border-2 border-purple-200 rounded-xl p-6">
              <div className="flex items-center justify-between mb-4">
                <h4 className="font-medium text-purple-900">Your Public Booking Page</h4>
                <Link2 className="w-5 h-5 text-purple-600" />
              </div>
              
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  readOnly
                  value={bookingLink || `${window.location.origin}/book/${studioData.name.toLowerCase().replace(/[^a-z0-9]/g, '-')}`}
                  className="flex-1 px-4 py-3 bg-white border border-purple-200 rounded-lg text-purple-900 font-mono text-sm"
                />
                <button
                  onClick={() => navigator.clipboard.writeText(bookingLink || `${window.location.origin}/book/${studioData.name.toLowerCase().replace(/[^a-z0-9]/g, '-')}`)}
                  className="px-4 py-3 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700"
                >
                  Copy
                </button>
              </div>
              
              <p className="text-sm text-purple-700 mt-3">
                Students can visit this link to view your schedule and book classes
              </p>
            </div>
            
            <div className="grid grid-cols-2 gap-4 mt-6">
              <div className="p-4 bg-gray-50 rounded-xl text-center">
                <h4 className="font-medium text-gray-900 mb-1">Share on WhatsApp</h4>
                <button className="text-green-600 text-sm font-medium hover:underline">
                  Send to contacts →
                </button>
              </div>
              <div className="p-4 bg-gray-50 rounded-xl text-center">
                <h4 className="font-medium text-gray-900 mb-1">Add to Instagram Bio</h4>
                <button className="text-pink-600 text-sm font-medium hover:underline">
                  Copy short link →
                </button>
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-indigo-50 py-8 px-4">
      <div className="max-w-2xl mx-auto">
        {/* Logo */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-purple-600">Studio OS</h1>
          <p className="text-gray-600">Dance Studio Management</p>
        </div>
        
        {/* Step Indicator */}
        <StepIndicator currentStep={currentStep} steps={steps} />
        
        {/* Content Card */}
        <div className="bg-white rounded-2xl shadow-xl p-8">
          {renderStepContent()}
          
          {error && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}
          
          {/* Navigation */}
          <div className="flex items-center justify-between mt-8 pt-6 border-t">
            <button
              onClick={handleBack}
              disabled={currentStep === 0}
              className={`flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition-colors ${
                currentStep === 0
                  ? 'text-gray-300 cursor-not-allowed'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              <ChevronLeft className="w-5 h-5" />
              Back
            </button>
            
            {currentStep === steps.length - 1 ? (
              <button
                onClick={handleFinish}
                disabled={loading}
                className="flex items-center gap-2 px-8 py-3 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 disabled:opacity-50"
              >
                {loading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <>
                    Go to Dashboard
                    <ChevronRight className="w-5 h-5" />
                  </>
                )}
              </button>
            ) : (
              <button
                onClick={handleNext}
                disabled={loading}
                className="flex items-center gap-2 px-8 py-3 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 disabled:opacity-50"
              >
                {loading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <>
                    Continue
                    <ChevronRight className="w-5 h-5" />
                  </>
                )}
              </button>
            )}
          </div>
        </div>
        
        {/* Skip option */}
        {currentStep < steps.length - 1 && (
          <p className="text-center mt-4 text-sm text-gray-500">
            <button 
              onClick={() => navigate('/inbox')}
              className="text-purple-600 hover:underline"
            >
              Skip setup and go to dashboard →
            </button>
          </p>
        )}
      </div>

      {/* Setup Modal */}
      {showSetupModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b">
              <div className="flex items-center justify-between">
                <h3 className="text-xl font-bold text-gray-900">
                  {showSetupModal === 'whatsapp' && '📱 Connect WhatsApp Business'}
                  {showSetupModal === 'gmail' && '📧 Connect Gmail'}
                  {showSetupModal === 'instagram' && '📸 Connect Instagram'}
                </h3>
                <button 
                  onClick={() => setShowSetupModal(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>
            </div>
            
            <div className="p-6">
              {showSetupModal === 'whatsapp' && (
                <div className="space-y-4">
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                    <h4 className="font-medium text-yellow-800 mb-2">⚠️ Requirements</h4>
                    <ul className="text-sm text-yellow-700 space-y-1">
                      <li>• A WhatsApp Business Account (not regular WhatsApp)</li>
                      <li>• A Twilio account with WhatsApp enabled</li>
                      <li>• Verified business phone number</li>
                    </ul>
                  </div>
                  
                  <div className="space-y-3">
                    <h4 className="font-semibold">Setup Steps:</h4>
                    <ol className="text-sm text-gray-600 space-y-2 list-decimal list-inside">
                      <li>Create a <a href="https://www.twilio.com/try-twilio" target="_blank" rel="noopener noreferrer" className="text-purple-600 underline">Twilio account</a></li>
                      <li>Enable WhatsApp in Twilio Console</li>
                      <li>Get a WhatsApp-enabled phone number from Twilio</li>
                      <li>Configure webhook URL to: <code className="bg-gray-100 px-1 rounded text-xs">{window.location.origin}/api/whatsapp/webhook</code></li>
                      <li>Add your Twilio credentials to Studio OS settings</li>
                    </ol>
                  </div>
                  
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <p className="text-sm text-blue-700">
                      <strong>For testing:</strong> You can use Twilio's sandbox to test before going live.
                    </p>
                  </div>
                </div>
              )}
              
              {showSetupModal === 'gmail' && (
                <div className="space-y-4">
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                    <h4 className="font-medium text-yellow-800 mb-2">⚠️ Requirements</h4>
                    <ul className="text-sm text-yellow-700 space-y-1">
                      <li>• A Google Workspace or Gmail account</li>
                      <li>• Google Cloud Console project</li>
                      <li>• OAuth 2.0 credentials configured</li>
                    </ul>
                  </div>
                  
                  <div className="space-y-3">
                    <h4 className="font-semibold">Setup Steps:</h4>
                    <ol className="text-sm text-gray-600 space-y-2 list-decimal list-inside">
                      <li>Create a project in <a href="https://console.cloud.google.com" target="_blank" rel="noopener noreferrer" className="text-purple-600 underline">Google Cloud Console</a></li>
                      <li>Enable Gmail API</li>
                      <li>Configure OAuth consent screen</li>
                      <li>Create OAuth 2.0 credentials</li>
                      <li>Add authorized redirect URI</li>
                    </ol>
                  </div>
                  
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                    <p className="text-sm text-gray-600">
                      Gmail integration allows you to receive and send emails directly from Studio OS inbox.
                    </p>
                  </div>
                </div>
              )}
              
              {showSetupModal === 'instagram' && (
                <div className="space-y-4">
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                    <h4 className="font-medium text-yellow-800 mb-2">⚠️ Requirements</h4>
                    <ul className="text-sm text-yellow-700 space-y-1">
                      <li>• An Instagram Business or Creator account</li>
                      <li>• Connected to a Facebook Page</li>
                      <li>• Meta Developer account</li>
                    </ul>
                  </div>
                  
                  <div className="space-y-3">
                    <h4 className="font-semibold">Setup Steps:</h4>
                    <ol className="text-sm text-gray-600 space-y-2 list-decimal list-inside">
                      <li>Convert to Instagram Business account</li>
                      <li>Connect Instagram to a Facebook Page</li>
                      <li>Create app in <a href="https://developers.facebook.com" target="_blank" rel="noopener noreferrer" className="text-purple-600 underline">Meta Developer Portal</a></li>
                      <li>Set up Instagram Messaging API</li>
                      <li>Configure webhooks for messages</li>
                    </ol>
                  </div>
                  
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                    <p className="text-sm text-gray-600">
                      Instagram DM integration requires business verification and may take a few days to approve.
                    </p>
                  </div>
                </div>
              )}
            </div>
            
            <div className="p-6 border-t bg-gray-50 flex gap-3">
              <button
                onClick={() => setShowSetupModal(null)}
                className="flex-1 py-2 border border-gray-300 rounded-lg text-gray-700 font-medium hover:bg-gray-100"
              >
                I'll do this later
              </button>
              <button
                onClick={() => markChannelConnected(showSetupModal)}
                className="flex-1 py-2 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700"
              >
                I've completed setup
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
