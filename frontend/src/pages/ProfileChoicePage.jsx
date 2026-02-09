import { useNavigate, useSearchParams } from 'react-router-dom';
import { Zap, FileText, Upload, Clock, ArrowRight, Sparkles } from 'lucide-react';

export default function ProfileChoicePage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const finalRedirect = searchParams.get('redirect') || '/dashboard';

  const redirectParam = `?redirect=${encodeURIComponent(finalRedirect)}`;

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
                onClick={() => navigate(`/profile-manual${redirectParam}`)}
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

              <button
                onClick={() => navigate(`/profile-cv${redirectParam}`)}
                className="w-full flex items-center justify-center gap-2 px-5 py-3 bg-purple-600 text-white rounded-xl text-sm font-semibold hover:bg-purple-700 transition-colors cursor-pointer border-none"
              >
                <Upload className="w-4 h-4" />
                Upload CV
              </button>
            </div>
          </div>

          {/* Skip link */}
          <div className="text-center mt-8">
            <button
              onClick={() => navigate(finalRedirect)}
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
