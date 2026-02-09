import { useState, useEffect, useRef, useMemo } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  Zap, ArrowLeft, ArrowRight, Check, Loader2, Search,
  X, ChevronDown, Briefcase, BarChart3, Code2, Heart,
  AlertCircle,
} from 'lucide-react';
import api from '../services/api';

const STEPS = [
  { id: 1, label: 'Job Position' },
  { id: 2, label: 'Experience' },
  { id: 3, label: 'Skills' },
  { id: 4, label: 'Interests' },
];

const EXPERIENCE_LEVELS = [
  {
    value: 'beginner',
    label: 'Beginner',
    description: 'New to IT. Learning the basics, no professional experience yet.',
    icon: '🌱',
  },
  {
    value: 'junior',
    label: 'Junior',
    description: '0–1 years of experience. Building foundational skills.',
    icon: '🚀',
  },
  {
    value: 'mid',
    label: 'Mid-level',
    description: '2–4 years of experience. Can work independently on tasks.',
    icon: '💼',
  },
  {
    value: 'senior',
    label: 'Senior',
    description: '5+ years of experience. Leads projects and mentors others.',
    icon: '⭐',
  },
  {
    value: 'lead',
    label: 'Lead / Principal',
    description: '7+ years. Drives architecture and team-level decisions.',
    icon: '👑',
  },
];

const PROFICIENCY_OPTIONS = [
  { value: 'beginner', label: 'Beginner' },
  { value: 'intermediate', label: 'Intermediate' },
  { value: 'advanced', label: 'Advanced' },
  { value: 'expert', label: 'Expert' },
];

const STEP_ICONS = [Briefcase, BarChart3, Code2, Heart];

// ─── Step 1: Job Position ────────────────────────────────────────

const COMMON_POSITIONS = [
  'Backend Developer', 'Frontend Developer', 'Full-Stack Developer',
  'Mobile Developer', 'DevOps Engineer', 'Data Scientist',
  'Data Analyst', 'UI/UX Designer', 'QA Engineer',
  'Machine Learning Engineer', 'Cloud Engineer', 'Cybersecurity Analyst',
  'Product Manager', 'Project Manager', 'System Administrator',
];

