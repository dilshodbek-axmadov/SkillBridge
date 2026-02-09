import { useState, useRef, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  Zap, Upload, FileText, X, Loader2, CheckCircle2, AlertCircle,
  ArrowRight, ArrowLeft, Trash2, Plus, ChevronDown, Check, Brain,
  Sparkles, Search,
} from 'lucide-react';
import api from '../services/api';

const EXPERIENCE_LEVELS = [
  { value: 'beginner', label: 'Beginner' },
  { value: 'junior', label: 'Junior' },
  { value: 'mid', label: 'Mid-level' },
  { value: 'senior', label: 'Senior' },
  { value: 'lead', label: 'Lead / Principal' },
];

const PROFICIENCY_OPTIONS = [
  { value: 'beginner', label: 'Beginner' },
  { value: 'intermediate', label: 'Intermediate' },
  { value: 'advanced', label: 'Advanced' },
  { value: 'expert', label: 'Expert' },
];

// ─── Phase 1: Upload ────────────────────────────────────────────

function UploadPhase({ onFileSelected, error }) {
  const fileInputRef = useRef(null);
  const [dragOver, setDragOver] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);

  const validateFile = (file) => {
    const ext = file.name.split('.').pop().toLowerCase();
    if (!['pdf', 'docx', 'doc'].includes(ext)) {
      return 'Please upload a PDF or DOCX file.';
    }
    if (file.size > 5 * 1024 * 1024) {
      return 'File size must be under 5MB.';
    }
    return null;
  };

  const handleFile = (file) => {
    if (!file) return;
    const err = validateFile(file);
    if (err) {
      onFileSelected(null, err);
      return;
    }
    setSelectedFile(file);
    onFileSelected(file, null);
  };

  const formatSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-2">
          Upload Your CV
        </h2>
        <p className="text-gray-500">
          Our AI will extract your skills and experience automatically.
        </p>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {/* Drop zone */}
      {!selectedFile ? (
        <div
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragOver(false);
            handleFile(e.dataTransfer.files?.[0]);
          }}
          onClick={() => fileInputRef.current?.click()}
          className={`w-full border-2 border-dashed rounded-2xl p-12 text-center transition-all cursor-pointer ${
            dragOver
              ? 'border-primary-400 bg-primary-50'
              : 'border-gray-300 hover:border-primary-300 hover:bg-gray-50'
          }`}
        >
          <div className="w-16 h-16 bg-primary-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <Upload className="w-8 h-8 text-primary-600" />
          </div>
          <p className="text-lg font-semibold text-gray-700 mb-1">
            Drag & drop your CV here
          </p>
          <p className="text-sm text-gray-400 mb-4">
            or click to browse files
          </p>
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-gray-100 rounded-full">
            <FileText className="w-4 h-4 text-gray-500" />
            <span className="text-xs text-gray-500 font-medium">
              PDF, DOC, DOCX — Max 5MB
            </span>
          </div>
        </div>
      ) : (
        /* File preview */
        <div className="p-5 bg-gray-50 border border-gray-200 rounded-2xl">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-primary-100 rounded-xl flex items-center justify-center flex-shrink-0">
              <FileText className="w-6 h-6 text-primary-600" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-gray-900 truncate">
                {selectedFile.name}
              </p>
              <p className="text-xs text-gray-400">
                {formatSize(selectedFile.size)}
              </p>
            </div>
            <button
              onClick={(e) => {
                e.stopPropagation();
                setSelectedFile(null);
                onFileSelected(null, null);
              }}
              className="p-2 rounded-lg hover:bg-red-50 text-gray-400 hover:text-red-500 transition-colors bg-transparent border-none cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>
      )}

      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.docx,.doc"
        onChange={(e) => handleFile(e.target.files?.[0])}
        className="hidden"
      />
    </div>
  );
}

// ─── Phase 2: Processing ────────────────────────────────────────

