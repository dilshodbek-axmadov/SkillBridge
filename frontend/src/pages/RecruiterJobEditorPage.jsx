import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Loader2, Save, Send, Archive } from 'lucide-react';
import useAuthStore from '../store/authStore';
import useRecruiterGate from '../hooks/useRecruiterGate';
import RecruiterLayout from '../components/layout/RecruiterLayout';
import api from '../services/api';

const EXPERIENCE_OPTIONS = [
  { value: '', label: 'Select level' },
  { value: 'no_experience', label: 'No experience' },
  { value: 'junior', label: 'Junior (1–3 years)' },
  { value: 'mid', label: 'Mid (3–6 years)' },
  { value: 'senior', label: 'Senior (6+ years)' },
];

const EMPLOYMENT_OPTIONS = [
  { value: 'full_time', label: 'Full-time' },
  { value: 'part_time', label: 'Part-time' },
  { value: 'project', label: 'Project-based' },
];

const emptyForm = {
  job_title: '',
  company_name: '',
  job_category: '',
  job_description: '',
  experience_required: '',
  employment_type: 'full_time',
  salary_min: '',
  salary_max: '',
  salary_currency: 'UZS',
  location: '',
  is_remote: false,
  job_url: '',
  deadline_date: '',
};

function toInputDateTime(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '';
  const pad = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function fromInputDateTime(val) {
  if (!val) return null;
  const d = new Date(val);
  if (Number.isNaN(d.getTime())) return null;
  return d.toISOString();
}

export default function RecruiterJobEditorPage() {
  useRecruiterGate();
  const user = useAuthStore((s) => s.user);
  const navigate = useNavigate();
  const { jobId } = useParams();
  const isCreate = !jobId;

  const [form, setForm] = useState(emptyForm);
  const [loading, setLoading] = useState(!isCreate);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isCreate) {
      setLoading(false);
      return;
    }
    const run = async () => {
      setLoading(true);
      setError('');
      try {
        const { data } = await api.get(`/recruiters/jobs/${jobId}/`);
        setForm({
          job_title: data.job_title || '',
          company_name: data.company_name || '',
          job_category: data.job_category || '',
          job_description: data.job_description || '',
          experience_required: data.experience_required || '',
          employment_type: data.employment_type || 'full_time',
          salary_min: data.salary_min != null ? String(data.salary_min) : '',
          salary_max: data.salary_max != null ? String(data.salary_max) : '',
          salary_currency: data.salary_currency || 'UZS',
          location: data.location || '',
          is_remote: !!data.is_remote,
          job_url: data.job_url || '',
          deadline_date: toInputDateTime(data.deadline_date),
        });
      } catch {
        setError('Could not load this job.');
      } finally {
        setLoading(false);
      }
    };
    run();
  }, [jobId, isCreate]);

  const update = (key) => (e) => {
    const v = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    setForm((f) => ({ ...f, [key]: v }));
    setError('');
  };

  const buildPayload = (listingStatus) => {
    const payload = {
      job_title: form.job_title.trim(),
      company_name: form.company_name.trim(),
      job_category: form.job_category.trim(),
      job_description: form.job_description,
      experience_required: form.experience_required || '',
      employment_type: form.employment_type,
      salary_currency: form.salary_currency || 'UZS',
      location: form.location.trim(),
      is_remote: form.is_remote,
      job_url: form.job_url.trim(),
      listing_status: listingStatus,
    };
    if (form.salary_min !== '') {
      payload.salary_min = form.salary_min;
    } else {
      payload.salary_min = null;
    }
    if (form.salary_max !== '') {
      payload.salary_max = form.salary_max;
    } else {
      payload.salary_max = null;
    }
    const ddl = fromInputDateTime(form.deadline_date);
    payload.deadline_date = ddl;
    return payload;
  };

  const submit = async (listingStatus) => {
    setSaving(true);
    setError('');
    try {
      const payload = buildPayload(listingStatus);
      if (!payload.job_title) {
        setError('Job title is required.');
        setSaving(false);
        return;
      }
      if (isCreate) {
        const { data } = await api.post('/recruiters/jobs/', payload);
        if (listingStatus === 'active') {
          navigate('/recruiter/jobs');
        } else {
          navigate(`/recruiter/jobs/${data.job_id}/edit`, { replace: true });
        }
      } else {
        await api.patch(`/recruiters/jobs/${jobId}/`, payload);
        navigate('/recruiter/jobs');
      }
    } catch (e) {
      const msg =
        e.response?.data?.detail ||
        (typeof e.response?.data === 'object' && Object.values(e.response.data).flat()?.[0]) ||
        'Save failed.';
      setError(String(msg));
    } finally {
      setSaving(false);
    }
  };

  const archive = async () => {
    if (!jobId || isCreate) return;
    if (!window.confirm('Archive this job? It will no longer appear in public search.')) return;
    setSaving(true);
    setError('');
    try {
      await api.patch(`/recruiters/jobs/${jobId}/`, { listing_status: 'archived' });
      navigate('/recruiter/jobs');
    } catch (e) {
      setError('Could not archive.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <RecruiterLayout user={user}>
        <div className="flex justify-center py-24">
          <Loader2 className="w-8 h-8 text-primary-600 animate-spin" />
        </div>
      </RecruiterLayout>
    );
  }

  return (
    <RecruiterLayout user={user}>
      <Link
        to="/recruiter/jobs"
        className="inline-flex items-center gap-1.5 text-sm text-primary-600 hover:text-primary-700 no-underline mb-6"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to job postings
      </Link>

      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
          {isCreate ? 'Create job posting' : 'Edit job posting'}
        </h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Drafts stay private. Publishing makes the role visible in job search (subject to listing rules).
        </p>
      </div>

      {error && (
        <div className="mb-4 p-3 rounded-lg bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900 text-sm text-red-700 dark:text-red-300">
          {error}
        </div>
      )}

      <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-5 sm:p-6 space-y-5 max-w-3xl">
        <div className="grid sm:grid-cols-2 gap-4">
          <div className="sm:col-span-2">
            <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Job title *</label>
            <input
              value={form.job_title}
              onChange={update('job_title')}
              className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm"
              required
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Company</label>
            <input
              value={form.company_name}
              onChange={update('company_name')}
              className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Category</label>
            <input
              value={form.job_category}
              onChange={update('job_category')}
              className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm"
              placeholder="e.g. Backend"
            />
          </div>
          <div className="sm:col-span-2">
            <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Description</label>
            <textarea
              value={form.job_description}
              onChange={update('job_description')}
              rows={6}
              className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Experience</label>
            <select
              value={form.experience_required}
              onChange={update('experience_required')}
              className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm"
            >
              {EXPERIENCE_OPTIONS.map((o) => (
                <option key={o.value || 'x'} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Employment</label>
            <select
              value={form.employment_type}
              onChange={update('employment_type')}
              className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm"
            >
              {EMPLOYMENT_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Salary min</label>
            <input
              type="number"
              min="0"
              step="0.01"
              value={form.salary_min}
              onChange={update('salary_min')}
              className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Salary max</label>
            <input
              type="number"
              min="0"
              step="0.01"
              value={form.salary_max}
              onChange={update('salary_max')}
              className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Currency</label>
            <input
              value={form.salary_currency}
              onChange={update('salary_currency')}
              className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Location</label>
            <input
              value={form.location}
              onChange={update('location')}
              className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Application / detail URL</label>
            <input
              type="url"
              value={form.job_url}
              onChange={update('job_url')}
              className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm"
              placeholder="https://…"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Deadline</label>
            <input
              type="datetime-local"
              value={form.deadline_date}
              onChange={update('deadline_date')}
              className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm"
            />
          </div>
          <div className="flex items-center gap-2 pt-6">
            <input
              id="remote"
              type="checkbox"
              checked={form.is_remote}
              onChange={update('is_remote')}
              className="rounded border-gray-300"
            />
            <label htmlFor="remote" className="text-sm text-gray-700 dark:text-gray-300">
              Remote-friendly
            </label>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3 pt-4 border-t border-gray-200 dark:border-gray-800">
          <button
            type="button"
            disabled={saving}
            onClick={() => submit('draft')}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-sm font-semibold text-gray-800 dark:text-gray-100 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700/50 cursor-pointer disabled:opacity-50"
          >
            <Save className="w-4 h-4" />
            {isCreate ? 'Save as draft' : 'Update draft'}
          </button>
          <button
            type="button"
            disabled={saving}
            onClick={() => submit('active')}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-primary-600 hover:bg-primary-700 text-white text-sm font-semibold border-none cursor-pointer disabled:opacity-50"
          >
            <Send className="w-4 h-4" />
            {isCreate ? 'Publish job' : 'Save & publish'}
          </button>
          {!isCreate && (
            <button
              type="button"
              disabled={saving}
              onClick={archive}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-transparent text-amber-700 dark:text-amber-400 border border-amber-300 dark:border-amber-800 text-sm font-semibold cursor-pointer disabled:opacity-50 ml-auto"
            >
              <Archive className="w-4 h-4" />
              Archive
            </button>
          )}
        </div>
      </div>
    </RecruiterLayout>
  );
}
