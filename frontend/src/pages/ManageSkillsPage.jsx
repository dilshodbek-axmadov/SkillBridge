import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import {
  Search, Loader2, AlertCircle, Check, ChevronDown, X,
  Trash2, Star, Plus, ArrowLeft, Sparkles,
} from 'lucide-react';
import DashboardLayout from '../components/layout/DashboardLayout';
import useAuthStore from '../store/authStore';
import api from '../services/api';

/* ─── constants ──────────────────────────────── */
const PROFICIENCY_LEVELS = [
  { value: 'beginner',     label: 'Beginner',     color: 'bg-gray-100 text-gray-600 border-gray-200',     active: 'bg-gray-600 text-white border-gray-600' },
  { value: 'intermediate', label: 'Intermediate', color: 'bg-amber-50 text-amber-600 border-amber-200',   active: 'bg-amber-500 text-white border-amber-500' },
  { value: 'advanced',     label: 'Advanced',     color: 'bg-blue-50 text-blue-600 border-blue-200',      active: 'bg-blue-600 text-white border-blue-600' },
  { value: 'expert',       label: 'Expert',       color: 'bg-emerald-50 text-emerald-600 border-emerald-200', active: 'bg-emerald-600 text-white border-emerald-600' },
];

const CATEGORY_LABELS = {
  programming_language: 'Programming',
  library_or_package: 'Libraries',
  framework: 'Frameworks',
  database: 'Databases',
  data_engineering: 'Data Engineering',
  cloud_platform: 'Cloud',
  devops_infrastructure: 'DevOps',
  testing_qa: 'Testing/QA',
  bi_analytics: 'BI & Analytics',
  tools_software: 'Tools',
  design_creative: 'Design',
  business_product_management: 'Business',
  security: 'Security',
  networking: 'Networking',
  operating_system: 'OS',
  methodology_process: 'Methodology',
  soft_skill: 'Soft Skills',
  domain_specific: 'Domain',
  other: 'Other',
};

