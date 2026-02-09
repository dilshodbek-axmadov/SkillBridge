import { useState, useEffect, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  User, Shield, Globe,
  Camera, Check, Eye, EyeOff,
  AlertTriangle, Monitor, Moon, Sun, Settings,
} from 'lucide-react';
import DashboardLayout from '../components/layout/DashboardLayout';
import useAuthStore from '../store/authStore';
import api from '../services/api';

/* ── Constants ─────────────────────────────────────────────────── */

const TABS = [
  { key: 'profile',     label: 'Profile',     icon: User,   desc: 'Personal & career details' },
  { key: 'security',    label: 'Security',     icon: Shield, desc: 'Password & account' },
  { key: 'preferences', label: 'Preferences',  icon: Globe,  desc: 'Theme & language' },
];

const UZ_CITIES = [
  'Tashkent', 'Samarkand', 'Bukhara', 'Namangan', 'Andijan',
  'Fergana', 'Nukus', 'Karshi', 'Kokand', 'Margilan',
  'Jizzakh', 'Urgench', 'Navoi', 'Termez', 'Gulistan',
];

const EXP_LEVELS = [
  { value: 'beginner', label: 'Beginner' },
  { value: 'junior',   label: 'Junior' },
  { value: 'mid',      label: 'Mid-level' },
  { value: 'senior',   label: 'Senior' },
  { value: 'lead',     label: 'Lead / Principal' },
];

/* ── Shared UI Primitives ──────────────────────────────────────── */

function Card({ children, className = '', danger = false }) {
  return (
    <div className={`bg-white rounded-2xl shadow-sm border border-gray-100 p-6 ${danger ? 'border-l-4 !border-l-red-400' : ''} ${className}`}>
      {children}
    </div>
  );
}

function SectionTitle({ children, sub }) {
  return (
    <div className="mb-5">
      <h3 className="text-[17px] font-bold text-gray-800">{children}</h3>
      {sub && <p className="text-xs text-gray-400 mt-0.5">{sub}</p>}
    </div>
  );
}

function Label({ children, htmlFor }) {
  return <label htmlFor={htmlFor} className="block text-sm font-medium text-gray-500 mb-1.5">{children}</label>;
}

function Input({ id, type = 'text', value, onChange, placeholder, disabled, maxLength, className = '' }) {
  return (
    <input
      id={id}
      type={type}
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      disabled={disabled}
      maxLength={maxLength}
      className={`w-full h-11 px-3.5 rounded-xl border border-gray-200 text-sm text-gray-900 outline-none transition-all
        focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 focus:shadow-sm
        disabled:bg-gray-50 disabled:text-gray-400 ${className}`}
    />
  );
}

