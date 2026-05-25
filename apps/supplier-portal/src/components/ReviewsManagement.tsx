import React, { useState, useEffect } from 'react';
import { getReviews, getReviewStats, respondToReview, flagReview } from '../api.ts';
import { Star, MessageSquare, Flag, AlertTriangle } from 'lucide-react';

export function ReviewsManagement() {
  const [reviews, setReviews] = useState([]);
  const [stats, setStats] = useState({ total: 0, average_rating: 0, rating_distribution: {} });
  const [loading, setLoading] = useState(true);
  const [selectedReview, setSelectedReview] = useState(null);
  const [responseText, setResponseText] = useState('');

  useEffect(() => {
    loadReviews();
  }, []);

  const loadReviews = async () => {
    try {
      const [reviewsData, statsData] = await Promise.all([
        getReviews(50, 0),
        getReviewStats(),
      ]);
      setReviews(reviewsData.reviews || []);
      setStats(statsData);
    } catch (err) {
      console.error('Failed to load reviews:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRespond = async () => {
    if (!selectedReview || !responseText.trim()) return;
    try {
      await respondToReview(selectedReview.id, responseText);
      setResponseText('');
      setSelectedReview(null);
      loadReviews();
    } catch (err) {
      console.error('Failed to respond to review:', err);
    }
  };

  const handleFlag = async (reviewId) => {
    try {
      await flagReview(reviewId);
      loadReviews();
    } catch (err) {
      console.error('Failed to flag review:', err);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={Star} label="Total Reviews" value={stats.total} color="yellow" />
        <StatCard icon={Star} label="Average Rating" value={stats.average_rating.toFixed(1)} color="green" />
        <StatCard icon={MessageSquare} label="Pending Responses" value={reviews.filter(r => !r.supplier_response).length} color="blue" />
        <StatCard icon={Flag} label="Flagged" value={reviews.filter(r => r.is_flagged).length} color="red" />
      </div>

      <div className="bg-white rounded-2xl shadow-lg p-6">
        <h3 className="text-lg font-black text-earth-800 mb-4">Customer Reviews</h3>
        {reviews.length === 0 ? (
          <p className="text-earth-500 text-center py-8">No reviews yet</p>
        ) : (
          <div className="space-y-4">
            {reviews.map((review) => (
              <ReviewCard key={review.id} review={review} onSelect={setSelectedReview} onFlag={handleFlag} />
            ))}
          </div>
        )}
      </div>

      {selectedReview && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl shadow-xl p-6 max-w-lg w-full mx-4">
            <h3 className="text-lg font-black text-earth-800 mb-4">Respond to Review</h3>
            <div className="bg-earth-50 rounded-xl p-4 mb-4">
              <p className="font-bold text-earth-800">{selectedReview.buyer_name}</p>
              <div className="flex items-center gap-1 my-2">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} size={16} className={i < selectedReview.rating ? 'text-yellow-500 fill-yellow-500' : 'text-gray-300'} />
                ))}
              </div>
              <p className="text-earth-600">{selectedReview.comment}</p>
            </div>
            <textarea
              value={responseText}
              onChange={(e) => setResponseText(e.target.value)}
              placeholder="Write your response..."
              className="w-full h-32 p-4 border-2 border-earth-200 rounded-xl focus:border-primary-500 focus:outline-none resize-none"
            />
            <div className="flex gap-3 mt-4">
              <button
                onClick={handleRespond}
                className="flex-1 bg-primary-600 text-white font-black py-3 rounded-xl hover:bg-primary-700 transition-colors"
              >
                Submit Response
              </button>
              <button
                onClick={() => { setSelectedReview(null); setResponseText(''); }}
                className="flex-1 bg-earth-100 text-earth-800 font-black py-3 rounded-xl hover:bg-earth-200 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({ icon: Icon, label, value, color }) {
  const colors = {
    yellow: 'bg-yellow-50 text-yellow-600',
    green: 'bg-green-50 text-green-600',
    blue: 'bg-blue-50 text-blue-600',
    red: 'bg-red-50 text-red-600',
  };
  return (
    <div className="bg-white rounded-2xl shadow-lg p-6">
      <div className={`w-12 h-12 ${colors[color]} rounded-xl flex items-center justify-center mb-4`}>
        <Icon className="w-6 h-6" />
      </div>
      <p className="text-earth-600 font-bold text-sm">{label}</p>
      <p className="text-2xl font-black text-earth-800">{value}</p>
    </div>
  );
}

function ReviewCard({ review, onSelect, onFlag }) {
  return (
    <div className="bg-earth-50 rounded-xl p-6">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-primary-100 rounded-full flex items-center justify-center">
            <span className="text-primary-600 font-black text-lg">{review.buyer_name?.charAt(0) || 'U'}</span>
          </div>
          <div>
            <p className="font-bold text-earth-800">{review.buyer_name}</p>
            <p className="text-sm text-earth-500">{new Date(review.created_at).toLocaleDateString()}</p>
          </div>
        </div>
        <div className="flex items-center gap-1">
          {[...Array(5)].map((_, i) => (
            <Star key={i} size={16} className={i < review.rating ? 'text-yellow-500 fill-yellow-500' : 'text-gray-300'} />
          ))}
        </div>
      </div>

      <p className="text-earth-700 mb-4">{review.comment}</p>

      {review.supplier_response && (
        <div className="bg-white rounded-lg p-4 mb-4">
          <p className="text-sm font-bold text-earth-600 mb-2">Your Response:</p>
          <p className="text-earth-700">{review.supplier_response}</p>
        </div>
      )}

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {review.is_flagged && (
            <span className="flex items-center gap-1 text-xs font-bold text-red-600">
              <Flag size={12} />Flagged
            </span>
          )}
          {review.is_hidden && (
            <span className="flex items-center gap-1 text-xs font-bold text-gray-600">
              <AlertTriangle size={12} />Hidden
            </span>
          )}
        </div>
        <div className="flex gap-2">
          {!review.supplier_response && (
            <button
              onClick={() => onSelect(review)}
              className="px-4 py-2 bg-primary-100 text-primary-700 font-bold text-sm rounded-lg hover:bg-primary-200 transition-colors"
            >
              Respond
            </button>
          )}
          {!review.is_flagged && (
            <button
              onClick={() => onFlag(review.id)}
              className="px-4 py-2 bg-red-100 text-red-700 font-bold text-sm rounded-lg hover:bg-red-200 transition-colors"
            >
              Flag
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
