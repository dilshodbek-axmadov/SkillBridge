import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import DashboardLayout from '../components/layout/DashboardLayout';
import useAuthStore from '../store/authStore';
import api from '../services/api';
import {
  FileText, Download, Loader2, Plus, Trash2, ChevronDown, ChevronUp,
  Eye, EyeOff, ArrowUp, ArrowDown, Sparkles, CheckCircle2, X,
  User, Briefcase, GraduationCap, Code2, FolderOpen, Award, Languages,
  Trophy, AlignLeft, Mail, Phone, MapPin, Github, Linkedin, Globe,
  Pen, Save, AlertCircle,
} from 'lucide-react';

/* ═══════════════════════════════════════════
   Constants
   ═══════════════════════════════════════════ */

const SECTION_META = {
  personal_info: { label: 'Personal Information', icon: User, required: true },
  summary:       { label: 'Professional Summary', icon: AlignLeft },
  experience:    { label: 'Work Experience', icon: Briefcase },
  education:     { label: 'Education', icon: GraduationCap },
  skills:        { label: 'Skills', icon: Code2 },
  projects:      { label: 'Projects', icon: FolderOpen },
  certifications:{ label: 'Certifications', icon: Award },
  languages:     { label: 'Languages', icon: Languages },
  awards:        { label: 'Awards & Achievements', icon: Trophy },
};

const TEMPLATES = {
  modern:   { name: 'Modern',   desc: 'Clean layout with skills highlighted first' },
  classic:  { name: 'Classic',  desc: 'Traditional format with experience first' },
  creative: { name: 'Creative', desc: 'Portfolio-focused with projects highlighted' },
};

const TEMPLATE_ORDERS = {
  modern:   ['personal_info','summary','skills','experience','projects','education','certifications','languages'],
  classic:  ['personal_info','summary','experience','education','skills','projects','certifications','languages'],
  creative: ['personal_info','summary','projects','skills','experience','education','certifications','awards','languages'],
};

const PROFICIENCY_OPTIONS = ['Native', 'Fluent', 'Professional', 'Intermediate', 'Basic'];

const inputCls = 'w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 text-sm text-gray-900 dark:text-gray-100 bg-white dark:bg-gray-900 focus:outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 transition-all';
const btnPrimary = 'inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-semibold border-none cursor-pointer hover:bg-primary-700 transition-colors disabled:opacity-50';
const btnOutline = 'inline-flex items-center gap-2 px-4 py-2 bg-white dark:bg-gray-900 text-gray-700 dark:text-gray-200 rounded-lg text-sm font-semibold border border-gray-200 dark:border-gray-700 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors disabled:opacity-50';

/* ═══════════════════════════════════════════
   Main Page
   ═══════════════════════════════════════════ */