function Toggle({ checked, onChange, label }) {
  return (
    <div className="flex items-center justify-between py-2">
      <span className="text-sm text-gray-700">{label}</span>
      <button
        type="button"
        onClick={() => onChange(!checked)}
        className={`relative w-11 h-6 rounded-full transition-colors border-none cursor-pointer ${
          checked ? 'bg-primary-600' : 'bg-gray-300'
        }`}
      >
        <span className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow-sm transition-transform ${
          checked ? 'translate-x-5' : 'translate-x-0'
        }`} />
      </button>
    </div>
  );
}

function SaveBtn({ onClick, saving, saved }) {
  return (
    <div className="flex justify-end mt-6">
      <button
        onClick={onClick}
        disabled={saving}
        className="h-11 px-7 bg-primary-600 text-white rounded-xl text-sm font-semibold border-none cursor-pointer
          hover:bg-primary-700 hover:shadow-md disabled:opacity-60 transition-all flex items-center gap-2"
      >
        {saving ? 'Saving...' : saved ? <><Check className="w-4 h-4" /> Saved</> : 'Save Changes'}
      </button>
    </div>
  );
}

/* ── Tab 1: Profile Information ────────────────────────────────── */

function ProfileTab({ user, profile, onUserUpdate }) {
  const [firstName, setFirstName] = useState(user?.first_name || '');
  const [lastName, setLastName] = useState(user?.last_name || '');
  const [phone, setPhone] = useState(user?.phone || '');
  const [location, setLocation] = useState(profile?.location || '');
  const [bio, setBio] = useState(profile?.bio || '');
  const [jobPosition, setJobPosition] = useState(profile?.current_job_position || '');
  const [expLevel, setExpLevel] = useState(profile?.experience_level || 'beginner');
  const [desiredRole, setDesiredRole] = useState(profile?.desired_role || '');
  const [employed, setEmployed] = useState(!!profile?.current_job_position);
  const [saving1, setSaving1] = useState(false);
  const [saved1, setSaved1] = useState(false);
  const [saving2, setSaving2] = useState(false);
  const [saved2, setSaved2] = useState(false);

  const initial = (user?.first_name?.[0] || user?.email?.[0] || 'U').toUpperCase();

  const savePersonal = async () => {
    setSaving1(true);
    try {
      await api.patch('/users/auth/update/', { first_name: firstName, last_name: lastName, phone });
      await api.patch('/users/profile/', { location, bio });
      onUserUpdate();
      setSaved1(true);
      setTimeout(() => setSaved1(false), 2000);
    } catch { /* ignore */ }
    setSaving1(false);
  };

  const saveCareer = async () => {
    setSaving2(true);
    try {
      await api.patch('/users/profile/', {
        current_job_position: jobPosition,
        experience_level: expLevel,
        desired_role: desiredRole,
      });
      onUserUpdate();
      setSaved2(true);
      setTimeout(() => setSaved2(false), 2000);
    } catch { /* ignore */ }
    setSaving2(false);
  };

  return (
    <div className="space-y-6">
      <Card>
        <SectionTitle sub="Manage your personal information">Personal Details</SectionTitle>

        {/* Avatar */}
        <div className="flex items-center gap-5 mb-7 p-4 bg-gradient-to-r from-primary-50 to-purple-50 rounded-2xl">
          <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-primary-500 to-purple-500 flex items-center justify-center text-white text-2xl font-bold relative group cursor-pointer shadow-lg shadow-primary-500/20">
            {initial}
            <div className="absolute inset-0 bg-black/40 rounded-2xl flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
              <Camera className="w-5 h-5 text-white" />
            </div>
          </div>
          <div>
            <p className="text-base font-semibold text-gray-800">{user?.full_name || user?.email}</p>
            <p className="text-xs text-gray-400 mt-0.5">Click avatar to change photo</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <Label htmlFor="first_name">First Name</Label>
            <Input id="first_name" value={firstName} onChange={(e) => setFirstName(e.target.value)} placeholder="First name" />
          </div>
          <div>
            <Label htmlFor="last_name">Last Name</Label>
            <Input id="last_name" value={lastName} onChange={(e) => setLastName(e.target.value)} placeholder="Last name" />
          </div>
          <div>
            <Label htmlFor="email">Email</Label>
            <div className="relative">
              <Input id="email" value={user?.email || ''} disabled />
              <span className="absolute right-3 top-1/2 -translate-y-1/2 text-[11px] bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full font-semibold flex items-center gap-1">
                <Check className="w-3 h-3" /> Verified
              </span>
            </div>
          </div>
          <div>
            <Label htmlFor="phone">Phone Number</Label>
            <Input id="phone" value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="+998 ..." />
          </div>
          <div>
            <Label htmlFor="location">Location</Label>
            <select
              id="location"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              className="w-full h-11 px-3.5 rounded-xl border border-gray-200 text-sm text-gray-900 outline-none bg-white
                focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 transition-all"
            >
              <option value="">Select city</option>
              {UZ_CITIES.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <div className="md:col-span-2">
            <Label htmlFor="bio">Bio</Label>
            <textarea
              id="bio"
              value={bio}
              onChange={(e) => setBio(e.target.value.slice(0, 200))}
              maxLength={200}
              rows={3}
              placeholder="Tell us about yourself..."
              className="w-full px-3.5 py-2.5 rounded-xl border border-gray-200 text-sm text-gray-900 outline-none resize-none
                focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 transition-all"
            />
            <p className="text-xs text-gray-400 text-right mt-1">{bio.length}/200</p>
          </div>
        </div>
        <SaveBtn onClick={savePersonal} saving={saving1} saved={saved1} />
      </Card>

      <Card>
        <SectionTitle sub="Your current position and career goals">Career Information</SectionTitle>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <Label htmlFor="job_position">Current Job Position</Label>
            <Input id="job_position" value={jobPosition} onChange={(e) => setJobPosition(e.target.value)} placeholder="e.g. Backend Developer" />
          </div>
          <div>
            <Label htmlFor="desired_role">Desired Role</Label>
            <Input id="desired_role" value={desiredRole} onChange={(e) => setDesiredRole(e.target.value)} placeholder="e.g. Full-Stack Engineer" />
          </div>
          <div className="md:col-span-2">
            <Label>Experience Level</Label>
            <div className="flex flex-wrap gap-2 mt-1">
              {EXP_LEVELS.map((lvl) => (
                <button
                  key={lvl.value}
                  type="button"
                  onClick={() => setExpLevel(lvl.value)}
                  className={`px-4 py-2.5 rounded-xl text-sm font-medium border cursor-pointer transition-all ${
                    expLevel === lvl.value
                      ? 'bg-primary-600 text-white border-primary-600 shadow-sm shadow-primary-600/20'
                      : 'bg-white text-gray-600 border-gray-200 hover:border-primary-300 hover:bg-primary-50'
                  }`}
                >
                  {lvl.label}
                </button>
              ))}
            </div>
          </div>
          <div>
            <Toggle checked={employed} onChange={setEmployed} label="Currently Employed" />
          </div>
        </div>
        <SaveBtn onClick={saveCareer} saving={saving2} saved={saved2} />
      </Card>
    </div>
  );
}

/* ── Tab 2: Account Security ──────────────────────────────────── */

function SecurityTab() {
  const [curPwd, setCurPwd] = useState('');
  const [newPwd, setNewPwd] = useState('');
  const [confirmPwd, setConfirmPwd] = useState('');
  const [showCur, setShowCur] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [pwdError, setPwdError] = useState('');
  const [pwdSuccess, setPwdSuccess] = useState('');
  const [saving, setSaving] = useState(false);
  const [deleteModal, setDeleteModal] = useState(false);
  const [deletePwd, setDeletePwd] = useState('');
  const [deleteError, setDeleteError] = useState('');
  const [deleting, setDeleting] = useState(false);

  const passwordStrength = useMemo(() => {
    if (!newPwd) return 0;
    let s = 0;
    if (newPwd.length >= 8) s++;
    if (/[A-Z]/.test(newPwd)) s++;
    if (/[0-9]/.test(newPwd)) s++;
    if (/[^A-Za-z0-9]/.test(newPwd)) s++;
    return s;
  }, [newPwd]);

  const strengthColors = ['bg-red-400', 'bg-orange-400', 'bg-yellow-400', 'bg-emerald-400'];
  const strengthLabels = ['Weak', 'Fair', 'Good', 'Strong'];

  const changePassword = async () => {
    setPwdError('');
    setPwdSuccess('');
    if (newPwd !== confirmPwd) { setPwdError("Passwords don't match"); return; }
    setSaving(true);
    try {
      await api.post('/users/auth/change-password/', {
        current_password: curPwd,
        new_password: newPwd,
        new_password_confirm: confirmPwd,
      });
      setPwdSuccess('Password changed successfully');
      setCurPwd(''); setNewPwd(''); setConfirmPwd('');
    } catch (err) {
      const data = err.response?.data;
      setPwdError(
        data?.current_password?.[0] ||
        data?.new_password?.[0] ||
        data?.non_field_errors?.[0] ||
        'Failed to change password'
      );
    }
    setSaving(false);
  };

  const deleteAccount = async () => {
    setDeleteError('');
    setDeleting(true);
    try {
      await api.post('/users/auth/delete-account/', { password: deletePwd });
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      window.location.href = '/login';
    } catch (err) {
      setDeleteError(err.response?.data?.error || 'Failed to delete account');
    }
    setDeleting(false);
  };

  return (
    <div className="space-y-6">
      <Card>
        <SectionTitle sub="Update your password to keep your account secure">Change Password</SectionTitle>
        <div className="space-y-4 max-w-md">
          <div>
            <Label htmlFor="cur_pwd">Current Password</Label>
            <div className="relative">
              <Input id="cur_pwd" type={showCur ? 'text' : 'password'} value={curPwd} onChange={(e) => setCurPwd(e.target.value)} placeholder="Enter current password" />
              <button onClick={() => setShowCur(!showCur)} className="absolute right-3 top-1/2 -translate-y-1/2 bg-transparent border-none cursor-pointer text-gray-400 hover:text-gray-600">
                {showCur ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>
          <div>
            <Label htmlFor="new_pwd">New Password</Label>
            <div className="relative">
              <Input id="new_pwd" type={showNew ? 'text' : 'password'} value={newPwd} onChange={(e) => setNewPwd(e.target.value)} placeholder="Enter new password" />
              <button onClick={() => setShowNew(!showNew)} className="absolute right-3 top-1/2 -translate-y-1/2 bg-transparent border-none cursor-pointer text-gray-400 hover:text-gray-600">
                {showNew ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
            {newPwd && (
              <div className="mt-2.5">
                <div className="flex gap-1 h-1.5 rounded-full overflow-hidden">
                  {[0, 1, 2, 3].map((i) => (
                    <div key={i} className={`flex-1 rounded-full transition-all duration-300 ${i < passwordStrength ? strengthColors[passwordStrength - 1] : 'bg-gray-200'}`} />
                  ))}
                </div>
                <p className={`text-xs mt-1 font-medium ${passwordStrength >= 3 ? 'text-emerald-600' : passwordStrength >= 2 ? 'text-yellow-600' : 'text-red-500'}`}>
                  {strengthLabels[passwordStrength - 1] || 'Too short'}
                </p>
              </div>
            )}
          </div>
          <div>
            <Label htmlFor="confirm_pwd">Confirm New Password</Label>
            <Input id="confirm_pwd" type="password" value={confirmPwd} onChange={(e) => setConfirmPwd(e.target.value)} placeholder="Confirm new password" />
          </div>

          {pwdError && <div className="flex items-center gap-2 text-sm text-red-500 bg-red-50 px-3 py-2 rounded-lg"><AlertTriangle className="w-4 h-4 flex-shrink-0" />{pwdError}</div>}
          {pwdSuccess && <div className="flex items-center gap-2 text-sm text-emerald-600 bg-emerald-50 px-3 py-2 rounded-lg"><Check className="w-4 h-4 flex-shrink-0" />{pwdSuccess}</div>}

          <button
            onClick={changePassword}
            disabled={saving || !curPwd || !newPwd || !confirmPwd}
            className="h-11 px-7 bg-primary-600 text-white rounded-xl text-sm font-semibold border-none cursor-pointer
              hover:bg-primary-700 hover:shadow-md disabled:opacity-60 transition-all"
          >
            {saving ? 'Updating...' : 'Update Password'}
          </button>
        </div>
      </Card>

      <Card>
        <SectionTitle sub="Devices currently logged into your account">Active Sessions</SectionTitle>
        <div className="bg-gradient-to-r from-gray-50 to-emerald-50/30 rounded-xl px-4 py-3.5 flex items-center justify-between border border-gray-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-white rounded-xl flex items-center justify-center shadow-sm border border-gray-100">
              <Monitor className="w-5 h-5 text-gray-600" />
            </div>
            <div>
              <p className="text-sm font-semibold text-gray-800">Current Session</p>
              <p className="text-xs text-gray-400">This device &middot; Active now</p>
            </div>
          </div>
          <span className="text-xs bg-emerald-100 text-emerald-700 px-2.5 py-1 rounded-full font-semibold flex items-center gap-1">
            <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full" />
            Active
          </span>
        </div>
      </Card>

      <Card danger>
        <SectionTitle sub="Permanent actions that cannot be undone">Danger Zone</SectionTitle>
        <p className="text-sm text-gray-500 mb-4">Deleting your account will remove all your data, skills, roadmaps, and progress permanently.</p>
        <button
          onClick={() => setDeleteModal(true)}
          className="h-11 px-6 bg-white text-red-600 border-2 border-red-200 rounded-xl text-sm font-semibold cursor-pointer
            hover:bg-red-50 hover:border-red-300 transition-all"
        >
          Delete My Account
        </button>
      </Card>

      {/* Delete confirmation modal */}
      {deleteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl p-6 w-full max-w-md mx-4 border border-gray-100">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-11 h-11 bg-red-100 rounded-xl flex items-center justify-center">
                <AlertTriangle className="w-5 h-5 text-red-600" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-gray-900">Delete Account</h3>
                <p className="text-xs text-gray-400">This action cannot be undone</p>
              </div>
            </div>
            <p className="text-sm text-gray-600 mb-4">All your data will be permanently deleted. Enter your password to confirm.</p>
            <Label htmlFor="delete_pwd">Password</Label>
            <Input id="delete_pwd" type="password" value={deletePwd} onChange={(e) => setDeletePwd(e.target.value)} placeholder="Your password" />
            {deleteError && <div className="flex items-center gap-2 text-sm text-red-500 bg-red-50 px-3 py-2 rounded-lg mt-2"><AlertTriangle className="w-4 h-4 flex-shrink-0" />{deleteError}</div>}
            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => { setDeleteModal(false); setDeletePwd(''); setDeleteError(''); }}
                className="h-10 px-5 bg-gray-100 text-gray-700 rounded-xl text-sm font-medium border-none cursor-pointer hover:bg-gray-200 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={deleteAccount}
                disabled={deleting || !deletePwd}
                className="h-10 px-5 bg-red-600 text-white rounded-xl text-sm font-semibold border-none cursor-pointer
                  hover:bg-red-700 disabled:opacity-60 transition-all"
              >
                {deleting ? 'Deleting...' : 'Delete Account'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/* ── Tab 3: Preferences ────────────────────────────────────────── */

function PreferencesTab({ user, onUserUpdate }) {
  const [lang, setLang] = useState(user?.preferred_language || 'en');
  const [theme, setTheme] = useState('light');
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const save = async () => {
    setSaving(true);
    try {
      await api.patch('/users/auth/update/', { preferred_language: lang });
      onUserUpdate();
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch { /* ignore */ }
    setSaving(false);
  };

  const LANGUAGES = [
    { value: 'en', label: 'English',  flag: '🇬🇧' },
    { value: 'ru', label: 'Russian', flag: '🇷🇺' },
    { value: 'uz', label: 'Uzbek',   flag: '🇺🇿' },
  ];

  const THEMES = [
    { value: 'light', label: 'Light', icon: Sun,     disabled: false },
    { value: 'dark',  label: 'Dark',  icon: Moon,    disabled: true },
    { value: 'auto',  label: 'System',icon: Monitor, disabled: true },
  ];

  return (
    <div className="space-y-6">
      <Card>
        <SectionTitle sub="Choose your preferred interface language">Language</SectionTitle>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {LANGUAGES.map((l) => (
            <button
              key={l.value}
              onClick={() => setLang(l.value)}
              className={`flex items-center gap-3 px-4 py-4 rounded-xl border-2 text-left cursor-pointer transition-all ${
                lang === l.value
                  ? 'border-primary-500 bg-primary-50 shadow-sm shadow-primary-500/10'
                  : 'border-gray-100 bg-white hover:border-gray-200 hover:shadow-sm'
              }`}
            >
              <span className="text-2xl">{l.flag}</span>
              <div>
                <p className={`text-sm font-semibold ${lang === l.value ? 'text-primary-700' : 'text-gray-800'}`}>{l.label}</p>
              </div>
              {lang === l.value && (
                <div className="ml-auto w-5 h-5 bg-primary-600 rounded-full flex items-center justify-center">
                  <Check className="w-3 h-3 text-white" />
                </div>
              )}
            </button>
          ))}
        </div>
      </Card>

      <Card>
        <SectionTitle sub="Customize the look and feel of SkillBridge">Theme</SectionTitle>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {THEMES.map((t) => {
            const Icon = t.icon;
            return (
              <button
                key={t.value}
                onClick={() => !t.disabled && setTheme(t.value)}
                disabled={t.disabled}
                className={`relative flex flex-col items-center gap-3 px-4 py-5 rounded-xl border-2 cursor-pointer transition-all ${
                  theme === t.value
                    ? 'border-primary-500 bg-primary-50 shadow-sm shadow-primary-500/10'
                    : t.disabled
                      ? 'border-gray-100 bg-gray-50 cursor-not-allowed opacity-60'
                      : 'border-gray-100 bg-white hover:border-gray-200 hover:shadow-sm'
                }`}
              >
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                  theme === t.value ? 'bg-primary-100' : 'bg-gray-100'
                }`}>
                  <Icon className={`w-6 h-6 ${theme === t.value ? 'text-primary-600' : 'text-gray-400'}`} />
                </div>
                <span className={`text-sm font-semibold ${theme === t.value ? 'text-primary-700' : 'text-gray-600'}`}>
                  {t.label}
                </span>
                {t.disabled && (
                  <span className="absolute top-2 right-2 text-[10px] bg-gray-200 text-gray-500 px-2 py-0.5 rounded-full font-medium">
                    Soon
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </Card>

      <SaveBtn onClick={save} saving={saving} saved={saved} />
    </div>
  );
}

/* ── Main Settings Page ────────────────────────────────────────── */

export default function SettingsPage() {
  const { user, fetchUser, logout } = useAuthStore();
  const [profile, setProfile] = useState(null);
  const [activeTab, setActiveTab] = useState('profile');
  const [loading, setLoading] = useState(true);
  const [searchParams, setSearchParams] = useSearchParams();

  useEffect(() => {
    const tab = searchParams.get('tab');
    if (tab && TABS.find((t) => t.key === tab)) {
      setActiveTab(tab);
    }
  }, [searchParams]);

  const changeTab = (key) => {
    setActiveTab(key);
    setSearchParams({ tab: key });
  };

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    setLoading(true);
    try {
      await fetchUser();
      const { data } = await api.get('/users/profile/');
      setProfile(data);
    } catch { /* ignore */ }
    setLoading(false);
  };

  const currentUser = useAuthStore.getState().user || user;

  if (loading) {
    return (
      <DashboardLayout user={currentUser}>
        <div className="flex items-center justify-center h-64">
          <div className="w-8 h-8 border-3 border-primary-600 border-t-transparent rounded-full animate-spin" />
        </div>
      </DashboardLayout>
    );
  }

  const renderTab = () => {
    switch (activeTab) {
      case 'profile':
        return <ProfileTab user={currentUser} profile={profile} onUserUpdate={loadProfile} />;
      case 'security':
        return <SecurityTab />;
      case 'preferences':
        return <PreferencesTab user={currentUser} onUserUpdate={loadProfile} />;
      default:
        return null;
    }
  };

  return (
    <DashboardLayout user={currentUser}>
      {/* Page header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-1">
          <div className="w-10 h-10 bg-gradient-to-br from-gray-100 to-gray-200 rounded-xl flex items-center justify-center">
            <Settings className="w-5 h-5 text-gray-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
            <p className="text-sm text-gray-400">Manage your account and preferences</p>
          </div>
        </div>
      </div>

      {/* Tab navigation — elegant pill bar */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-1.5 mb-6 inline-flex gap-1">
        {TABS.map((tab) => {
          const Icon = tab.icon;
          const active = activeTab === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => changeTab(tab.key)}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold border-none cursor-pointer transition-all ${
                active
                  ? 'bg-primary-600 text-white shadow-sm shadow-primary-600/20'
                  : 'bg-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-50'
              }`}
            >
              <Icon className={`w-4 h-4 ${active ? 'text-white' : 'text-gray-400'}`} />
              <span className="hidden sm:inline">{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Tab content */}
      <div className="max-w-[800px]">
        {renderTab()}
      </div>
    </DashboardLayout>
  );
}
