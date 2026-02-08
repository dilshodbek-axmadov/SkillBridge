import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Zap, FileText, Upload, Clock, ArrowRight, Loader2, CheckCircle2, AlertCircle, Sparkles } from 'lucide-react';
import api from '../services/api';

export default function ProfileChoicePage() {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);

  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [uploadError, setUploadError] = useState('');
  const [dragOver, setDragOver] = useState(false);

  const handleCVUpload = async (file) => {
    if (!file) return;

    // Validate file type
    const ext = file.name.split('.').pop().toLowerCase();
    if (!['pdf', 'docx', 'doc'].includes(ext)) {
      setUploadError('Please upload a PDF or DOCX file.');
      return;
    }

    // Validate file size (5MB)
    if (file.size > 5 * 1024 * 1024) {
      setUploadError('File size must be under 5MB.');
      return;
    }

    setUploading(true);
    setUploadError('');

    try {
      const formData = new FormData();
      formData.append('cv_file', file);

      const { data } = await api.post('/users/profile/cv-upload/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      setUploadResult(data);

      // Auto-navigate to assessment after 2 seconds
      setTimeout(() => {
        navigate('/assessment');
      }, 2500);
    } catch (err) {
      const msg =
        err.response?.data?.cv_file?.[0] ||
        err.response?.data?.error ||
        err.response?.data?.detail ||
        'Failed to upload CV. Please try again.';
      setUploadError(msg);
    } finally {
      setUploading(false);
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files?.[0];
    if (file) handleCVUpload(file);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) handleCVUpload(file);
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-4 sm:px-6 lg:px-8 py-4">
        <div className="max-w-4xl mx-auto flex items-center gap-2">
          <div className="w-8 h-8 bg-gradient-to-br from-primary-600 to-purple-500 rounded-lg flex items-center justify-center">
            <Zap className="w-4 h-4 text-white" />
          </div>
          <span className="text-sm font-semibold text-gray-900">
            Skill<span className="text-primary-600">Bridge</span>
          </span>
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1 flex items-center justify-center px-4 sm:px-6 py-12">
        <div className="w-full max-w-3xl">
          {/* Heading */}
          <div className="text-center mb-10">
            <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-3">
              How would you like to create your profile?
            </h1>
            <p className="text-gray-500 text-lg max-w-xl mx-auto">
              We need to know your skills and experience to give you personalized career recommendations.
            </p>
          </div>

          {/* Option cards */}
          <div className="grid sm:grid-cols-2 gap-5 sm:gap-6">
            {/* Manual Entry */}
            <div className="bg-white rounded-2xl border-2 border-gray-200 hover:border-primary-300 hover:shadow-lg transition-all p-7 sm:p-8 flex flex-col">
              <div className="w-14 h-14 bg-primary-50 rounded-xl flex items-center justify-center mb-5">
                <FileText className="w-7 h-7 text-primary-600" />
              </div>

              <h2 className="text-xl font-bold text-gray-900 mb-2">Fill Step-by-Step Form</h2>
              <p className="text-gray-500 text-sm leading-relaxed mb-4 flex-1">
                Answer a few questions about your current skills, experience level, and career goals.
              </p>

              <div className="flex items-center gap-1.5 text-gray-400 text-xs mb-5">
                <Clock className="w-3.5 h-3.5" />
                <span>~5 minutes</span>
              </div>

              <button
                onClick={() => navigate('/profile-manual')}
                className="w-full flex items-center justify-center gap-2 px-5 py-3 bg-primary-600 text-white rounded-xl text-sm font-semibold hover:bg-primary-700 transition-colors cursor-pointer border-none"
              >
                Start Manual Entry
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>

            {/* CV Upload */}
            <div className="bg-white rounded-2xl border-2 border-gray-200 hover:border-purple-300 hover:shadow-lg transition-all p-7 sm:p-8 flex flex-col">
              <div className="w-14 h-14 bg-purple-50 rounded-xl flex items-center justify-center mb-5">
                <Sparkles className="w-7 h-7 text-purple-600" />
              </div>

              <h2 className="text-xl font-bold text-gray-900 mb-2">Upload Your CV</h2>
              <p className="text-gray-500 text-sm leading-relaxed mb-4 flex-1">
                Let our AI extract your skills and experience automatically from your resume.
              </p>

              <div className="flex items-center gap-1.5 text-gray-400 text-xs mb-5">
                <Clock className="w-3.5 h-3.5" />
                <span>~2 minutes</span>
              </div>

              {/* Upload result */}
              {uploadResult && (
                <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg">
                  <div className="flex items-center gap-2 mb-1">
                    <CheckCircle2 className="w-4 h-4 text-green-600" />
                    <span className="text-sm font-semibold text-green-700">CV Processed Successfully</span>
                  </div>
                  <p className="text-xs text-green-600 ml-6">
                    Found {uploadResult.extraction?.skills_found || 0} skills.
                    Redirecting to assessment...
                  </p>
                </div>
              )}

              {/* Upload error */}
              {uploadError && (
                <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2">
                  <AlertCircle className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" />
                  <span className="text-sm text-red-600">{uploadError}</span>
                </div>
              )}

              {/* Drop zone / Upload button */}
              {!uploadResult && (
                <div
                  onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                  onDragLeave={() => setDragOver(false)}
                  onDrop={handleDrop}
                  className={`w-full border-2 border-dashed rounded-xl p-4 text-center transition-colors mb-3 ${
                    dragOver
                      ? 'border-purple-400 bg-purple-50'
                      : 'border-gray-300 hover:border-purple-300'
                  }`}
                >
                  {uploading ? (
                    <div className="flex flex-col items-center gap-2 py-2">
                      <Loader2 className="w-6 h-6 text-purple-500 animate-spin" />
                      <span className="text-sm text-purple-600 font-medium">Processing your CV...</span>
                    </div>
                  ) : (
                    <>
                      <Upload className="w-6 h-6 text-gray-400 mx-auto mb-2" />
                      <p className="text-sm text-gray-500">
                        Drag & drop your CV here
                      </p>
                      <p className="text-xs text-gray-400 mt-1">PDF, DOCX — max 5MB</p>
                    </>
                  )}
                </div>
              )}

              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.docx,.doc"
                onChange={handleFileSelect}
                className="hidden"
              />

              {!uploadResult && (
                <button
                  onClick={() => fileInputRef.current?.click()}
                  disabled={uploading}
                  className="w-full flex items-center justify-center gap-2 px-5 py-3 bg-purple-600 text-white rounded-xl text-sm font-semibold hover:bg-purple-700 disabled:bg-purple-400 transition-colors cursor-pointer border-none"
                >
                  {uploading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Uploading...
                    </>
                  ) : (
                    <>
                      <Upload className="w-4 h-4" />
                      Upload CV
                    </>
                  )}
                </button>
              )}
            </div>
          </div>

          {/* Skip link */}
          <div className="text-center mt-8">
            <button
              onClick={() => navigate('/assessment')}
              className="text-sm text-gray-400 hover:text-gray-600 transition-colors bg-transparent border-none cursor-pointer underline"
            >
              I&apos;ll do this later
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
