import { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { 
  CreditCard, Wallet, Package, Clock, Check, AlertCircle, 
  Loader2, Tag, X
} from 'lucide-react';
import api from '../lib/api';

interface ClassSession {
  id: string;
  date: string;
  start_time: string;
  end_time: string;
  class_name: string;
  instructor_name: string;
  drop_in_price: number;
}

interface ClassPack {
  id: string;
  name: string;
  class_count: number;
  price: number;
  validity_days: number;
}

interface WalletData {
  balance: number;
  currency: string;
}

declare global {
  interface Window {
    Razorpay: any;
  }
}

export default function CheckoutPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const session = location.state?.session as ClassSession | undefined;

  const [loading, setLoading] = useState(false);
  const [classPacks, setClassPacks] = useState<ClassPack[]>([]);
  const [selectedPack, setSelectedPack] = useState<ClassPack | null>(null);
  const [wallet, setWallet] = useState<WalletData | null>(null);
  const [discountCode, setDiscountCode] = useState('');
  const [discountApplied, setDiscountApplied] = useState<{ amount: number; code: string } | null>(null);
  const [discountError, setDiscountError] = useState('');
  const [useWalletBalance, setUseWalletBalance] = useState(false);
  const [paymentSuccess, setPaymentSuccess] = useState(false);
  const [error, setError] = useState('');

  // Calculate amounts
  const baseAmount = session?.drop_in_price || selectedPack?.price || 0;
  const discountAmount = discountApplied?.amount || 0;
  const walletDeduction = useWalletBalance ? Math.min(wallet?.balance || 0, baseAmount - discountAmount) : 0;
  const taxRate = 0.18;
  const subtotal = baseAmount - discountAmount - walletDeduction;
  const taxAmount = subtotal * taxRate;
  const totalAmount = subtotal + taxAmount;

  useEffect(() => {
    fetchClassPacks();
    fetchWallet();
    loadRazorpayScript();
  }, []);

  const loadRazorpayScript = () => {
    const script = document.createElement('script');
    script.src = 'https://checkout.razorpay.com/v1/checkout.js';
    script.async = true;
    document.body.appendChild(script);
  };

  const fetchClassPacks = async () => {
    try {
      const response = await api.get('/payments/class-packs');
      setClassPacks(response.data.class_packs || []);
    } catch (err) {
      console.error('Failed to fetch class packs:', err);
    }
  };

  const fetchWallet = async () => {
    try {
      const contactsRes = await api.get('/contacts');
      const contactId = contactsRes.data.contacts[0]?.id;
      if (contactId) {
        const response = await api.get('/payments/wallet', { params: { contact_id: contactId } });
        setWallet(response.data);
      }
    } catch (err) {
      console.error('Failed to fetch wallet:', err);
    }
  };

  const applyDiscount = async () => {
    if (!discountCode.trim()) return;
    
    setDiscountError('');
    try {
      const response = await api.post('/payments/validate-code', {
        code: discountCode,
        amount: baseAmount
      });
      
      if (response.data.valid) {
        setDiscountApplied({
          amount: response.data.discount_amount,
          code: discountCode.toUpperCase()
        });
      } else {
        setDiscountError(response.data.error || 'Invalid code');
      }
    } catch (err: any) {
      setDiscountError(err.response?.data?.error || 'Failed to apply code');
    }
  };

  const removeDiscount = () => {
    setDiscountApplied(null);
    setDiscountCode('');
  };

  const handlePayment = async () => {
    setLoading(true);
    setError('');

    try {
      const contactsRes = await api.get('/contacts');
      const contactId = contactsRes.data.contacts[0]?.id;

      if (!contactId) {
        setError('No contact found');
        return;
      }

      // Create order
      const orderRes = await api.post('/payments/create-order', {
        contact_id: contactId,
        amount: baseAmount,
        purchase_type: session ? 'DROP_IN' : 'CLASS_PACK',
        description: session ? `Class: ${session.class_name}` : `Class Pack: ${selectedPack?.name}`,
        discount_code: discountApplied?.code,
        use_wallet: useWalletBalance
      });

      const orderData = orderRes.data;

      // If fully covered by wallet
      if (orderData.total_amount === 0) {
        setPaymentSuccess(true);
        return;
      }

      // Open Razorpay
      const options = {
        key: orderData.razorpay_key_id,
        amount: Math.round(orderData.total_amount * 100),
        currency: orderData.currency,
        name: 'Studio OS',
        description: session ? session.class_name : selectedPack?.name,
        order_id: orderData.razorpay_order_id,
        handler: async (response: any) => {
          // Verify payment
          try {
            await api.post('/payments/verify', {
              payment_id: orderData.payment_id,
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_order_id: response.razorpay_order_id,
              razorpay_signature: response.razorpay_signature
            });
            setPaymentSuccess(true);
          } catch (err) {
            setError('Payment verification failed');
          }
        },
        prefill: {
          name: orderData.contact?.name,
          email: orderData.contact?.email,
          contact: orderData.contact?.phone
        },
        theme: {
          color: '#9333EA'
        }
      };

      const razorpay = new window.Razorpay(options);
      razorpay.open();

    } catch (err: any) {
      setError(err.response?.data?.error || 'Payment failed');
    } finally {
      setLoading(false);
    }
  };

  if (paymentSuccess) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="bg-white rounded-xl p-8 max-w-md w-full mx-4 shadow-lg text-center">
          <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <Check className="w-10 h-10 text-green-600" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Payment Successful!</h2>
          <p className="text-gray-600 mb-6">
            {session 
              ? `Your booking for ${session.class_name} is confirmed.`
              : `Your ${selectedPack?.name} is now active.`
            }
          </p>
          <button
            onClick={() => navigate('/my-bookings')}
            className="w-full py-3 bg-purple-600 text-white rounded-lg font-semibold hover:bg-purple-700"
          >
            View My Bookings
          </button>
          <button
            onClick={() => navigate('/booking')}
            className="w-full mt-2 py-3 border border-gray-300 text-gray-700 rounded-lg font-semibold hover:bg-gray-50"
          >
            Book Another Class
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Checkout</h1>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* What you're buying */}
            <div className="bg-white rounded-xl p-6 shadow-sm">
              <h2 className="text-lg font-semibold mb-4">Order Details</h2>
              
              {session ? (
                <div className="flex items-start gap-4 p-4 bg-purple-50 rounded-lg">
                  <div className="w-12 h-12 bg-purple-600 rounded-lg flex items-center justify-center">
                    <Clock className="w-6 h-6 text-white" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900">{session.class_name}</h3>
                    <p className="text-sm text-gray-600">
                      {new Date(session.date).toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}
                    </p>
                    <p className="text-sm text-gray-600">
                      {new Date(session.start_time).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })} • {session.instructor_name}
                    </p>
                  </div>
                  <div className="text-right">
                    <span className="text-lg font-bold text-gray-900">₹{session.drop_in_price}</span>
                  </div>
                </div>
              ) : (
                <div className="space-y-3">
                  <p className="text-gray-600 mb-4">Select a class pack:</p>
                  {classPacks.map((pack) => (
                    <div
                      key={pack.id}
                      onClick={() => setSelectedPack(pack)}
                      className={`flex items-center gap-4 p-4 rounded-lg border-2 cursor-pointer transition-all ${
                        selectedPack?.id === pack.id
                          ? 'border-purple-600 bg-purple-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                        <Package className="w-6 h-6 text-purple-600" />
                      </div>
                      <div className="flex-1">
                        <h3 className="font-semibold text-gray-900">{pack.name}</h3>
                        <p className="text-sm text-gray-600">
                          {pack.class_count} classes • Valid for {pack.validity_days} days
                        </p>
                      </div>
                      <div className="text-right">
                        <span className="text-lg font-bold text-gray-900">₹{pack.price}</span>
                        <p className="text-xs text-gray-500">₹{Math.round(pack.price / pack.class_count)}/class</p>
                      </div>
                      {selectedPack?.id === pack.id && (
                        <Check className="w-5 h-5 text-purple-600" />
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Discount Code */}
            <div className="bg-white rounded-xl p-6 shadow-sm">
              <h2 className="text-lg font-semibold mb-4">Discount Code</h2>
              
              {discountApplied ? (
                <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg border border-green-200">
                  <div className="flex items-center gap-2">
                    <Tag className="w-5 h-5 text-green-600" />
                    <span className="font-medium text-green-700">{discountApplied.code}</span>
                    <span className="text-green-600">- ₹{discountApplied.amount} off</span>
                  </div>
                  <button onClick={removeDiscount} className="text-gray-400 hover:text-gray-600">
                    <X className="w-5 h-5" />
                  </button>
                </div>
              ) : (
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={discountCode}
                    onChange={(e) => setDiscountCode(e.target.value.toUpperCase())}
                    placeholder="Enter code"
                    className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  />
                  <button
                    onClick={applyDiscount}
                    className="px-6 py-2 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200"
                  >
                    Apply
                  </button>
                </div>
              )}
              {discountError && (
                <p className="mt-2 text-sm text-red-600">{discountError}</p>
              )}
            </div>

            {/* Wallet */}
            {wallet && wallet.balance > 0 && (
              <div className="bg-white rounded-xl p-6 shadow-sm">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                      <Wallet className="w-5 h-5 text-green-600" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900">Wallet Balance</h3>
                      <p className="text-sm text-gray-600">₹{wallet.balance} available</p>
                    </div>
                  </div>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={useWalletBalance}
                      onChange={(e) => setUseWalletBalance(e.target.checked)}
                      className="w-5 h-5 text-purple-600 rounded focus:ring-purple-500"
                    />
                    <span className="text-sm font-medium text-gray-700">Use wallet</span>
                  </label>
                </div>
              </div>
            )}
          </div>

          {/* Order Summary */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-xl p-6 shadow-sm sticky top-6">
              <h2 className="text-lg font-semibold mb-4">Order Summary</h2>
              
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Subtotal</span>
                  <span className="text-gray-900">₹{baseAmount}</span>
                </div>
                
                {discountAmount > 0 && (
                  <div className="flex justify-between text-green-600">
                    <span>Discount</span>
                    <span>-₹{discountAmount}</span>
                  </div>
                )}
                
                {walletDeduction > 0 && (
                  <div className="flex justify-between text-green-600">
                    <span>Wallet</span>
                    <span>-₹{walletDeduction.toFixed(2)}</span>
                  </div>
                )}
                
                <div className="flex justify-between">
                  <span className="text-gray-600">GST (18%)</span>
                  <span className="text-gray-900">₹{taxAmount.toFixed(2)}</span>
                </div>
                
                <div className="border-t pt-3 mt-3">
                  <div className="flex justify-between text-lg font-bold">
                    <span>Total</span>
                    <span>₹{totalAmount.toFixed(2)}</span>
                  </div>
                </div>
              </div>

              {error && (
                <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-red-700 text-sm">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  {error}
                </div>
              )}

              <button
                onClick={handlePayment}
                disabled={loading || (!session && !selectedPack)}
                className="w-full mt-6 py-3 bg-purple-600 text-white rounded-lg font-semibold hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    <CreditCard className="w-5 h-5" />
                    Pay ₹{totalAmount.toFixed(2)}
                  </>
                )}
              </button>

              <div className="mt-4 flex items-center justify-center gap-2 text-xs text-gray-500">
                <img src="https://cdn.razorpay.com/static/assets/logo/payment.svg" alt="Razorpay" className="h-4" />
                <span>Secured by Razorpay</span>
              </div>

              <div className="mt-4 text-xs text-gray-500 text-center">
                UPI • Cards • NetBanking • Wallets
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