function ProcessingPhase({ progress }) {
  const steps = [
    'Reading document...',
    'Extracting text content...',
    'Identifying skills...',
    'Matching job position...',
    'Calculating experience level...',
    'Finalizing profile...',
  ];

  const currentStep = Math.min(
    Math.floor((progress / 100) * steps.length),
    steps.length - 1
  );

  return (
    <div className="text-center space-y-8 py-8">
      {/* Animated AI icon */}
      <div className="relative w-24 h-24 mx-auto">
        <div className="absolute inset-0 bg-primary-100 rounded-full animate-ping opacity-30" />
        <div className="absolute inset-2 bg-primary-200 rounded-full animate-pulse" />
        <div className="relative w-24 h-24 bg-gradient-to-br from-primary-500 to-purple-500 rounded-full flex items-center justify-center">
          <Brain className="w-10 h-10 text-white" />
        </div>
      </div>

      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Analyzing your CV with AI...
        </h2>
        <p className="text-gray-500">
          {steps[currentStep]}
        </p>
      </div>

      {/* Progress bar */}
      <div className="max-w-xs mx-auto">
        <div className="w-full bg-gray-200 rounded-full h-2.5">
          <div
            className="bg-gradient-to-r from-primary-500 to-purple-500 h-2.5 rounded-full transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
        <div className="flex items-center justify-between mt-2">
          <span className="text-sm font-semibold text-primary-600">{progress}%</span>
          <span className="text-xs text-gray-400">
            ~{Math.max(5, Math.round((100 - progress) * 0.3))}s remaining
          </span>
        </div>
      </div>

      {/* Step indicators */}
      <div className="max-w-sm mx-auto space-y-2">
        {steps.map((step, idx) => (
          <div
            key={idx}
            className={`flex items-center gap-3 px-4 py-2 rounded-lg transition-all ${
              idx < currentStep
                ? 'bg-green-50'
                : idx === currentStep
                  ? 'bg-primary-50'
                  : 'opacity-40'
            }`}
          >
            {idx < currentStep ? (
              <CheckCircle2 className="w-4 h-4 text-green-500 flex-shrink-0" />
            ) : idx === currentStep ? (
              <Loader2 className="w-4 h-4 text-primary-500 animate-spin flex-shrink-0" />
            ) : (
              <div className="w-4 h-4 rounded-full border-2 border-gray-300 flex-shrink-0" />
            )}
            <span className={`text-sm ${
              idx <= currentStep ? 'text-gray-700 font-medium' : 'text-gray-400'
            }`}>
              {step}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Phase 3: Review ────────────────────────────────────────────

function ReviewPhase({ profileData, onConfirm, onEditManually, confirming }) {
  const [jobPosition, setJobPosition] = useState(profileData.job_position || '');
  const [experienceLevel, setExperienceLevel] = useState(profileData.experience_level || 'beginner');
  const [skills, setSkills] = useState(profileData.skills || []);
  const [years, setYears] = useState(profileData.years || 0);

  // Skill search
  const [skillSearch, setSkillSearch] = useState('');
  const [skillResults, setSkillResults] = useState([]);
  const [searchingSkills, setSearchingSkills] = useState(false);
  const [showSkillSearch, setShowSkillSearch] = useState(false);
  const searchTimeout = useRef(null);

  useEffect(() => {
    if (searchTimeout.current) clearTimeout(searchTimeout.current);
    if (!skillSearch.trim()) {
      setSkillResults([]);
      setSearchingSkills(false);
      return;
    }
    setSearchingSkills(true);
    searchTimeout.current = setTimeout(async () => {
      try {
        const { data } = await api.get('/users/skills/search/', {
          params: { q: skillSearch.trim(), verified_only: 'false' },
        });
        const existingIds = new Set(skills.map((s) => s.skill_id));
        setSkillResults(
          (data.skills || []).filter((s) => !existingIds.has(s.skill_id))
        );
      } catch {
        // ignore
      } finally {
        setSearchingSkills(false);
      }
    }, 300);
    return () => { if (searchTimeout.current) clearTimeout(searchTimeout.current); };
  }, [skillSearch, skills]);

  const handleConfirm = () => {
    onConfirm({
      current_job_position: jobPosition,
      experience_level: experienceLevel,
      skills: skills.map((s) => ({
        skill_id: s.skill_id,
        proficiency_level: s.proficiency_level || 'intermediate',
        years_of_experience: years,
      })),
    });
  };

  const removeSkill = (skillId) => {
    setSkills((prev) => prev.filter((s) => s.skill_id !== skillId));
  };

  const addSkill = (skill) => {
    setSkills((prev) => [...prev, { ...skill, proficiency_level: 'intermediate' }]);
    setSkillSearch('');
    setShowSkillSearch(false);
  };

  const updateProficiency = (skillId, level) => {
    setSkills((prev) =>
      prev.map((s) => s.skill_id === skillId ? { ...s, proficiency_level: level } : s)
    );
  };

  return (
    <div className="space-y-6">
      {/* Success banner */}
      <div className="p-4 bg-green-50 border border-green-200 rounded-xl flex items-start gap-3">
        <Sparkles className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
        <div>
          <p className="text-sm font-semibold text-green-700">
            CV analyzed successfully!
          </p>
          <p className="text-xs text-green-600 mt-0.5">
            Review the extracted information below and make any corrections.
          </p>
        </div>
      </div>

      <h2 className="text-xl font-bold text-gray-900">
        We found the following information
      </h2>

      {/* Job Position */}
      <div className="bg-white border border-gray-200 rounded-xl p-5">
        <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">
          Job Position
        </label>
        <input
          type="text"
          value={jobPosition}
          onChange={(e) => setJobPosition(e.target.value)}
          className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl text-base focus:outline-none focus:border-primary-500 transition-colors"
          placeholder="e.g. Backend Developer"
        />
      </div>

      {/* Experience Level */}
      <div className="bg-white border border-gray-200 rounded-xl p-5">
        <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">
          Experience Level
        </label>
        <div className="relative">
          <select
            value={experienceLevel}
            onChange={(e) => setExperienceLevel(e.target.value)}
            className="w-full appearance-none px-4 py-3 border-2 border-gray-200 rounded-xl text-base bg-white focus:outline-none focus:border-primary-500 transition-colors cursor-pointer pr-10"
          >
            {EXPERIENCE_LEVELS.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
          <ChevronDown className="absolute right-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
        </div>
      </div>

      {/* Years of Experience */}
      <div className="bg-white border border-gray-200 rounded-xl p-5">
        <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">
          Years of Experience
        </label>
        <input
          type="number"
          min="0"
          max="30"
          step="0.5"
          value={years}
          onChange={(e) => setYears(parseFloat(e.target.value) || 0)}
          className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl text-base focus:outline-none focus:border-primary-500 transition-colors"
        />
      </div>

      {/* Skills */}
      <div className="bg-white border border-gray-200 rounded-xl p-5">
        <div className="flex items-center justify-between mb-3">
          <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wide">
            Skills ({skills.length})
          </label>
          <button
            onClick={() => setShowSkillSearch(!showSkillSearch)}
            className="flex items-center gap-1 text-xs font-semibold text-primary-600 hover:text-primary-700 bg-transparent border-none cursor-pointer"
          >
            <Plus className="w-3.5 h-3.5" />
            Add more
          </button>
        </div>

        {/* Add skill search */}
        {showSkillSearch && (
          <div className="mb-4 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={skillSearch}
              onChange={(e) => setSkillSearch(e.target.value)}
              placeholder="Search skills to add..."
              className="w-full pl-10 pr-4 py-2.5 border-2 border-gray-200 rounded-lg text-sm focus:outline-none focus:border-primary-500 transition-colors"
              autoFocus
            />
            {searchingSkills && (
              <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-primary-500 animate-spin" />
            )}
            {skillResults.length > 0 && (
              <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-40 overflow-y-auto">
                {skillResults.map((skill) => (
                  <button
                    key={skill.skill_id}
                    onClick={() => addSkill(skill)}
                    className="w-full text-left px-4 py-2 text-sm hover:bg-primary-50 transition-colors border-none bg-transparent cursor-pointer text-gray-700"
                  >
                    {skill.name_en}
                    <span className="text-xs text-gray-400 ml-2">{skill.category}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Skill chips */}
        {skills.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {skills.map((skill) => (
              <div
                key={skill.skill_id}
                className="flex items-center gap-1.5 bg-primary-50 border border-primary-200 rounded-lg pl-3 pr-1 py-1.5"
              >
                <span className="text-sm font-medium text-primary-700">
                  {skill.name_en}
                </span>
                <div className="relative">
                  <select
                    value={skill.proficiency_level || 'intermediate'}
                    onChange={(e) => updateProficiency(skill.skill_id, e.target.value)}
                    className="appearance-none bg-primary-100 text-xs text-primary-600 font-medium rounded px-2 py-0.5 pr-5 border-none cursor-pointer focus:outline-none"
                  >
                    {PROFICIENCY_OPTIONS.map((opt) => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                  <ChevronDown className="absolute right-1 top-1/2 -translate-y-1/2 w-3 h-3 text-primary-400 pointer-events-none" />
                </div>
                <button
                  onClick={() => removeSkill(skill.skill_id)}
                  className="p-1 rounded-full hover:bg-red-50 text-gray-400 hover:text-red-500 transition-colors bg-transparent border-none cursor-pointer"
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-400 text-center py-4">
            No skills extracted. Add skills manually.
          </p>
        )}
      </div>

      {/* Actions */}
      <div className="space-y-3">
        <button
          onClick={handleConfirm}
          disabled={confirming || !jobPosition.trim()}
          className="w-full flex items-center justify-center gap-2 px-6 py-3.5 text-sm font-semibold text-white bg-primary-600 rounded-xl hover:bg-primary-700 disabled:bg-primary-400 transition-colors cursor-pointer border-none"
        >
          {confirming ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Saving...
            </>
          ) : (
            <>
              <Check className="w-4 h-4" />
              Looks good — Save & Continue
            </>
          )}
        </button>
        <button
          onClick={onEditManually}
          className="w-full text-center text-sm text-gray-500 hover:text-primary-600 transition-colors bg-transparent border-none cursor-pointer py-2"
        >
          Edit manually instead
        </button>
      </div>
    </div>
  );
}

// ─── Main Page ──────────────────────────────────────────────────

export default function CVUploadPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const finalRedirect = searchParams.get('redirect') || '/dashboard';

  const [phase, setPhase] = useState('upload'); // upload | processing | review
  const [file, setFile] = useState(null);
  const [uploadError, setUploadError] = useState('');
  const [progress, setProgress] = useState(0);
  const [extractedData, setExtractedData] = useState(null);
  const [confirming, setConfirming] = useState(false);
  const progressInterval = useRef(null);

  const handleFileSelected = (selectedFile, error) => {
    if (error) {
      setUploadError(error);
      setFile(null);
      return;
    }
    setUploadError('');
    setFile(selectedFile);
  };

  const startUpload = async () => {
    if (!file) return;

    setPhase('processing');
    setProgress(0);

    // Simulate progress while uploading
    progressInterval.current = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 90) {
          clearInterval(progressInterval.current);
          return 90;
        }
        return prev + Math.random() * 8 + 2;
      });
    }, 500);

    try {
      const formData = new FormData();
      formData.append('cv_file', file);

      const { data } = await api.post('/users/profile/cv-upload/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      clearInterval(progressInterval.current);
      setProgress(100);

      // Fetch the updated profile to show in review
      const profileRes = await api.get('/users/profile/summary/');
      const profile = profileRes.data;

      const extracted = {
        job_position: profile.profile?.current_job_position || data.extraction?.job_position || '',
        experience_level: profile.profile?.experience_level || 'beginner',
        years: data.extraction?.years || 0,
        skills: (profile.skills?.list || []).map((s) => ({
          skill_id: s.user_skill_id, // we'll use what's available
          name_en: s.name_en,
          proficiency_level: s.proficiency,
          category: s.category,
        })),
        skills_found: data.extraction?.skills_found || 0,
        quality: data.extraction?.quality,
      };

      // Map skills correctly - use actual skill objects from browse endpoint
      if (profile.skills?.list?.length > 0) {
        // Skills are already added to profile by backend, just show them
        extracted.skills = profile.skills.list.map((s) => ({
          skill_id: s.user_skill_id,
          name_en: s.name_en,
          proficiency_level: s.proficiency,
          category: s.category,
        }));
      }

      setExtractedData(extracted);

      setTimeout(() => setPhase('review'), 600);
    } catch (err) {
      clearInterval(progressInterval.current);
      const msg =
        err.response?.data?.cv_file?.[0] ||
        err.response?.data?.error ||
        err.response?.data?.detail ||
        'Failed to process CV. Please try again.';
      setUploadError(msg);
      setPhase('upload');
    }
  };

  const handleConfirm = async (editedData) => {
    setConfirming(true);
    try {
      // Update profile with any edits the user made
      await api.patch('/users/profile/', {
        current_job_position: editedData.current_job_position,
        experience_level: editedData.experience_level,
      });

      navigate(finalRedirect);
    } catch {
      // Even if update fails, profile was already created from CV
      navigate(finalRedirect);
    }
  };

  const handleEditManually = () => {
    navigate(`/profile-manual?redirect=${encodeURIComponent(finalRedirect)}`);
  };

  useEffect(() => {
    return () => {
      if (progressInterval.current) clearInterval(progressInterval.current);
    };
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-4 sm:px-6 lg:px-8 py-4">
        <div className="max-w-2xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gradient-to-br from-primary-600 to-purple-500 rounded-lg flex items-center justify-center">
              <Zap className="w-4 h-4 text-white" />
            </div>
            <span className="text-sm font-semibold text-gray-900">
              Skill<span className="text-primary-600">Bridge</span>
            </span>
          </div>
          {phase === 'upload' && (
            <button
              onClick={() => navigate(-1)}
              className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 bg-transparent border-none cursor-pointer"
            >
              <ArrowLeft className="w-4 h-4" />
              Back
            </button>
          )}
        </div>
      </header>

      {/* Main */}
      <main className="flex-1 flex items-center justify-center px-4 sm:px-6 py-8 sm:py-12">
        <div className="w-full max-w-2xl">
          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 sm:p-8">
            {phase === 'upload' && (
              <>
                <UploadPhase
                  onFileSelected={handleFileSelected}
                  error={uploadError}
                />
                {file && (
                  <div className="mt-6">
                    <button
                      onClick={startUpload}
                      className="w-full flex items-center justify-center gap-2 px-6 py-3.5 text-sm font-semibold text-white bg-gradient-to-r from-primary-600 to-purple-500 rounded-xl hover:from-primary-700 hover:to-purple-600 transition-all cursor-pointer border-none"
                    >
                      <Sparkles className="w-4 h-4" />
                      Analyze with AI
                      <ArrowRight className="w-4 h-4" />
                    </button>
                  </div>
                )}
              </>
            )}

            {phase === 'processing' && (
              <ProcessingPhase progress={Math.round(progress)} />
            )}

            {phase === 'review' && extractedData && (
              <ReviewPhase
                profileData={extractedData}
                onConfirm={handleConfirm}
                onEditManually={handleEditManually}
                confirming={confirming}
              />
            )}
          </div>

          {/* Skip link */}
          {phase === 'upload' && (
            <div className="text-center mt-6">
              <button
                onClick={() => navigate(finalRedirect)}
                className="text-sm text-gray-400 hover:text-gray-600 transition-colors bg-transparent border-none cursor-pointer underline"
              >
                Skip for now
              </button>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
