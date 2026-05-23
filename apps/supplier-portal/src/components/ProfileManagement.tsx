import React, { useState, useEffect } from 'react';
import { getProfile, updateProfile, getApplicationStatus, uploadDocuments } from '../api.ts';
import { User, Building, MapPin, Phone, Mail, Save, Upload } from 'lucide-react';

export function ProfileManagement() {
  const [profile, setProfile] = useState(null);
  const [applicationStatus, setApplicationStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showDocUpload, setShowDocUpload] = useState(false);
  const [formData, setFormData] = useState({});
  const [docFiles, setDocFiles] = useState([]);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [p, status] = await Promise.all([
        getProfile(),
        getApplicationStatus().catch(() => null),
      ]);
      setProfile(p);
      setApplicationStatus(status);
      setFormData({
        business_name: p.business_name,
        physical_address: p.physical_address,
        contact_person: p.contact_person,
        phone: p.phone,
        email: p.email,
        shipping_policy: p.shipping_policy,
        return_policy: p.return_policy,
        business_hours: p.business_hours,
      });
    } catch (err) {
      console.error('Load profile error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await updateProfile(formData);
      alert('Profile updated successfully');
      loadData();
    } catch (err) {
      alert('Error updating profile: ' + err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleDocUpload = async (e) => {
    e.preventDefault();
    try {
      const docs = docFiles.map(f => ({
        document_type: f.type,
        document_url: f.url,
        document_name: f.name,
      }));
      await uploadDocuments(docs);
      setShowDocUpload(false);
      setDocFiles([]);
      loadData();
      alert('Documents uploaded successfully');
    } catch (err) {
      alert('Error uploading documents: ' + err.message);
    }
  };

  if (loading) {
    return <div className="text-center py-12">Loading profile...</div>;
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-black text-earth-800">Profile Management</h2>

      {/* Verification Status */}
      {applicationStatus && (
        <div className={`rounded-2xl p-6 ${
          applicationStatus.verification_status === 'approved' ? 'bg-green-50 border-2 border-green-200' :
          applicationStatus.verification_status === 'rejected' ? 'bg-red-50 border-2 border-red-200' :
          'bg-yellow-50 border-2 border-yellow-200'
        }`}>
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-black text-earth-800">Verification Status</h3>
              <p className="text-sm text-earth-600 capitalize">{applicationStatus.verification_status}</p>
              {applicationStatus.verification_notes && (
                <p className="text-sm text-earth-600 mt-1">{applicationStatus.verification_notes}</p>
              )}
            </div>
            <button
              onClick={() => setShowDocUpload(true)}
              className="flex items-center gap-2 bg-primary-600 hover:bg-primary-700 text-white font-bold px-4 py-2 rounded-xl"
            >
              <Upload className="w-4 h-4" /> Upload Documents
            </button>
          </div>
        </div>
      )}

      {/* Profile Form */}
      <div className="bg-white rounded-2xl shadow-lg p-6">
        <h3 className="font-black text-earth-800 mb-6">Business Information</h3>
        <form onSubmit={handleSave} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-bold text-earth-700 mb-2">Business Name</label>
              <input
                type="text"
                value={formData.business_name}
                onChange={(e) => setFormData({ ...formData, business_name: e.target.value })}
                className="w-full px-4 py-3 rounded-xl border-2 border-earth-200 focus:border-primary-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-sm font-bold text-earth-700 mb-2">Contact Person</label>
              <input
                type="text"
                value={formData.contact_person}
                onChange={(e) => setFormData({ ...formData, contact_person: e.target.value })}
                className="w-full px-4 py-3 rounded-xl border-2 border-earth-200 focus:border-primary-500 focus:outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-bold text-earth-700 mb-2">Physical Address</label>
            <input
              type="text"
              value={formData.physical_address}
              onChange={(e) => setFormData({ ...formData, physical_address: e.target.value })}
              className="w-full px-4 py-3 rounded-xl border-2 border-earth-200 focus:border-primary-500 focus:outline-none"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-bold text-earth-700 mb-2">Phone</label>
              <input
                type="tel"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                className="w-full px-4 py-3 rounded-xl border-2 border-earth-200 focus:border-primary-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-sm font-bold text-earth-700 mb-2">Email</label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="w-full px-4 py-3 rounded-xl border-2 border-earth-200 focus:border-primary-500 focus:outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-bold text-earth-700 mb-2">Business Hours</label>
            <input
              type="text"
              value={formData.business_hours}
              onChange={(e) => setFormData({ ...formData, business_hours: e.target.value })}
              placeholder="e.g., Mon-Fri 8am-5pm"
              className="w-full px-4 py-3 rounded-xl border-2 border-earth-200 focus:border-primary-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-sm font-bold text-earth-700 mb-2">Shipping Policy</label>
            <textarea
              value={formData.shipping_policy}
              onChange={(e) => setFormData({ ...formData, shipping_policy: e.target.value })}
              className="w-full px-4 py-3 rounded-xl border-2 border-earth-200 focus:border-primary-500 focus:outline-none"
              rows={3}
            />
          </div>

          <div>
            <label className="block text-sm font-bold text-earth-700 mb-2">Return Policy</label>
            <textarea
              value={formData.return_policy}
              onChange={(e) => setFormData({ ...formData, return_policy: e.target.value })}
              className="w-full px-4 py-3 rounded-xl border-2 border-earth-200 focus:border-primary-500 focus:outline-none"
              rows={3}
            />
          </div>

          <button
            type="submit"
            disabled={saving}
            className="flex items-center gap-2 bg-primary-600 hover:bg-primary-700 text-white font-bold px-6 py-3 rounded-xl disabled:opacity-50"
          >
            <Save className="w-5 h-5" /> {saving ? 'Saving...' : 'Save Changes'}
          </button>
        </form>
      </div>

      {/* Document Upload Modal */}
      {showDocUpload && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-md w-full p-6">
            <h3 className="text-xl font-black text-earth-800 mb-4">Upload Documents</h3>
            <form onSubmit={handleDocUpload} className="space-y-4">
              <div>
                <label className="block text-sm font-bold text-earth-700 mb-1">Document Type</label>
                <select
                  className="w-full px-3 py-2 rounded-lg border-2 border-earth-200 focus:border-primary-500 focus:outline-none"
                  onChange={(e) => setDocFiles([{ ...docFiles[0] || {}, type: e.target.value }])}
                >
                  <option value="">Select type...</option>
                  <option value="certificate_of_incorporation">Certificate of Incorporation</option>
                  <option value="tax_clearance">Tax Clearance</option>
                  <option value="trade_license">Trade License</option>
                  <option value="product_registration">Product Registration</option>
                  <option value="bank_details">Bank Details</option>
                  <option value="store_photos">Store Photos</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-bold text-earth-700 mb-1">Document URL</label>
                <input
                  type="url"
                  placeholder="https://..."
                  className="w-full px-3 py-2 rounded-lg border-2 border-earth-200 focus:border-primary-500 focus:outline-none"
                  onChange={(e) => setDocFiles([{ ...docFiles[0] || {}, url: e.target.value }])}
                />
              </div>
              <div>
                <label className="block text-sm font-bold text-earth-700 mb-1">Document Name</label>
                <input
                  type="text"
                  className="w-full px-3 py-2 rounded-lg border-2 border-earth-200 focus:border-primary-500 focus:outline-none"
                  onChange={(e) => setDocFiles([{ ...docFiles[0] || {}, name: e.target.value }])}
                />
              </div>
              <div className="flex gap-3 mt-6">
                <button type="submit" className="flex-1 bg-primary-600 hover:bg-primary-700 text-white font-bold py-2 rounded-xl">
                  Upload
                </button>
                <button type="button" onClick={() => setShowDocUpload(false)} className="flex-1 bg-earth-200 hover:bg-earth-300 text-earth-800 font-bold py-2 rounded-xl">
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