/* ─── main page ──────────────────────────────── */
export default function ManageSkillsPage() {
  const { user, fetchUser } = useAuthStore();

  // user skills
  const [mySkills, setMySkills] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // add panel
  const [showAddPanel, setShowAddPanel] = useState(false);
  const [allSkills, setAllSkills] = useState([]);
  const [categories, setCategories] = useState([]);
  const [activeCategory, setActiveCategory] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [loadingBrowse, setLoadingBrowse] = useState(true);
  const [searching, setSearching] = useState(false);
  const [adding, setAdding] = useState(null); // skill_id being added
  const searchTimeout = useRef(null);

  // delete confirm
  const [deleteTarget, setDeleteTarget] = useState(null);

  /* ─── load user skills ──────────────────── */
  useEffect(() => {
    const load = async () => {
      try {
        if (!user) await fetchUser();
        const { data } = await api.get('/users/profile/my-skills/');
        setMySkills(data.skills || []);
      } catch (err) {
        if (err.response?.status === 401) {
          window.location.href = '/login?redirect=/manage-skills';
          return;
        }
        setError('Failed to load your skills.');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  /* ─── load browse skills & categories ──── */
  useEffect(() => {
    if (!showAddPanel) return;
    const fetchBrowse = async () => {
      setLoadingBrowse(true);
      try {
        const catsRes = await api.get('/users/skills/categories/');
        setCategories(catsRes.data.categories || []);

        let page = 1;
        let accumulated = [];
        let hasNext = true;
        while (hasNext) {
          const res = await api.get('/users/skills/browse/', {
            params: { page, verified_only: 'false' },
          });
          accumulated = [...accumulated, ...(res.data.skills || [])];
          hasNext = res.data.has_next;
          page++;
        }
        setAllSkills(accumulated);
      } catch {
        // fallback
      } finally {
        setLoadingBrowse(false);
      }
    };
    if (allSkills.length === 0) fetchBrowse();
    else setLoadingBrowse(false);
  }, [showAddPanel]);

  /* ─── search debounce ──────────────────── */
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
    return () => { if (searchTimeout.current) clearTimeout(searchTimeout.current); };
  }, [searchQuery]);

  /* ─── add skill ────────────────────────── */
  const addSkill = async (skill) => {
    setAdding(skill.skill_id);
    try {
      const { data } = await api.post('/users/profile/skills/add/', {
        skill_id: skill.skill_id,
        proficiency_level: 'beginner',
      });
      if (data.skill) {
        setMySkills((prev) => [...prev, data.skill]);
      }
    } catch (err) {
      // might be duplicate
      if (err.response?.status === 400) {
        // skill already exists, ignore
      }
    } finally {
      setAdding(null);
    }
  };

  /* ─── update proficiency ───────────────── */
  const updateProficiency = async (userSkillId, level) => {
    // optimistic update
    setMySkills((prev) =>
      prev.map((s) =>
        s.user_skill_id === userSkillId ? { ...s, proficiency_level: level } : s
      )
    );
    try {
      await api.patch(`/users/profile/skills/update/${userSkillId}/`, {
        proficiency_level: level,
      });
    } catch {
      // revert on error (reload)
      const { data } = await api.get('/users/profile/my-skills/');
      setMySkills(data.skills || []);
    }
  };

  /* ─── toggle primary ───────────────────── */
  const togglePrimary = async (userSkillId, current) => {
    setMySkills((prev) =>
      prev.map((s) =>
        s.user_skill_id === userSkillId ? { ...s, is_primary: !current } : s
      )
    );
    try {
      await api.patch(`/users/profile/skills/update/${userSkillId}/`, {
        is_primary: !current,
      });
    } catch {
      const { data } = await api.get('/users/profile/my-skills/');
      setMySkills(data.skills || []);
    }
  };

  /* ─── delete skill ─────────────────────── */
  const deleteSkill = async (userSkillId) => {
    setDeleteTarget(null);
    setMySkills((prev) => prev.filter((s) => s.user_skill_id !== userSkillId));
    try {
      await api.delete(`/users/profile/skills/delete/${userSkillId}/`);
    } catch {
      const { data } = await api.get('/users/profile/my-skills/');
      setMySkills(data.skills || []);
    }
  };

  /* ─── derived ──────────────────────────── */
  const mySkillIds = new Set(mySkills.map((s) => s.skill?.skill_id || s.skill_id));
  const displaySkills = searchQuery.trim()
    ? searchResults
    : activeCategory
      ? allSkills.filter((s) => s.category === activeCategory)
      : allSkills;

  /* ─── loading / error ──────────────────── */
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-10 h-10 text-primary-600 animate-spin mx-auto mb-4" />
          <p className="text-gray-500 dark:text-gray-400 text-sm">Loading your skills...</p>
        </div>
      </div>
    );
  }
  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-10 h-10 text-red-400 mx-auto mb-3" />
          <p className="text-gray-600">{error}</p>
          <button onClick={() => window.location.reload()} className="mt-4 px-5 py-2 bg-primary-600 text-white rounded-lg text-sm font-semibold border-none cursor-pointer hover:bg-primary-700 transition-colors">
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <DashboardLayout user={user}>
      <div className="space-y-6">
        {/* header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Link to="/dashboard" className="text-gray-400 hover:text-gray-600 transition-colors no-underline">
                <ArrowLeft className="w-5 h-5" />
              </Link>
              <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">My Skills</h1>
            </div>
            <p className="text-sm text-gray-500 ml-7">
              {mySkills.length} skill{mySkills.length !== 1 ? 's' : ''} in your profile
            </p>
          </div>
          <button
            onClick={() => setShowAddPanel(!showAddPanel)}
            className={`inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold border-none cursor-pointer transition-all ${
              showAddPanel
                ? 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                : 'bg-primary-600 text-white hover:bg-primary-700 shadow-sm shadow-primary-600/20'
            }`}
          >
            {showAddPanel ? (
              <><X className="w-4 h-4" /> Close</>
            ) : (
              <><Plus className="w-4 h-4" /> Add Skills</>
            )}
          </button>
        </div>

        {/* add skills panel */}
        {showAddPanel && (
          <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-5 space-y-4">
            <div className="flex items-center gap-2 mb-1">
              <Sparkles className="w-4 h-4 text-primary-500" />
              <h3 className="text-sm font-bold text-gray-900 dark:text-gray-100">Browse & Add Skills</h3>
            </div>

            {/* search */}
            <div className="relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-gray-500" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search skills (e.g. Python, React, Docker...)"
                className="w-full pl-12 pr-10 py-3 border-2 border-gray-200 rounded-xl text-sm focus:outline-none focus:border-primary-500 transition-colors"
              />
              {searching && (
                <Loader2 className="absolute right-4 top-1/2 -translate-y-1/2 w-4 h-4 text-primary-500 animate-spin" />
              )}
              {searchQuery && !searching && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-4 top-1/2 -translate-y-1/2 p-0.5 text-gray-400 hover:text-gray-600 bg-transparent border-none cursor-pointer"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>

            {/* category tabs */}
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

            {/* skills grid */}
            {loadingBrowse ? (
              <div className="flex items-center justify-center py-10">
                <Loader2 className="w-6 h-6 text-primary-500 animate-spin" />
              </div>
            ) : (
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2 max-h-72 overflow-y-auto pr-1">
                {displaySkills.map((skill) => {
                  const isAdded = mySkillIds.has(skill.skill_id);
                  const isAdding = adding === skill.skill_id;
                  return (
                    <button
                      key={skill.skill_id}
                      onClick={() => !isAdded && !isAdding && addSkill(skill)}
                      disabled={isAdded || isAdding}
                      className={`text-left px-3 py-2.5 rounded-lg border text-sm transition-all cursor-pointer ${
                        isAdded
                          ? 'border-primary-300 bg-primary-50 text-primary-600 font-semibold cursor-default opacity-70'
                          : isAdding
                            ? 'border-gray-200 bg-gray-50 text-gray-400 cursor-wait'
                            : 'border-gray-200 bg-white text-gray-700 hover:border-primary-300 hover:bg-primary-50'
                      }`}
                    >
                      <div className="flex items-center justify-between gap-1">
                        <span className="truncate">{skill.name_en}</span>
                        {isAdded && <Check className="w-4 h-4 text-primary-500 flex-shrink-0" />}
                        {isAdding && <Loader2 className="w-3.5 h-3.5 text-primary-500 animate-spin flex-shrink-0" />}
                      </div>
                    </button>
                  );
                })}
                {displaySkills.length === 0 && (
                  <p className="col-span-full text-center text-gray-400 text-sm py-6">
                    {searchQuery.trim() ? 'No skills found.' : 'No skills available.'}
                  </p>
                )}
              </div>
            )}
          </div>
        )}

        {/* my skills list */}
        {mySkills.length === 0 ? (
          <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-100 dark:border-gray-800 p-12 text-center">
            <div className="w-14 h-14 bg-gray-100 dark:bg-gray-800 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <Sparkles className="w-7 h-7 text-gray-300" />
            </div>
            <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100 mb-1">No skills yet</h3>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">Click "Add Skills" above to start building your skill profile.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {mySkills.map((s) => {
              const skillName = s.skill?.name_en || s.skill_name || 'Unknown';
              const category = s.skill?.category || s.category || '';
              const catLabel = CATEGORY_LABELS[category] || category;
              return (
                <div
                  key={s.user_skill_id}
                  className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-4 hover:shadow-md transition-shadow"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center gap-3">
                    {/* skill info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-2">
                        <h3 className="text-base font-bold text-gray-900 dark:text-gray-100">{skillName}</h3>
                        {catLabel && (
                          <span className="px-2 py-0.5 bg-gray-100 text-gray-500 rounded text-[10px] font-semibold uppercase">
                            {catLabel}
                          </span>
                        )}
                        {s.is_primary && (
                          <span className="px-2 py-0.5 bg-amber-100 text-amber-600 rounded text-[10px] font-semibold uppercase flex items-center gap-0.5">
                            <Star className="w-2.5 h-2.5" fill="currentColor" /> Primary
                          </span>
                        )}
                      </div>

                      {/* proficiency buttons */}
                      <div className="flex flex-wrap gap-1.5">
                        {PROFICIENCY_LEVELS.map((lvl) => {
                          const isActive = s.proficiency_level === lvl.value;
                          return (
                            <button
                              key={lvl.value}
                              onClick={() => !isActive && updateProficiency(s.user_skill_id, lvl.value)}
                              className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all cursor-pointer ${
                                isActive ? lvl.active : lvl.color + ' hover:opacity-80'
                              }`}
                            >
                              {lvl.label}
                            </button>
                          );
                        })}
                      </div>
                    </div>

                    {/* actions */}
                    <div className="flex items-center gap-2 flex-shrink-0">
                      <button
                        onClick={() => togglePrimary(s.user_skill_id, s.is_primary)}
                        title={s.is_primary ? 'Remove from primary' : 'Mark as primary'}
                        className={`p-2 rounded-lg border transition-all cursor-pointer ${
                          s.is_primary
                            ? 'bg-amber-50 border-amber-200 text-amber-500 hover:bg-amber-100'
                            : 'bg-white border-gray-200 text-gray-300 hover:text-amber-400 hover:border-amber-200'
                        }`}
                      >
                        <Star className="w-4 h-4" fill={s.is_primary ? 'currentColor' : 'none'} />
                      </button>
                      <button
                        onClick={() => setDeleteTarget(s.user_skill_id)}
                        title="Remove skill"
                        className="p-2 rounded-lg border border-gray-200 bg-white text-gray-300 hover:text-red-500 hover:border-red-200 hover:bg-red-50 transition-all cursor-pointer"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* delete confirmation modal */}
      {deleteTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30" onClick={() => setDeleteTarget(null)}>
          <div className="bg-white rounded-2xl p-6 max-w-sm mx-4 shadow-xl" onClick={(e) => e.stopPropagation()}>
            <div className="w-12 h-12 bg-red-100 rounded-xl flex items-center justify-center mx-auto mb-4">
              <Trash2 className="w-6 h-6 text-red-500" />
            </div>
            <h3 className="text-base font-bold text-gray-900 text-center mb-1">Remove Skill</h3>
            <p className="text-sm text-gray-500 text-center mb-5">
              Are you sure you want to remove this skill from your profile?
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setDeleteTarget(null)}
                className="flex-1 px-4 py-2.5 border border-gray-200 text-gray-600 rounded-xl text-sm font-semibold cursor-pointer hover:bg-gray-50 transition-colors bg-white dark:bg-gray-800"
              >
                Cancel
              </button>
              <button
                onClick={() => deleteSkill(deleteTarget)}
                className="flex-1 px-4 py-2.5 bg-red-600 text-white rounded-xl text-sm font-semibold border-none cursor-pointer hover:bg-red-700 transition-colors"
              >
                Remove
              </button>
            </div>
          </div>
        </div>
      )}
    </DashboardLayout>
  );
}