function StepJobPosition({ value, onChange }) {
  const [query, setQuery] = useState(value);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const wrapperRef = useRef(null);

  const suggestions = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return COMMON_POSITIONS;
    return COMMON_POSITIONS.filter((p) => p.toLowerCase().includes(q));
  }, [query]);

  useEffect(() => {
    function handleClickOutside(e) {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
        setShowSuggestions(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (pos) => {
    setQuery(pos);
    onChange(pos);
    setShowSuggestions(false);
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-2">
          What's your current or desired role?
        </h2>
        <p className="text-gray-500">
          Choose from common IT positions or type your own.
        </p>
      </div>

      <div className="relative" ref={wrapperRef}>
        <div className="relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              onChange(e.target.value);
              setShowSuggestions(true);
            }}
            onFocus={() => setShowSuggestions(true)}
            placeholder="e.g. Backend Developer"
            className="w-full pl-12 pr-4 py-4 border-2 border-gray-200 rounded-xl text-lg focus:outline-none focus:border-primary-500 transition-colors"
          />
          {query && (
            <button
              onClick={() => { setQuery(''); onChange(''); }}
              className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 bg-transparent border-none cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>

        {showSuggestions && suggestions.length > 0 && (
          <div className="absolute z-10 w-full mt-2 bg-white border border-gray-200 rounded-xl shadow-lg max-h-64 overflow-y-auto">
            {suggestions.map((pos) => (
              <button
                key={pos}
                onClick={() => handleSelect(pos)}
                className={`w-full text-left px-4 py-3 text-sm hover:bg-primary-50 transition-colors border-none bg-transparent cursor-pointer ${
                  pos === value ? 'bg-primary-50 text-primary-700 font-semibold' : 'text-gray-700'
                }`}
              >
                {pos}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Quick-pick chips */}
      <div>
        <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">
          Popular choices
        </p>
        <div className="flex flex-wrap gap-2">
          {COMMON_POSITIONS.slice(0, 8).map((pos) => (
            <button
              key={pos}
              onClick={() => handleSelect(pos)}
              className={`px-4 py-2 rounded-full text-sm font-medium border-2 transition-all cursor-pointer ${
                pos === value
                  ? 'border-primary-500 bg-primary-50 text-primary-700'
                  : 'border-gray-200 bg-white text-gray-600 hover:border-primary-300'
              }`}
            >
              {pos}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── Step 2: Experience Level ────────────────────────────────────

function StepExperience({ value, onChange }) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-2">
          What's your experience level?
        </h2>
        <p className="text-gray-500">
          This helps us tailor recommendations to your career stage.
        </p>
      </div>

      <div className="space-y-3">
        {EXPERIENCE_LEVELS.map((level) => {
          const isSelected = value === level.value;
          return (
            <button
              key={level.value}
              onClick={() => onChange(level.value)}
              className={`w-full text-left p-5 rounded-xl border-2 transition-all cursor-pointer bg-white ${
                isSelected
                  ? 'border-primary-500 shadow-md shadow-primary-100'
                  : 'border-gray-200 hover:border-primary-300 hover:shadow-sm'
              }`}
            >
              <div className="flex items-start gap-4">
                <span className="text-2xl">{level.icon}</span>
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <span className={`font-semibold text-base ${isSelected ? 'text-primary-700' : 'text-gray-900'}`}>
                      {level.label}
                    </span>
                    {isSelected && (
                      <div className="w-6 h-6 bg-primary-600 rounded-full flex items-center justify-center">
                        <Check className="w-4 h-4 text-white" />
                      </div>
                    )}
                  </div>
                  <p className="text-sm text-gray-500 mt-1">{level.description}</p>
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

// ─── Step 3: Skills ──────────────────────────────────────────────

function StepSkills({ selected, onAdd, onRemove, onUpdateProficiency }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [allSkills, setAllSkills] = useState([]);
  const [categories, setCategories] = useState([]);
  const [activeCategory, setActiveCategory] = useState(null);
  const [loadingSkills, setLoadingSkills] = useState(true);
  const [searching, setSearching] = useState(false);
  const searchTimeout = useRef(null);

  // Load ALL skills (fetch every page) and categories
  useEffect(() => {
    const fetchData = async () => {
      try {
        const catsRes = await api.get('/users/skills/categories/');
        setCategories(catsRes.data.categories || []);

        // Fetch all pages of skills
        let page = 1;
        let accumulated = [];
        let hasNext = true;

        while (hasNext) {
          const res = await api.get('/users/skills/browse/', {
            params: { page, verified_only: 'false' },
          });
          const data = res.data;
          accumulated = [...accumulated, ...(data.skills || [])];
          hasNext = data.has_next;
          page++;
        }

        setAllSkills(accumulated);
      } catch {
        // fallback
      } finally {
        setLoadingSkills(false);
      }
    };
    fetchData();
  }, []);

  // Search with debounce
  useEffect(() => {
    if (searchTimeout.current) clearTimeout(searchTimeout.current);

    if (!searchQuery.trim()) {
      setSearchResults([]);
      setSearching(false);
      return;
    }

    setSearching(true);
    searchTimeout.current = setTimeout(async () => {
      try {
        const { data } = await api.get('/users/skills/search/', {
          params: { q: searchQuery.trim(), verified_only: 'false' },
        });
        setSearchResults(data.skills || []);
      } catch {
        // ignore
      } finally {
        setSearching(false);
      }
    }, 300);

    return () => {
      if (searchTimeout.current) clearTimeout(searchTimeout.current);
    };
  }, [searchQuery]);

  const displaySkills = searchQuery.trim()
    ? searchResults
    : activeCategory
      ? allSkills.filter((s) => s.category === activeCategory)
      : allSkills;

  const selectedIds = new Set(selected.map((s) => s.skill_id));

  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-2">
          What skills do you have?
        </h2>
        <p className="text-gray-500">
          Search or browse skills and set your proficiency level for each.
        </p>
      </div>

      {/* Selected skills chips */}
      {selected.length > 0 && (
        <div className="flex flex-wrap gap-2 p-4 bg-primary-50 rounded-xl border border-primary-100">
          {selected.map((skill) => (
            <div
              key={skill.skill_id}
              className="flex items-center gap-1.5 bg-white border border-primary-200 rounded-lg pl-3 pr-1 py-1"
            >
              <span className="text-sm font-medium text-primary-700">
                {skill.name_en}
              </span>

              {/* Proficiency dropdown */}
              <div className="relative">
                <select
                  value={skill.proficiency_level}
                  onChange={(e) => onUpdateProficiency(skill.skill_id, e.target.value)}
                  className="appearance-none bg-primary-50 text-xs text-primary-600 font-medium rounded px-2 py-1 pr-5 border-none cursor-pointer focus:outline-none"
                >
                  {PROFICIENCY_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
                <ChevronDown className="absolute right-1 top-1/2 -translate-y-1/2 w-3 h-3 text-primary-400 pointer-events-none" />
              </div>

              <button
                onClick={() => onRemove(skill.skill_id)}
                className="p-1 rounded-full hover:bg-red-50 text-gray-400 hover:text-red-500 transition-colors bg-transparent border-none cursor-pointer"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search skills (e.g. Python, React, Docker...)"
          className="w-full pl-12 pr-4 py-3.5 border-2 border-gray-200 rounded-xl text-sm focus:outline-none focus:border-primary-500 transition-colors"
        />
        {searching && (
          <Loader2 className="absolute right-4 top-1/2 -translate-y-1/2 w-4 h-4 text-primary-500 animate-spin" />
        )}
      </div>

      {/* Category tabs */}
      {!searchQuery.trim() && categories.length > 0 && (
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setActiveCategory(null)}
            className={`px-3 py-1.5 rounded-full text-xs font-semibold border transition-all cursor-pointer ${
              !activeCategory
                ? 'border-primary-500 bg-primary-50 text-primary-700'
                : 'border-gray-200 bg-white text-gray-500 hover:border-gray-300'
            }`}
          >
            All
          </button>
          {categories.map((cat) => (
            <button
              key={cat.value}
              onClick={() => setActiveCategory(cat.value)}
              className={`px-3 py-1.5 rounded-full text-xs font-semibold border transition-all cursor-pointer ${
                activeCategory === cat.value
                  ? 'border-primary-500 bg-primary-50 text-primary-700'
                  : 'border-gray-200 bg-white text-gray-500 hover:border-gray-300'
              }`}
            >
              {cat.label}
            </button>
          ))}
        </div>
      )}

      {/* Skills grid */}
      {loadingSkills ? (
        <div className="flex items-center justify-center py-10">
          <Loader2 className="w-6 h-6 text-primary-500 animate-spin" />
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 max-h-64 overflow-y-auto pr-1">
          {displaySkills.map((skill) => {
            const isAdded = selectedIds.has(skill.skill_id);
            return (
              <button
                key={skill.skill_id}
                onClick={() => {
                  if (isAdded) {
                    onRemove(skill.skill_id);
                  } else {
                    onAdd({
                      skill_id: skill.skill_id,
                      name_en: skill.name_en,
                      proficiency_level: 'beginner',
                    });
                  }
                }}
                className={`text-left px-3 py-2.5 rounded-lg border text-sm transition-all cursor-pointer ${
                  isAdded
                    ? 'border-primary-500 bg-primary-50 text-primary-700 font-semibold'
                    : 'border-gray-200 bg-white text-gray-700 hover:border-primary-300'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="truncate">{skill.name_en}</span>
                  {isAdded && <Check className="w-4 h-4 text-primary-600 flex-shrink-0" />}
                </div>
              </button>
            );
          })}
          {displaySkills.length === 0 && !loadingSkills && (
            <p className="col-span-full text-center text-gray-400 text-sm py-6">
              {searchQuery.trim() ? 'No skills found.' : 'No skills available.'}
            </p>
          )}
        </div>
      )}

      <p className="text-xs text-gray-400 text-center">
        {selected.length} skill{selected.length !== 1 ? 's' : ''} selected
      </p>
    </div>
  );
}

// ─── Step 4: Interests ───────────────────────────────────────────

function StepInterests({ selected, onToggle }) {
  const [allInterests, setAllInterests] = useState([]);
  const [categories, setCategories] = useState([]);
  const [activeCategory, setActiveCategory] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchInterests = async () => {
      try {
        const [interestsRes, catsRes] = await Promise.all([
          api.get('/interests/browse/'),
          api.get('/interests/categories/'),
        ]);
        setAllInterests(interestsRes.data.interests || []);
        setCategories(catsRes.data.categories || []);
      } catch {
        // fallback
      } finally {
        setLoading(false);
      }
    };
    fetchInterests();
  }, []);

  const CATEGORY_ICONS = {
    tech: '💻',
    design: '🎨',
    management: '📊',
    business: '💰',
    creative: '✨',
  };

  const displayInterests = activeCategory
    ? allInterests.filter((i) => i.category === activeCategory)
    : allInterests;

  const selectedSet = new Set(selected);

  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-2">
          What are your interests?
        </h2>
        <p className="text-gray-500">
          Optional — helps us suggest career paths that match your passions.
        </p>
      </div>

      {/* Category tabs */}
      {categories.length > 0 && (
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setActiveCategory(null)}
            className={`px-3 py-1.5 rounded-full text-xs font-semibold border transition-all cursor-pointer ${
              !activeCategory
                ? 'border-purple-500 bg-purple-50 text-purple-700'
                : 'border-gray-200 bg-white text-gray-500 hover:border-gray-300'
            }`}
          >
            All
          </button>
          {categories.map((cat) => (
            <button
              key={cat.code}
              onClick={() => setActiveCategory(cat.code)}
              className={`px-3 py-1.5 rounded-full text-xs font-semibold border transition-all cursor-pointer ${
                activeCategory === cat.code
                  ? 'border-purple-500 bg-purple-50 text-purple-700'
                  : 'border-gray-200 bg-white text-gray-500 hover:border-gray-300'
              }`}
            >
              {CATEGORY_ICONS[cat.code] || '📌'} {cat.name}
            </button>
          ))}
        </div>
      )}

      {/* Interest grid */}
      {loading ? (
        <div className="flex items-center justify-center py-10">
          <Loader2 className="w-6 h-6 text-purple-500 animate-spin" />
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {displayInterests.map((interest) => {
            const isSelected = selectedSet.has(interest.interest_id);
            return (
              <button
                key={interest.interest_id}
                onClick={() => onToggle(interest.interest_id)}
                className={`text-left p-4 rounded-xl border-2 transition-all cursor-pointer ${
                  isSelected
                    ? 'border-purple-500 bg-purple-50 shadow-sm'
                    : 'border-gray-200 bg-white hover:border-purple-300'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className={`text-sm font-medium ${isSelected ? 'text-purple-700' : 'text-gray-700'}`}>
                    {interest.name_en}
                  </span>
                  {isSelected && (
                    <div className="w-5 h-5 bg-purple-600 rounded-full flex items-center justify-center flex-shrink-0">
                      <Check className="w-3 h-3 text-white" />
                    </div>
                  )}
                </div>
                <span className="text-xs text-gray-400 mt-1 block capitalize">
                  {interest.category}
                </span>
              </button>
            );
          })}
          {displayInterests.length === 0 && !loading && (
            <p className="col-span-full text-center text-gray-400 text-sm py-6">
              No interests available.
            </p>
          )}
        </div>
      )}

      <p className="text-xs text-gray-400 text-center">
        {selected.length} interest{selected.length !== 1 ? 's' : ''} selected (optional)
      </p>
    </div>
  );
}

// ─── Main Page ───────────────────────────────────────────────────

export default function ManualProfilePage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const finalRedirect = searchParams.get('redirect') || '/dashboard';
  const [step, setStep] = useState(1);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  // Form data
  const [jobPosition, setJobPosition] = useState('');
  const [experienceLevel, setExperienceLevel] = useState('');
  const [skills, setSkills] = useState([]);
  const [interestIds, setInterestIds] = useState([]);

  const canProceed = () => {
    switch (step) {
      case 1: return jobPosition.trim().length > 0;
      case 2: return experienceLevel.length > 0;
      case 3: return skills.length >= 1;
      case 4: return true; // optional
      default: return false;
    }
  };

  const handleNext = () => {
    if (step < 4) {
      setStep(step + 1);
      setError('');
    } else {
      handleSubmit();
    }
  };

  const handleBack = () => {
    if (step > 1) {
      setStep(step - 1);
      setError('');
    } else {
      navigate('/profile-setup');
    }
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    setError('');

    try {
      await api.post('/users/profile/create-manual/', {
        current_job_position: jobPosition.trim(),
        experience_level: experienceLevel,
        skills: skills.map((s) => ({
          skill_id: s.skill_id,
          proficiency_level: s.proficiency_level,
          years_of_experience: 0,
        })),
        interest_ids: interestIds,
      });

      navigate(finalRedirect);
    } catch (err) {
      const msg =
        err.response?.data?.error ||
        err.response?.data?.detail ||
        (err.response?.data && typeof err.response.data === 'object'
          ? Object.values(err.response.data).flat().join(' ')
          : null) ||
        'Failed to save profile. Please try again.';
      setError(typeof msg === 'string' ? msg : 'Failed to save profile.');
    } finally {
      setSubmitting(false);
    }
  };

  // Skill handlers
  const handleAddSkill = (skill) => {
    setSkills((prev) => [...prev, skill]);
  };

  const handleRemoveSkill = (skillId) => {
    setSkills((prev) => prev.filter((s) => s.skill_id !== skillId));
  };

  const handleUpdateProficiency = (skillId, proficiency) => {
    setSkills((prev) =>
      prev.map((s) =>
        s.skill_id === skillId ? { ...s, proficiency_level: proficiency } : s
      )
    );
  };

  // Interest handler
  const handleToggleInterest = (interestId) => {
    setInterestIds((prev) =>
      prev.includes(interestId)
        ? prev.filter((id) => id !== interestId)
        : [...prev, interestId]
    );
  };

  const StepIcon = STEP_ICONS[step - 1];
  const progress = (step / STEPS.length) * 100;

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-4 sm:px-6 lg:px-8">
        <div className="max-w-3xl mx-auto py-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gradient-to-br from-primary-600 to-purple-500 rounded-lg flex items-center justify-center">
                <Zap className="w-4 h-4 text-white" />
              </div>
              <span className="text-sm font-semibold text-gray-900">
                Skill<span className="text-primary-600">Bridge</span>
              </span>
            </div>
            <span className="text-sm text-gray-500">
              Step {step} of {STEPS.length}
            </span>
          </div>

          {/* Progress bar */}
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-gradient-to-r from-primary-500 to-purple-500 h-2 rounded-full transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>

          {/* Step indicators */}
          <div className="flex items-center justify-between mt-3">
            {STEPS.map((s) => {
              const Icon = STEP_ICONS[s.id - 1];
              const isActive = s.id === step;
              const isDone = s.id < step;
              return (
                <div key={s.id} className="flex items-center gap-1.5">
                  <div
                    className={`w-6 h-6 rounded-full flex items-center justify-center transition-all ${
                      isDone
                        ? 'bg-primary-600'
                        : isActive
                          ? 'bg-primary-100 border-2 border-primary-500'
                          : 'bg-gray-100'
                    }`}
                  >
                    {isDone ? (
                      <Check className="w-3.5 h-3.5 text-white" />
                    ) : (
                      <Icon className={`w-3 h-3 ${isActive ? 'text-primary-600' : 'text-gray-400'}`} />
                    )}
                  </div>
                  <span
                    className={`text-xs font-medium hidden sm:inline ${
                      isActive ? 'text-primary-600' : isDone ? 'text-gray-600' : 'text-gray-400'
                    }`}
                  >
                    {s.label}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1 flex items-start justify-center px-4 sm:px-6 py-8 sm:py-12">
        <div className="w-full max-w-2xl">
          {/* Error banner */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          {/* Step content */}
          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 sm:p-8">
            {step === 1 && (
              <StepJobPosition value={jobPosition} onChange={setJobPosition} />
            )}
            {step === 2 && (
              <StepExperience value={experienceLevel} onChange={setExperienceLevel} />
            )}
            {step === 3 && (
              <StepSkills
                selected={skills}
                onAdd={handleAddSkill}
                onRemove={handleRemoveSkill}
                onUpdateProficiency={handleUpdateProficiency}
              />
            )}
            {step === 4 && (
              <StepInterests
                selected={interestIds}
                onToggle={handleToggleInterest}
              />
            )}
          </div>

          {/* Navigation */}
          <div className="flex items-center justify-between mt-6">
            <button
              onClick={handleBack}
              className="flex items-center gap-2 px-5 py-3 text-sm font-semibold text-gray-600 bg-white border-2 border-gray-200 rounded-xl hover:border-gray-300 transition-colors cursor-pointer"
            >
              <ArrowLeft className="w-4 h-4" />
              Back
            </button>

            <button
              onClick={handleNext}
              disabled={!canProceed() || submitting}
              className="flex items-center gap-2 px-6 py-3 text-sm font-semibold text-white bg-primary-600 rounded-xl hover:bg-primary-700 disabled:bg-primary-400 transition-colors cursor-pointer border-none"
            >
              {submitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Saving...
                </>
              ) : step < 4 ? (
                <>
                  Next
                  <ArrowRight className="w-4 h-4" />
                </>
              ) : (
                <>
                  <Check className="w-4 h-4" />
                  Save & Continue
                </>
              )}
            </button>
          </div>

          {/* Skip link */}
          <div className="text-center mt-6">
            <button
              onClick={() => navigate(finalRedirect)}
              className="text-sm text-gray-400 hover:text-gray-600 transition-colors bg-transparent border-none cursor-pointer underline"
            >
              Skip for now
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