export default function CVBuilderPage() {
  const { user } = useAuthStore();
  const navigate = useNavigate();

  const [cv, setCv] = useState(null);
  const [sections, setSections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [populating, setPopulating] = useState(false);

  // editor state
  const [activeSection, setActiveSection] = useState(null);
  const [template, setTemplate] = useState('modern');
  const [activeTab, setActiveTab] = useState('edit'); // mobile

  // save state
  const [saving, setSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState(null);
  const saveTimer = useRef(null);

  // download
  const [showDownload, setShowDownload] = useState(false);

  /* ─── load ──────────────────────────── */
  useEffect(() => {
    const load = async () => {
      try {
        const { data } = await api.get('/cv/');
        if (data.cvs && data.cvs.length > 0) {
          const latest = data.cvs[0];
          const detail = await api.get(`/cv/${latest.cv_id}/`);
          setCv(detail.data);
          setSections(detail.data.sections || []);
          setTemplate(detail.data.template_type || 'modern');
          if (detail.data.sections?.length > 0) {
            setActiveSection(detail.data.sections[0].section_type);
          }
        }
      } catch (err) {
        if (err.response?.status === 401) {
          window.location.href = '/login?redirect=/cv-builder';
          return;
        }
        setError('Failed to load CV data.');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  /* ─── auto-save ─────────────────────── */
  const scheduleSave = useCallback(() => {
    if (!cv) return;
    if (saveTimer.current) clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(async () => {
      setSaving(true);
      try {
        const payload = sections.map((s) => ({
          section_type: s.section_type,
          content: s.content,
          display_order: s.display_order,
          is_visible: s.is_visible,
        }));
        await api.put(`/cv/${cv.cv_id}/sections/`, { sections: payload });
        setLastSaved(new Date());
      } catch {
        // silent
      } finally {
        setSaving(false);
      }
    }, 2000);
  }, [cv, sections]);

  const updateSection = useCallback((sectionType, newContent) => {
    setSections((prev) =>
      prev.map((s) =>
        s.section_type === sectionType ? { ...s, content: newContent } : s
      )
    );
    // schedule save after state update
    setTimeout(() => scheduleSave(), 0);
  }, [scheduleSave]);

  const toggleVisibility = useCallback((sectionType) => {
    setSections((prev) =>
      prev.map((s) =>
        s.section_type === sectionType ? { ...s, is_visible: !s.is_visible } : s
      )
    );
    setTimeout(() => scheduleSave(), 0);
  }, [scheduleSave]);

  const moveSection = useCallback((sectionType, direction) => {
    setSections((prev) => {
      const idx = prev.findIndex((s) => s.section_type === sectionType);
      if (idx < 0) return prev;
      const target = direction === 'up' ? idx - 1 : idx + 1;
      if (target < 0 || target >= prev.length) return prev;
      const next = [...prev];
      [next[idx], next[target]] = [next[target], next[idx]];
      return next.map((s, i) => ({ ...s, display_order: i }));
    });
    setTimeout(() => scheduleSave(), 0);
  }, [scheduleSave]);

  /* ─── auto-fill ─────────────────────── */
  const handleAutoFill = async () => {
    setPopulating(true);
    setError('');
    try {
      const { data } = await api.post('/cv/auto-populate/', {
        template_type: template,
      });
      setCv(data);
      setSections(data.sections || []);
      setTemplate(data.template_type || 'modern');
      if (data.sections?.length > 0) {
        setActiveSection(data.sections[0].section_type);
      }
    } catch (err) {
      setError('Failed to auto-fill CV. Please try again.');
    } finally {
      setPopulating(false);
    }
  };

  /* ─── template switch ───────────────── */
  const handleTemplateSwitch = async (newTemplate) => {
    if (!cv || newTemplate === template) return;
    setTemplate(newTemplate);
    try {
      const { data } = await api.put(`/cv/${cv.cv_id}/template/`, {
        template_type: newTemplate,
      });
      setSections(data.sections || []);
    } catch {
      // revert
      setTemplate(template);
    }
  };

  /* ─── download ──────────────────────── */
  const handleDownload = async (format) => {
    if (!cv) return;
    try {
      // Use export_format (not format) — DRF reserves ?format= for content negotiation
      const response = await api.get(`/cv/${cv.cv_id}/export/`, {
        params: { export_format: format },
        responseType: 'blob',
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${cv.title || 'CV'}.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      setShowDownload(false);
    } catch {
      setError('Failed to download CV.');
    }
  };

  /* ─── render ────────────────────────── */
  if (loading) {
    return (
      <DashboardLayout user={user}>
        <div className="flex items-center justify-center py-32">
          <Loader2 className="w-8 h-8 text-primary-600 animate-spin" />
        </div>
      </DashboardLayout>
    );
  }

  // No CV yet — empty state
  if (!cv) {
    return (
      <DashboardLayout user={user}>
        <EmptyState
          onAutoFill={handleAutoFill}
          populating={populating}
          error={error}
          template={template}
          onTemplateChange={setTemplate}
        />
      </DashboardLayout>
    );
  }

  const orderedSections = [...sections].sort((a, b) => a.display_order - b.display_order);

  return (
    <DashboardLayout user={user}>
      <div className="space-y-4">
        {/* Top bar */}
        <TopBar
          cv={cv}
          template={template}
          saving={saving}
          lastSaved={lastSaved}
          onTemplateSwitch={handleTemplateSwitch}
          onDownload={() => setShowDownload(true)}
        />

        {/* Mobile tabs */}
        <div className="flex lg:hidden gap-2 mb-4">
          <button
            onClick={() => setActiveTab('edit')}
            className={`flex-1 py-2 rounded-lg text-sm font-semibold border-none cursor-pointer transition-colors ${
              activeTab === 'edit'
                ? 'bg-primary-600 text-white'
                : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300'
            }`}
          >
            <Pen className="w-4 h-4 inline mr-1.5" />Edit
          </button>
          <button
            onClick={() => setActiveTab('preview')}
            className={`flex-1 py-2 rounded-lg text-sm font-semibold border-none cursor-pointer transition-colors ${
              activeTab === 'preview'
                ? 'bg-primary-600 text-white'
                : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300'
            }`}
          >
            <Eye className="w-4 h-4 inline mr-1.5" />Preview
          </button>
        </div>

        {error && (
          <div className="flex items-center gap-2 p-3 bg-red-50 text-red-600 rounded-lg text-sm">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            {error}
          </div>
        )}

        {/* Split view */}
        <div className="flex gap-6">
          {/* Editor — left */}
          <div className={`w-full lg:w-[45%] space-y-3 ${activeTab === 'preview' ? 'hidden lg:block' : ''}`}>
            {orderedSections.map((s, idx) => (
              <SectionCard
                key={s.section_type}
                section={s}
                isOpen={activeSection === s.section_type}
                onToggle={() =>
                  setActiveSection(
                    activeSection === s.section_type ? null : s.section_type
                  )
                }
                onContentChange={(c) => updateSection(s.section_type, c)}
                onVisibilityToggle={() => toggleVisibility(s.section_type)}
                onMoveUp={() => moveSection(s.section_type, 'up')}
                onMoveDown={() => moveSection(s.section_type, 'down')}
                isFirst={idx === 0}
                isLast={idx === orderedSections.length - 1}
              />
            ))}
          </div>

          {/* Preview — right */}
          <div className={`w-full lg:w-[55%] ${activeTab === 'edit' ? 'hidden lg:block' : ''}`}>
            <div className="sticky top-6">
              <PreviewPanel sections={orderedSections} template={template} />
            </div>
          </div>
        </div>
      </div>

      {/* Download modal */}
      {showDownload && (
        <DownloadModal
          cv={cv}
          onDownload={handleDownload}
          onClose={() => setShowDownload(false)}
        />
      )}
    </DashboardLayout>
  );
}

/* ═══════════════════════════════════════════
   Empty State
   ═══════════════════════════════════════════ */

function EmptyState({ onAutoFill, populating, error, template, onTemplateChange }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 px-4">
      <div className="w-20 h-20 bg-primary-50 rounded-2xl flex items-center justify-center mb-6">
        <FileText className="w-10 h-10 text-primary-500" />
      </div>
      <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">Build Your Professional CV</h1>
      <p className="text-gray-500 dark:text-gray-400 text-center max-w-md mb-8">
        Create an ATS-friendly CV in minutes using your profile data, skills, and projects.
      </p>

      {/* Template picker */}
      <div className="flex gap-3 mb-6">
        {Object.entries(TEMPLATES).map(([key, t]) => (
          <button
            key={key}
            onClick={() => onTemplateChange(key)}
            className={`px-4 py-2 rounded-xl text-sm font-medium border-2 cursor-pointer transition-all ${
              template === key
                ? 'border-primary-500 bg-primary-50 text-primary-700'
                : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-600 dark:text-gray-300 hover:border-gray-300 dark:hover:border-gray-600'
            }`}
          >
            {t.name}
          </button>
        ))}
      </div>

      {error && (
        <div className="flex items-center gap-2 p-3 bg-red-50 text-red-600 rounded-lg text-sm mb-4">
          <AlertCircle className="w-4 h-4" />{error}
        </div>
      )}

      <button onClick={onAutoFill} disabled={populating} className={btnPrimary + ' text-base px-6 py-3'}>
        {populating ? (
          <><Loader2 className="w-5 h-5 animate-spin" />Building your CV...</>
        ) : (
          <><Sparkles className="w-5 h-5" />Auto-Fill from Profile</>
        )}
      </button>
      <p className="text-xs text-gray-400 dark:text-gray-500 mt-3">
        Or <button onClick={() => {}} className="text-primary-600 underline bg-transparent border-none cursor-pointer text-xs">start from scratch</button>
      </p>
    </div>
  );
}

/* ═══════════════════════════════════════════
   Top Bar
   ═══════════════════════════════════════════ */

function TopBar({ cv, template, saving, lastSaved, onTemplateSwitch, onDownload }) {
  return (
    <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 bg-white dark:bg-gray-900 rounded-2xl border border-gray-100 dark:border-gray-800 p-4">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 bg-primary-50 rounded-xl flex items-center justify-center">
          <FileText className="w-5 h-5 text-primary-600" />
        </div>
        <div>
          <h1 className="text-lg font-bold text-gray-900 dark:text-gray-100">{cv.title || 'My CV'}</h1>
          <div className="flex items-center gap-2 text-xs text-gray-400 dark:text-gray-500">
            {saving ? (
              <><Loader2 className="w-3 h-3 animate-spin" />Saving...</>
            ) : lastSaved ? (
              <><CheckCircle2 className="w-3 h-3 text-emerald-500" />Saved {formatTime(lastSaved)}</>
            ) : (
              <span>Auto-save enabled</span>
            )}
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2">
        {/* Template selector */}
        <select
          value={template}
          onChange={(e) => onTemplateSwitch(e.target.value)}
          className="px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 text-sm text-gray-900 dark:text-gray-100 bg-white dark:bg-gray-900 focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 cursor-pointer"
        >
          {Object.entries(TEMPLATES).map(([key, t]) => (
            <option key={key} value={key}>{t.name} Template</option>
          ))}
        </select>

        <button onClick={onDownload} className={btnPrimary}>
          <Download className="w-4 h-4" />Download
        </button>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════
   Section Card
   ═══════════════════════════════════════════ */

function SectionCard({
  section, isOpen, onToggle, onContentChange,
  onVisibilityToggle, onMoveUp, onMoveDown, isFirst, isLast,
}) {
  const meta = SECTION_META[section.section_type] || { label: section.section_type, icon: FileText };
  const Icon = meta.icon;

  return (
    <div className={`bg-white dark:bg-gray-900 rounded-xl border transition-all ${
      isOpen ? 'border-primary-200 dark:border-primary-800 shadow-sm' : 'border-gray-100 dark:border-gray-800'
    }`}>
      {/* Header */}
      <div
        className="flex items-center gap-3 p-3.5 cursor-pointer select-none"
        onClick={onToggle}
      >
        <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
          section.is_visible ? 'bg-primary-50 dark:bg-primary-900/20' : 'bg-gray-100 dark:bg-gray-800'
        }`}>
          <Icon className={`w-4 h-4 ${section.is_visible ? 'text-primary-600' : 'text-gray-400'}`} />
        </div>
        <span className={`flex-1 text-sm font-semibold ${
          section.is_visible ? 'text-gray-900 dark:text-gray-100' : 'text-gray-400 dark:text-gray-500'
        }`}>
          {meta.label}
        </span>

        {/* Controls */}
        <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
          {!meta.required && (
            <button
              onClick={onVisibilityToggle}
              className="p-1.5 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors bg-transparent border-none cursor-pointer"
              title={section.is_visible ? 'Hide section' : 'Show section'}
            >
              {section.is_visible ? (
                <Eye className="w-3.5 h-3.5 text-gray-400 dark:text-gray-500" />
              ) : (
                <EyeOff className="w-3.5 h-3.5 text-gray-300" />
              )}
            </button>
          )}
          {!isFirst && (
            <button onClick={onMoveUp} className="p-1.5 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors bg-transparent border-none cursor-pointer" title="Move up">
              <ArrowUp className="w-3.5 h-3.5 text-gray-400 dark:text-gray-500" />
            </button>
          )}
          {!isLast && (
            <button onClick={onMoveDown} className="p-1.5 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors bg-transparent border-none cursor-pointer" title="Move down">
              <ArrowDown className="w-3.5 h-3.5 text-gray-400 dark:text-gray-500" />
            </button>
          )}
        </div>

        {isOpen ? (
          <ChevronUp className="w-4 h-4 text-gray-400 dark:text-gray-500" />
        ) : (
          <ChevronDown className="w-4 h-4 text-gray-400 dark:text-gray-500" />
        )}
      </div>

      {/* Body */}
      {isOpen && (
        <div className="px-3.5 pb-4 border-t border-gray-50 dark:border-gray-800 pt-3">
          <SectionEditor
            sectionType={section.section_type}
            content={section.content || {}}
            onChange={onContentChange}
          />
        </div>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════
   Section Editor Router
   ═══════════════════════════════════════════ */

function SectionEditor({ sectionType, content, onChange }) {
  switch (sectionType) {
    case 'personal_info': return <PersonalInfoEditor content={content} onChange={onChange} />;
    case 'summary':       return <SummaryEditor content={content} onChange={onChange} />;
    case 'experience':    return <ExperienceEditor content={content} onChange={onChange} />;
    case 'education':     return <EducationEditor content={content} onChange={onChange} />;
    case 'skills':        return <SkillsEditor content={content} onChange={onChange} />;
    case 'projects':      return <ProjectsEditor content={content} onChange={onChange} />;
    case 'certifications':return <CertificationsEditor content={content} onChange={onChange} />;
    case 'languages':     return <LanguagesEditor content={content} onChange={onChange} />;
    case 'awards':        return <AwardsEditor content={content} onChange={onChange} />;
    default:              return <p className="text-sm text-gray-400 dark:text-gray-500">Unknown section type.</p>;
  }
}

/* ═══════════════════════════════════════════
   Personal Info Editor
   ═══════════════════════════════════════════ */

function PersonalInfoEditor({ content, onChange }) {
  const update = (field, value) => onChange({ ...content, [field]: value });

  return (
    <div className="space-y-3">
      <div>
        <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Full Name</label>
        <input className={inputCls} value={content.full_name || ''} onChange={(e) => update('full_name', e.target.value)} placeholder="John Doe" />
      </div>
      <div>
        <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Current Position</label>
        <input className={inputCls} value={content.current_position || ''} onChange={(e) => update('current_position', e.target.value)} placeholder="Frontend Developer" />
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div>
          <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Email</label>
          <input className={inputCls} type="email" value={content.email || ''} onChange={(e) => update('email', e.target.value)} placeholder="email@example.com" />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Phone</label>
          <input className={inputCls} value={content.phone || ''} onChange={(e) => update('phone', e.target.value)} placeholder="+998 90 123 45 67" />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Location</label>
          <input className={inputCls} value={content.location || ''} onChange={(e) => update('location', e.target.value)} placeholder="Tashkent, Uzbekistan" />
        </div>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div>
          <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">LinkedIn</label>
          <input className={inputCls} value={content.linkedin_url || ''} onChange={(e) => update('linkedin_url', e.target.value)} placeholder="linkedin.com/in/..." />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">GitHub</label>
          <input className={inputCls} value={content.github_url || ''} onChange={(e) => update('github_url', e.target.value)} placeholder="github.com/..." />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Portfolio</label>
          <input className={inputCls} value={content.portfolio_url || ''} onChange={(e) => update('portfolio_url', e.target.value)} placeholder="yoursite.com" />
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════
   Summary Editor
   ═══════════════════════════════════════════ */

function SummaryEditor({ content, onChange }) {
  const text = content.text || '';
  const maxLen = 500;

  return (
    <div>
      <textarea
        className={inputCls + ' resize-none h-28'}
        value={text}
        onChange={(e) => onChange({ ...content, text: e.target.value.slice(0, maxLen) })}
        placeholder="A brief professional summary highlighting your key qualifications and career goals..."
        maxLength={maxLen}
      />
      <p className="text-xs text-gray-400 dark:text-gray-500 text-right mt-1">{text.length}/{maxLen}</p>
    </div>
  );
}

/* ═══════════════════════════════════════════
   Experience Editor
   ═══════════════════════════════════════════ */

function ExperienceEditor({ content, onChange }) {
  const positions = content.positions || [];

  const updatePos = (idx, field, value) => {
    const next = [...positions];
    next[idx] = { ...next[idx], [field]: value };
    onChange({ ...content, positions: next });
  };

  const addPos = () => {
    onChange({
      ...content,
      positions: [...positions, { title: '', company: '', location: '', start_date: '', end_date: '', current: false, responsibilities: [], achievements: [] }],
    });
  };

  const removePos = (idx) => {
    onChange({ ...content, positions: positions.filter((_, i) => i !== idx) });
  };

  const updateList = (posIdx, field, text) => {
    const items = text.split('\n').filter(Boolean);
    updatePos(posIdx, field, items);
  };

  return (
    <div className="space-y-4">
      {positions.map((pos, idx) => (
        <div key={idx} className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3 space-y-2.5 relative">
          <button onClick={() => removePos(idx)} className="absolute top-2 right-2 p-1 rounded hover:bg-red-50 bg-transparent border-none cursor-pointer">
            <Trash2 className="w-3.5 h-3.5 text-red-400" />
          </button>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <input className={inputCls} value={pos.title || ''} onChange={(e) => updatePos(idx, 'title', e.target.value)} placeholder="Job Title" />
            <input className={inputCls} value={pos.company || ''} onChange={(e) => updatePos(idx, 'company', e.target.value)} placeholder="Company Name" />
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
            <input className={inputCls} value={pos.start_date || ''} onChange={(e) => updatePos(idx, 'start_date', e.target.value)} placeholder="Start (e.g. Jan 2023)" />
            <input className={inputCls} value={pos.end_date || ''} onChange={(e) => updatePos(idx, 'end_date', e.target.value)} placeholder="End (e.g. Dec 2024)" disabled={pos.current} />
            <label className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
              <input type="checkbox" checked={pos.current || false} onChange={(e) => updatePos(idx, 'current', e.target.checked)} className="rounded" />
              Currently working here
            </label>
          </div>
          <input className={inputCls} value={pos.location || ''} onChange={(e) => updatePos(idx, 'location', e.target.value)} placeholder="Location" />
          <div>
            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Responsibilities (one per line)</label>
            <textarea
              className={inputCls + ' resize-none h-20'}
              value={(pos.responsibilities || []).join('\n')}
              onChange={(e) => updateList(idx, 'responsibilities', e.target.value)}
              placeholder="Developed REST APIs using Django..."
            />
          </div>
        </div>
      ))}
      <button onClick={addPos} className={btnOutline + ' w-full justify-center'}>
        <Plus className="w-4 h-4" />Add Experience
      </button>
    </div>
  );
}

/* ═══════════════════════════════════════════
   Education Editor
   ═══════════════════════════════════════════ */

function EducationEditor({ content, onChange }) {
  const degrees = content.degrees || [];

  const updateDeg = (idx, field, value) => {
    const next = [...degrees];
    next[idx] = { ...next[idx], [field]: value };
    onChange({ ...content, degrees: next });
  };

  const addDeg = () => {
    onChange({
      ...content,
      degrees: [...degrees, { degree: '', field: '', institution: '', start_date: '', end_date: '', gpa: '' }],
    });
  };

  const removeDeg = (idx) => {
    onChange({ ...content, degrees: degrees.filter((_, i) => i !== idx) });
  };

  return (
    <div className="space-y-4">
      {degrees.map((deg, idx) => (
        <div key={idx} className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3 space-y-2.5 relative">
          <button onClick={() => removeDeg(idx)} className="absolute top-2 right-2 p-1 rounded hover:bg-red-50 bg-transparent border-none cursor-pointer">
            <Trash2 className="w-3.5 h-3.5 text-red-400" />
          </button>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <input className={inputCls} value={deg.degree || ''} onChange={(e) => updateDeg(idx, 'degree', e.target.value)} placeholder="Degree (e.g. Bachelor's)" />
            <input className={inputCls} value={deg.field || ''} onChange={(e) => updateDeg(idx, 'field', e.target.value)} placeholder="Field of Study" />
          </div>
          <input className={inputCls} value={deg.institution || ''} onChange={(e) => updateDeg(idx, 'institution', e.target.value)} placeholder="Institution Name" />
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
            <input className={inputCls} value={deg.start_date || ''} onChange={(e) => updateDeg(idx, 'start_date', e.target.value)} placeholder="Start Year" />
            <input className={inputCls} value={deg.end_date || ''} onChange={(e) => updateDeg(idx, 'end_date', e.target.value)} placeholder="End Year" />
            <input className={inputCls} value={deg.gpa || ''} onChange={(e) => updateDeg(idx, 'gpa', e.target.value)} placeholder="GPA (optional)" />
          </div>
        </div>
      ))}
      <button onClick={addDeg} className={btnOutline + ' w-full justify-center'}>
        <Plus className="w-4 h-4" />Add Education
      </button>
    </div>
  );
}

/* ═══════════════════════════════════════════
   Skills Editor
   ═══════════════════════════════════════════ */

function SkillsEditor({ content, onChange }) {
  const categories = content.categories || [];

  const updateCat = (idx, field, value) => {
    const next = [...categories];
    next[idx] = { ...next[idx], [field]: value };
    onChange({ ...content, categories: next });
  };

  const addCat = () => {
    onChange({ ...content, categories: [...categories, { name: '', skills: [] }] });
  };

  const removeCat = (idx) => {
    onChange({ ...content, categories: categories.filter((_, i) => i !== idx) });
  };

  return (
    <div className="space-y-3">
      {categories.map((cat, idx) => (
        <div key={idx} className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3 space-y-2 relative">
          <button onClick={() => removeCat(idx)} className="absolute top-2 right-2 p-1 rounded hover:bg-red-50 bg-transparent border-none cursor-pointer">
            <Trash2 className="w-3.5 h-3.5 text-red-400" />
          </button>
          <input
            className={inputCls}
            value={cat.name || ''}
            onChange={(e) => updateCat(idx, 'name', e.target.value)}
            placeholder="Category (e.g. Programming Languages)"
          />
          <input
            className={inputCls}
            value={(cat.skills || []).join(', ')}
            onChange={(e) => updateCat(idx, 'skills', e.target.value.split(',').map((s) => s.trim()).filter(Boolean))}
            placeholder="Skills separated by commas (e.g. Python, JavaScript, Go)"
          />
        </div>
      ))}
      <button onClick={addCat} className={btnOutline + ' w-full justify-center'}>
        <Plus className="w-4 h-4" />Add Category
      </button>
    </div>
  );
}

/* ═══════════════════════════════════════════
   Projects Editor
   ═══════════════════════════════════════════ */

function ProjectsEditor({ content, onChange }) {
  const projects = content.projects || [];

  const updateProj = (idx, field, value) => {
    const next = [...projects];
    next[idx] = { ...next[idx], [field]: value };
    onChange({ ...content, projects: next });
  };

  const addProj = () => {
    onChange({
      ...content,
      projects: [...projects, { name: '', description: '', technologies: [], github_url: '', live_url: '', highlights: [] }],
    });
  };

  const removeProj = (idx) => {
    onChange({ ...content, projects: projects.filter((_, i) => i !== idx) });
  };

  return (
    <div className="space-y-4">
      {projects.map((proj, idx) => (
        <div key={idx} className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3 space-y-2.5 relative">
          <button onClick={() => removeProj(idx)} className="absolute top-2 right-2 p-1 rounded hover:bg-red-50 bg-transparent border-none cursor-pointer">
            <Trash2 className="w-3.5 h-3.5 text-red-400" />
          </button>
          <input className={inputCls} value={proj.name || ''} onChange={(e) => updateProj(idx, 'name', e.target.value)} placeholder="Project Name" />
          <textarea
            className={inputCls + ' resize-none h-16'}
            value={proj.description || ''}
            onChange={(e) => updateProj(idx, 'description', e.target.value)}
            placeholder="Brief description..."
          />
          <input
            className={inputCls}
            value={(proj.technologies || []).join(', ')}
            onChange={(e) => updateProj(idx, 'technologies', e.target.value.split(',').map((s) => s.trim()).filter(Boolean))}
            placeholder="Technologies (comma-separated)"
          />
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <input className={inputCls} value={proj.github_url || ''} onChange={(e) => updateProj(idx, 'github_url', e.target.value)} placeholder="GitHub URL" />
            <input className={inputCls} value={proj.live_url || ''} onChange={(e) => updateProj(idx, 'live_url', e.target.value)} placeholder="Live Demo URL" />
          </div>
        </div>
      ))}
      <button onClick={addProj} className={btnOutline + ' w-full justify-center'}>
        <Plus className="w-4 h-4" />Add Project
      </button>
    </div>
  );
}

/* ═══════════════════════════════════════════
   Certifications Editor
   ═══════════════════════════════════════════ */

function CertificationsEditor({ content, onChange }) {
  const certs = content.certifications || [];

  const updateCert = (idx, field, value) => {
    const next = [...certs];
    next[idx] = { ...next[idx], [field]: value };
    onChange({ ...content, certifications: next });
  };

  const addCert = () => {
    onChange({
      ...content,
      certifications: [...certs, { name: '', issuer: '', date: '', credential_id: '', url: '' }],
    });
  };

  const removeCert = (idx) => {
    onChange({ ...content, certifications: certs.filter((_, i) => i !== idx) });
  };

  return (
    <div className="space-y-4">
      {certs.map((cert, idx) => (
        <div key={idx} className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3 space-y-2.5 relative">
          <button onClick={() => removeCert(idx)} className="absolute top-2 right-2 p-1 rounded hover:bg-red-50 bg-transparent border-none cursor-pointer">
            <Trash2 className="w-3.5 h-3.5 text-red-400" />
          </button>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <input className={inputCls} value={cert.name || ''} onChange={(e) => updateCert(idx, 'name', e.target.value)} placeholder="Certificate Name" />
            <input className={inputCls} value={cert.issuer || ''} onChange={(e) => updateCert(idx, 'issuer', e.target.value)} placeholder="Issuing Organization" />
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
            <input className={inputCls} value={cert.date || ''} onChange={(e) => updateCert(idx, 'date', e.target.value)} placeholder="Date Issued" />
            <input className={inputCls} value={cert.credential_id || ''} onChange={(e) => updateCert(idx, 'credential_id', e.target.value)} placeholder="Credential ID" />
            <input className={inputCls} value={cert.url || ''} onChange={(e) => updateCert(idx, 'url', e.target.value)} placeholder="Verification URL" />
          </div>
        </div>
      ))}
      <button onClick={addCert} className={btnOutline + ' w-full justify-center'}>
        <Plus className="w-4 h-4" />Add Certification
      </button>
    </div>
  );
}

/* ═══════════════════════════════════════════
   Languages Editor
   ═══════════════════════════════════════════ */

function LanguagesEditor({ content, onChange }) {
  const languages = content.languages || [];

  const updateLang = (idx, field, value) => {
    const next = [...languages];
    next[idx] = { ...next[idx], [field]: value };
    onChange({ ...content, languages: next });
  };

  const addLang = () => {
    onChange({ ...content, languages: [...languages, { language: '', proficiency: 'Intermediate' }] });
  };

  const removeLang = (idx) => {
    onChange({ ...content, languages: languages.filter((_, i) => i !== idx) });
  };

  return (
    <div className="space-y-3">
      {languages.map((lang, idx) => (
        <div key={idx} className="flex items-center gap-2">
          <input className={inputCls + ' flex-1'} value={lang.language || ''} onChange={(e) => updateLang(idx, 'language', e.target.value)} placeholder="Language" />
          <select className={inputCls + ' w-40'} value={lang.proficiency || 'Intermediate'} onChange={(e) => updateLang(idx, 'proficiency', e.target.value)}>
            {PROFICIENCY_OPTIONS.map((p) => <option key={p} value={p}>{p}</option>)}
          </select>
          <button onClick={() => removeLang(idx)} className="p-1.5 rounded hover:bg-red-50 bg-transparent border-none cursor-pointer">
            <Trash2 className="w-3.5 h-3.5 text-red-400" />
          </button>
        </div>
      ))}
      <button onClick={addLang} className={btnOutline + ' w-full justify-center'}>
        <Plus className="w-4 h-4" />Add Language
      </button>
    </div>
  );
}

/* ═══════════════════════════════════════════
   Awards Editor
   ═══════════════════════════════════════════ */

function AwardsEditor({ content, onChange }) {
  const awards = content.awards || [];

  const updateAward = (idx, field, value) => {
    const next = [...awards];
    next[idx] = { ...next[idx], [field]: value };
    onChange({ ...content, awards: next });
  };

  const addAward = () => {
    onChange({ ...content, awards: [...awards, { title: '', issuer: '', date: '', description: '' }] });
  };

  const removeAward = (idx) => {
    onChange({ ...content, awards: awards.filter((_, i) => i !== idx) });
  };

  return (
    <div className="space-y-4">
      {awards.map((aw, idx) => (
        <div key={idx} className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3 space-y-2.5 relative">
          <button onClick={() => removeAward(idx)} className="absolute top-2 right-2 p-1 rounded hover:bg-red-50 bg-transparent border-none cursor-pointer">
            <Trash2 className="w-3.5 h-3.5 text-red-400" />
          </button>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <input className={inputCls} value={aw.title || ''} onChange={(e) => updateAward(idx, 'title', e.target.value)} placeholder="Award Title" />
            <input className={inputCls} value={aw.issuer || ''} onChange={(e) => updateAward(idx, 'issuer', e.target.value)} placeholder="Issuing Organization" />
          </div>
          <input className={inputCls} value={aw.date || ''} onChange={(e) => updateAward(idx, 'date', e.target.value)} placeholder="Date" />
          <textarea className={inputCls + ' resize-none h-14'} value={aw.description || ''} onChange={(e) => updateAward(idx, 'description', e.target.value)} placeholder="Description (optional)" />
        </div>
      ))}
      <button onClick={addAward} className={btnOutline + ' w-full justify-center'}>
        <Plus className="w-4 h-4" />Add Award
      </button>
    </div>
  );
}

/* ═══════════════════════════════════════════
   Preview Panel
   ═══════════════════════════════════════════ */

function PreviewPanel({ sections, template }) {
  const visible = sections.filter((s) => s.is_visible !== false);

  return (
    <div className="bg-gray-100 dark:bg-gray-800 rounded-2xl p-4">
      <div
        className="bg-white shadow-lg mx-auto border border-gray-200 dark:border-gray-700"
        style={{
          width: '100%',
          maxWidth: 595, // A4-ish
          minHeight: 842,
          padding: '40px 36px',
          fontFamily: "'Inter', 'Segoe UI', system-ui, sans-serif",
          fontSize: 11,
          lineHeight: 1.5,
          color: '#1a1a2e',
        }}
      >
        {visible.length === 0 ? (
          <div className="flex items-center justify-center h-64 text-gray-300 text-sm">
            Your CV preview will appear here
          </div>
        ) : (
          visible.map((s) => (
            <PreviewSection key={s.section_type} section={s} />
          ))
        )}
      </div>
    </div>
  );
}

function PreviewSection({ section }) {
  const { section_type, content } = section;
  if (!content) return null;

  switch (section_type) {
    case 'personal_info': return <PreviewPersonalInfo content={content} />;
    case 'summary':       return <PreviewSummary content={content} />;
    case 'experience':    return <PreviewExperience content={content} />;
    case 'education':     return <PreviewEducation content={content} />;
    case 'skills':        return <PreviewSkills content={content} />;
    case 'projects':      return <PreviewProjects content={content} />;
    case 'certifications':return <PreviewCertifications content={content} />;
    case 'languages':     return <PreviewLanguages content={content} />;
    case 'awards':        return <PreviewAwards content={content} />;
    default:              return null;
  }
}

/* ─── Preview sub-components ──────────── */

const pvHeading = { fontSize: 13, fontWeight: 700, color: '#1a1a2e', marginBottom: 4, marginTop: 14, textTransform: 'uppercase', letterSpacing: 0.5 };
const pvDivider = { borderTop: '1px solid #e5e7eb', marginBottom: 8 };
const pvSmall = { fontSize: 9, color: '#666' };

function PreviewPersonalInfo({ content }) {
  const contactParts = [content.email, content.phone, content.location].filter(Boolean);
  const links = [content.linkedin_url, content.github_url, content.portfolio_url].filter(Boolean);

  return (
    <div style={{ textAlign: 'center', marginBottom: 10 }}>
      {content.full_name && (
        <div style={{ fontSize: 22, fontWeight: 700, color: '#1a1a2e', marginBottom: 2 }}>
          {content.full_name}
        </div>
      )}
      {content.current_position && (
        <div style={{ fontSize: 12, color: '#4b5563', marginBottom: 4 }}>
          {content.current_position}
        </div>
      )}
      {contactParts.length > 0 && (
        <div style={pvSmall}>{contactParts.join('  |  ')}</div>
      )}
      {links.length > 0 && (
        <div style={{ ...pvSmall, marginTop: 2 }}>{links.join('  |  ')}</div>
      )}
      <div style={{ ...pvDivider, marginTop: 10 }} />
    </div>
  );
}

function PreviewSummary({ content }) {
  if (!content.text) return null;
  return (
    <div style={{ marginBottom: 8 }}>
      <div style={pvHeading}>Professional Summary</div>
      <div style={pvDivider} />
      <div style={{ fontSize: 10 }}>{content.text}</div>
    </div>
  );
}

function PreviewExperience({ content }) {
  const positions = content.positions || [];
  if (positions.length === 0) return null;
  return (
    <div style={{ marginBottom: 8 }}>
      <div style={pvHeading}>Work Experience</div>
      <div style={pvDivider} />
      {positions.map((pos, i) => (
        <div key={i} style={{ marginBottom: 8 }}>
          <div style={{ fontWeight: 600, fontSize: 11 }}>
            {pos.title}{pos.company ? ` — ${pos.company}` : ''}
          </div>
          <div style={pvSmall}>
            {[pos.location, pos.start_date && `${pos.start_date} - ${pos.current ? 'Present' : pos.end_date || ''}`].filter(Boolean).join('  |  ')}
          </div>
          {(pos.responsibilities || []).map((r, j) => (
            <div key={j} style={{ fontSize: 10, paddingLeft: 10 }}>&#8226; {r}</div>
          ))}
        </div>
      ))}
    </div>
  );
}

function PreviewEducation({ content }) {
  const degrees = content.degrees || [];
  if (degrees.length === 0) return null;
  return (
    <div style={{ marginBottom: 8 }}>
      <div style={pvHeading}>Education</div>
      <div style={pvDivider} />
      {degrees.map((deg, i) => (
        <div key={i} style={{ marginBottom: 6 }}>
          <div style={{ fontWeight: 600, fontSize: 11 }}>
            {deg.degree}{deg.field ? ` in ${deg.field}` : ''}
          </div>
          <div style={pvSmall}>
            {[deg.institution, deg.start_date && `${deg.start_date} - ${deg.end_date || ''}`].filter(Boolean).join('  |  ')}
            {deg.gpa ? `  |  GPA: ${deg.gpa}` : ''}
          </div>
        </div>
      ))}
    </div>
  );
}

function PreviewSkills({ content }) {
  const categories = content.categories || [];
  if (categories.length === 0) return null;
  return (
    <div style={{ marginBottom: 8 }}>
      <div style={pvHeading}>Skills</div>
      <div style={pvDivider} />
      {categories.map((cat, i) => (
        <div key={i} style={{ fontSize: 10, marginBottom: 3 }}>
          <span style={{ fontWeight: 600 }}>{cat.name}: </span>
          {(cat.skills || []).join(', ')}
        </div>
      ))}
    </div>
  );
}

function PreviewProjects({ content }) {
  const projects = content.projects || [];
  if (projects.length === 0) return null;
  return (
    <div style={{ marginBottom: 8 }}>
      <div style={pvHeading}>Projects</div>
      <div style={pvDivider} />
      {projects.map((proj, i) => (
        <div key={i} style={{ marginBottom: 8 }}>
          <div style={{ fontWeight: 600, fontSize: 11 }}>{proj.name}</div>
          {proj.description && <div style={{ fontSize: 10 }}>{proj.description}</div>}
          {(proj.technologies || []).length > 0 && (
            <div style={{ ...pvSmall, fontStyle: 'italic' }}>
              Technologies: {proj.technologies.join(', ')}
            </div>
          )}
          {(proj.github_url || proj.live_url) && (
            <div style={pvSmall}>
              {[proj.github_url, proj.live_url].filter(Boolean).join('  |  ')}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function PreviewCertifications({ content }) {
  const certs = content.certifications || [];
  if (certs.length === 0) return null;
  return (
    <div style={{ marginBottom: 8 }}>
      <div style={pvHeading}>Certifications</div>
      <div style={pvDivider} />
      {certs.map((cert, i) => (
        <div key={i} style={{ fontSize: 10, marginBottom: 3 }}>
          <span style={{ fontWeight: 600 }}>{cert.name}</span>
          {cert.issuer ? ` — ${cert.issuer}` : ''}
          {cert.date ? ` (${cert.date})` : ''}
        </div>
      ))}
    </div>
  );
}

function PreviewLanguages({ content }) {
  const languages = content.languages || [];
  if (languages.length === 0) return null;
  return (
    <div style={{ marginBottom: 8 }}>
      <div style={pvHeading}>Languages</div>
      <div style={pvDivider} />
      {languages.map((lang, i) => (
        <div key={i} style={{ fontSize: 10, marginBottom: 2 }}>
          <span style={{ fontWeight: 600 }}>{lang.language}</span> — {lang.proficiency}
        </div>
      ))}
    </div>
  );
}

function PreviewAwards({ content }) {
  const awards = content.awards || [];
  if (awards.length === 0) return null;
  return (
    <div style={{ marginBottom: 8 }}>
      <div style={pvHeading}>Awards & Achievements</div>
      <div style={pvDivider} />
      {awards.map((aw, i) => (
        <div key={i} style={{ fontSize: 10, marginBottom: 3 }}>
          <span style={{ fontWeight: 600 }}>{aw.title}</span>
          {aw.issuer ? ` — ${aw.issuer}` : ''}
          {aw.date ? ` (${aw.date})` : ''}
          {aw.description && <div style={pvSmall}>{aw.description}</div>}
        </div>
      ))}
    </div>
  );
}

/* ═══════════════════════════════════════════
   Download Modal
   ═══════════════════════════════════════════ */

function DownloadModal({ cv, onDownload, onClose }) {
  const [format, setFormat] = useState('pdf');
  const [downloading, setDownloading] = useState(false);

  const handleDownload = async () => {
    setDownloading(true);
    await onDownload(format);
    setDownloading(false);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className="relative bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 shadow-xl max-w-md w-full mx-4 p-6">
        <button onClick={onClose} className="absolute top-4 right-4 p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 bg-transparent border-none cursor-pointer">
          <X className="w-5 h-5 text-gray-400 dark:text-gray-500" />
        </button>

        <div className="w-12 h-12 bg-primary-50 rounded-xl flex items-center justify-center mx-auto mb-4">
          <Download className="w-6 h-6 text-primary-600" />
        </div>
        <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 text-center mb-1">Download CV</h3>
        <p className="text-sm text-gray-500 dark:text-gray-400 text-center mb-6">{cv.title}</p>

        <div className="space-y-3 mb-6">
          <label className={`flex items-center gap-3 p-3 rounded-xl border-2 cursor-pointer transition-all ${
            format === 'pdf' ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20' : 'border-gray-200 dark:border-gray-700'
          }`}>
            <input type="radio" name="format" value="pdf" checked={format === 'pdf'} onChange={() => setFormat('pdf')} className="sr-only" />
            <div className="w-10 h-10 bg-red-50 rounded-lg flex items-center justify-center">
              <span className="text-xs font-bold text-red-600">PDF</span>
            </div>
            <div>
              <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">PDF Format</div>
              <div className="text-xs text-gray-500 dark:text-gray-400">Best for sharing and printing</div>
            </div>
          </label>

          <label className={`flex items-center gap-3 p-3 rounded-xl border-2 cursor-pointer transition-all ${
            format === 'docx' ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20' : 'border-gray-200 dark:border-gray-700'
          }`}>
            <input type="radio" name="format" value="docx" checked={format === 'docx'} onChange={() => setFormat('docx')} className="sr-only" />
            <div className="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center">
              <span className="text-xs font-bold text-blue-600">DOCX</span>
            </div>
            <div>
              <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">Word Document</div>
              <div className="text-xs text-gray-500 dark:text-gray-400">Editable in Microsoft Word</div>
            </div>
          </label>
        </div>

        <div className="flex gap-3">
          <button onClick={onClose} className={btnOutline + ' flex-1 justify-center'}>Cancel</button>
          <button onClick={handleDownload} disabled={downloading} className={btnPrimary + ' flex-1 justify-center'}>
            {downloading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
            {downloading ? 'Downloading...' : 'Download'}
          </button>
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════
   Helpers
   ═══════════════════════════════════════════ */

function formatTime(date) {
  if (!date) return '';
  const d = new Date(date);
  const now = new Date();
  const diff = Math.floor((now - d) / 1000);
  if (diff < 10) return 'just now';
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}
