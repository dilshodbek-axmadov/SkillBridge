import { useState, useEffect, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  User, Shield, Globe,
  Camera, Check, Eye, EyeOff,
  AlertTriangle, Monitor, Moon, Sun, Settings,
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import DashboardLayout from '../components/layout/DashboardLayout';
import RecruiterLayout from '../components/layout/RecruiterLayout';
import useAuthStore from '../store/authStore';
import useThemeStore from '../store/themeStore';
import api from '../services/api';
import { safeRemoveItem } from '../utils/safeStorage';

/* ── Constants ─────────────────────────────────────────────────── */

const TABS = [
  { key: 'profile',     labelKey: 'settings.tabs.profile',     descKey: 'settings.tabs.profileDesc',     icon: User },
  { key: 'security',    labelKey: 'settings.tabs.security',    descKey: 'settings.tabs.securityDesc',    icon: Shield },
  { key: 'preferences', labelKey: 'settings.tabs.preferences', descKey: 'settings.tabs.preferencesDesc', icon: Globe },
];

const UZ_CITIES = [
  'Tashkent', 'Samarkand', 'Bukhara', 'Namangan', 'Andijan',
  'Fergana', 'Nukus', 'Karshi', 'Kokand', 'Margilan',
  'Jizzakh', 'Urgench', 'Navoi', 'Termez', 'Gulistan',
];

const EXP_LEVELS = ['beginner', 'junior', 'mid', 'senior', 'lead'];

/* ── Shared UI Primitives ──────────────────────────────────────── */

function Card({ children, className = '', danger = false }) {
  return (
    <div className={`bg-white dark:bg-gray-900 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-800 p-6 ${danger ? 'border-l-4 !border-l-red-400' : ''} ${className}`}>
      {children}
    </div>
  );
}

function SectionTitle({ children, sub }) {
  return (
    <div className="mb-5">
      <h3 className="text-[17px] font-bold text-gray-800 dark:text-gray-100">{children}</h3>
      {sub && <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">{sub}</p>}
    </div>
  );
}

function Label({ children, htmlFor }) {
  return <label htmlFor={htmlFor} className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1.5">{children}</label>;
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
      className={`w-full h-11 px-3.5 rounded-xl border border-gray-200 dark:border-gray-700 text-sm text-gray-900 dark:text-gray-100 bg-white dark:bg-gray-800 outline-none transition-all
        focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 focus:shadow-sm
        disabled:bg-gray-50 dark:disabled:bg-gray-800/50 disabled:text-gray-400 ${className}`}
    />
  );
}

function Toggle({ checked, onChange, label }) {
  return (
    <div className="flex items-center justify-between py-2">
      <span className="text-sm text-gray-700 dark:text-gray-300">{label}</span>
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
  const { t } = useTranslation();
  return (
    <div className="flex justify-end mt-6">
      <button
        onClick={onClick}
        disabled={saving}
        className="h-11 px-7 bg-primary-600 text-white rounded-xl text-sm font-semibold border-none cursor-pointer
          hover:bg-primary-700 hover:shadow-md disabled:opacity-60 transition-all flex items-center gap-2"
      >
        {saving ? t('settings.save.saving') : saved ? <><Check className="w-4 h-4" /> {t('settings.save.saved')}</> : t('settings.save.cta')}
      </button>
    </div>
  );
}

/* ── Tab 1: Profile Information ────────────────────────────────── */

function ProfileTab({ user, profile, onUserUpdate }) {
  const { t } = useTranslation();
  const isRecruiter = user?.user_type === 'recruiter';
  const [firstName, setFirstName] = useState(user?.first_name || '');
  const [lastName, setLastName] = useState(user?.last_name || '');
  const [phone, setPhone] = useState(user?.phone || '');
  const [location, setLocation] = useState(profile?.location || '');
  const [bio, setBio] = useState(profile?.bio || '');
  const [jobPosition, setJobPosition] = useState(profile?.current_job_position || '');
  const [expLevel, setExpLevel] = useState(profile?.experience_level || 'beginner');
  const [desiredRole, setDesiredRole] = useState(profile?.desired_role || '');
  const [employed, setEmployed] = useState(!!profile?.current_job_position);
  const [openToRecruiters, setOpenToRecruiters] = useState(
    profile?.open_to_recruiters !== undefined ? !!profile.open_to_recruiters : true
  );
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
        open_to_recruiters: openToRecruiters,
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
        <SectionTitle sub={t('settings.profile.personalSub')}>{t('settings.profile.personalTitle')}</SectionTitle>

        {/* Avatar */}
        <div className="flex items-center gap-5 mb-7 p-4 bg-gradient-to-r from-primary-50 to-purple-50 dark:from-primary-900/20 dark:to-purple-900/20 rounded-2xl">
          <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-primary-500 to-purple-500 flex items-center justify-center text-white text-2xl font-bold relative group cursor-pointer shadow-lg shadow-primary-500/20">
            {initial}
            <div className="absolute inset-0 bg-black/40 rounded-2xl flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
              <Camera className="w-5 h-5 text-white" />
            </div>
          </div>
          <div>
            <p className="text-base font-semibold text-gray-800 dark:text-gray-100">{user?.full_name || user?.email}</p>
            <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">{t('settings.profile.avatarHint')}</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <Label htmlFor="first_name">{t('settings.profile.firstName')}</Label>
            <Input id="first_name" value={firstName} onChange={(e) => setFirstName(e.target.value)} placeholder={t('settings.profile.firstNamePlaceholder')} />
          </div>
          <div>
            <Label htmlFor="last_name">{t('settings.profile.lastName')}</Label>
            <Input id="last_name" value={lastName} onChange={(e) => setLastName(e.target.value)} placeholder={t('settings.profile.lastNamePlaceholder')} />
          </div>
          <div>
            <Label htmlFor="email">{t('settings.profile.email')}</Label>
            <div className="relative">
              <Input id="email" value={user?.email || ''} disabled />
              <span className="absolute right-3 top-1/2 -translate-y-1/2 text-[11px] bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full font-semibold flex items-center gap-1">
                <Check className="w-3 h-3" /> {t('settings.profile.verified')}
              </span>
            </div>
          </div>
          <div>
            <Label htmlFor="phone">{t('settings.profile.phone')}</Label>
            <Input id="phone" value={phone} onChange={(e) => setPhone(e.target.value)} placeholder={t('settings.profile.phonePlaceholder')} />
          </div>
          <div>
            <Label htmlFor="location">{t('settings.profile.location')}</Label>
            <select
              id="location"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              className="w-full h-11 px-3.5 rounded-xl border border-gray-200 dark:border-gray-700 text-sm text-gray-900 dark:text-gray-100 outline-none bg-white dark:bg-gray-800
                focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 transition-all"
            >
              <option value="">{t('settings.profile.locationPlaceholder')}</option>
              {UZ_CITIES.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <div className="md:col-span-2">
            <Label htmlFor="bio">{t('settings.profile.bio')}</Label>
            <textarea
              id="bio"
              value={bio}
              onChange={(e) => setBio(e.target.value)}
              rows={5}
              placeholder={t('settings.profile.bioPlaceholder')}
              className="w-full px-3.5 py-2.5 rounded-xl border border-gray-200 dark:border-gray-700 text-sm text-gray-900 dark:text-gray-100 bg-white dark:bg-gray-800 outline-none resize-y
                focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 transition-all"
            />
            <p className="text-xs text-gray-400 text-right mt-1">{bio.length} {t('settings.profile.charsLabel', 'characters')}</p>
          </div>
        </div>
        <SaveBtn onClick={savePersonal} saving={saving1} saved={saved1} />
      </Card>

      {!isRecruiter && (
        <Card>
          <SectionTitle sub={t('settings.profile.careerSub')}>{t('settings.profile.careerTitle')}</SectionTitle>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label htmlFor="job_position">{t('settings.profile.currentJob')}</Label>
              <Input id="job_position" value={jobPosition} onChange={(e) => setJobPosition(e.target.value)} placeholder={t('settings.profile.currentJobPlaceholder')} />
            </div>
            <div>
              <Label htmlFor="desired_role">{t('settings.profile.desiredRole')}</Label>
              <Input id="desired_role" value={desiredRole} onChange={(e) => setDesiredRole(e.target.value)} placeholder={t('settings.profile.desiredRolePlaceholder')} />
            </div>
            <div className="md:col-span-2">
              <Label>{t('settings.profile.expLevel')}</Label>
              <div className="flex flex-wrap gap-2 mt-1">
                {EXP_LEVELS.map((lvl) => (
                  <button
                    key={lvl}
                    type="button"
                    onClick={() => setExpLevel(lvl)}
                    className={`px-4 py-2.5 rounded-xl text-sm font-medium border cursor-pointer transition-all ${
                      expLevel === lvl
                        ? 'bg-primary-600 text-white border-primary-600 shadow-sm shadow-primary-600/20'
                        : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300 border-gray-200 dark:border-gray-700 hover:border-primary-300 hover:bg-primary-50 dark:hover:bg-gray-700'
                    }`}
                  >
                    {t(`settings.profile.expLevels.${lvl}`)}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <Toggle checked={employed} onChange={setEmployed} label={t('settings.profile.employed')} />
            </div>
            <div className="md:col-span-2 border-t border-gray-100 dark:border-gray-800 pt-3 mt-1">
              <Toggle
                checked={openToRecruiters}
                onChange={setOpenToRecruiters}
                label={t('settings.profile.openToRecruiters', 'Open to recruiters (visible in recruiter search)')}
              />
              <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                {t(
                  'settings.profile.openToRecruitersHint',
                  'When off, your profile will not appear to recruiters searching for candidates.'
                )}
              </p>
            </div>
          </div>
          <SaveBtn onClick={saveCareer} saving={saving2} saved={saved2} />
        </Card>
      )}
    </div>
  );
}

/* ── Tab 2: Account Security ──────────────────────────────────── */

function SecurityTab() {
  const { t } = useTranslation();
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
  const strengthLabels = [
    t('settings.security.strength.weak'),
    t('settings.security.strength.fair'),
    t('settings.security.strength.good'),
    t('settings.security.strength.strong'),
  ];

  const changePassword = async () => {
    setPwdError('');
    setPwdSuccess('');
    if (newPwd !== confirmPwd) { setPwdError(t('settings.security.errors.mismatch')); return; }
    setSaving(true);
    try {
      await api.post('/users/auth/change-password/', {
        current_password: curPwd,
        new_password: newPwd,
        new_password_confirm: confirmPwd,
      });
      setPwdSuccess(t('settings.security.success.changed'));
      setCurPwd(''); setNewPwd(''); setConfirmPwd('');
    } catch (err) {
      const data = err.response?.data;
      setPwdError(
        data?.current_password?.[0] ||
        data?.new_password?.[0] ||
        data?.non_field_errors?.[0] ||
        t('settings.security.errors.changeFailed')
      );
    }
    setSaving(false);
  };

  const deleteAccount = async () => {
    setDeleteError('');
    setDeleting(true);
    try {
      await api.post('/users/auth/delete-account/', { password: deletePwd });
      safeRemoveItem('access_token');
      safeRemoveItem('refresh_token');
      window.location.href = '/login';
    } catch (err) {
      setDeleteError(err.response?.data?.error || t('settings.security.errors.deleteFailed'));
    }
    setDeleting(false);
  };

  return (
    <div className="space-y-6">
      <Card>
        <SectionTitle sub={t('settings.security.changeSub')}>{t('settings.security.changeTitle')}</SectionTitle>
        <div className="space-y-4 max-w-md">
          <div>
            <Label htmlFor="cur_pwd">{t('settings.security.currentPassword')}</Label>
            <div className="relative">
              <Input id="cur_pwd" type={showCur ? 'text' : 'password'} value={curPwd} onChange={(e) => setCurPwd(e.target.value)} placeholder={t('settings.security.currentPasswordPlaceholder')} />
              <button onClick={() => setShowCur(!showCur)} className="absolute right-3 top-1/2 -translate-y-1/2 bg-transparent border-none cursor-pointer text-gray-400 hover:text-gray-600">
                {showCur ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>
          <div>
            <Label htmlFor="new_pwd">{t('settings.security.newPassword')}</Label>
            <div className="relative">
              <Input id="new_pwd" type={showNew ? 'text' : 'password'} value={newPwd} onChange={(e) => setNewPwd(e.target.value)} placeholder={t('settings.security.newPasswordPlaceholder')} />
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
                  {strengthLabels[passwordStrength - 1] || t('settings.security.strength.tooShort')}
                </p>
              </div>
            )}
          </div>
          <div>
            <Label htmlFor="confirm_pwd">{t('settings.security.confirmPassword')}</Label>
            <Input id="confirm_pwd" type="password" value={confirmPwd} onChange={(e) => setConfirmPwd(e.target.value)} placeholder={t('settings.security.confirmPasswordPlaceholder')} />
          </div>

          {pwdError && <div className="flex items-center gap-2 text-sm text-red-500 bg-red-50 px-3 py-2 rounded-lg"><AlertTriangle className="w-4 h-4 flex-shrink-0" />{pwdError}</div>}
          {pwdSuccess && <div className="flex items-center gap-2 text-sm text-emerald-600 bg-emerald-50 px-3 py-2 rounded-lg"><Check className="w-4 h-4 flex-shrink-0" />{pwdSuccess}</div>}

          <button
            onClick={changePassword}
            disabled={saving || !curPwd || !newPwd || !confirmPwd}
            className="h-11 px-7 bg-primary-600 text-white rounded-xl text-sm font-semibold border-none cursor-pointer
              hover:bg-primary-700 hover:shadow-md disabled:opacity-60 transition-all"
          >
            {saving ? t('settings.security.updating') : t('settings.security.updatePassword')}
          </button>
        </div>
      </Card>

      <Card>
        <SectionTitle sub={t('settings.security.sessionsSub')}>{t('settings.security.sessionsTitle')}</SectionTitle>
        <div className="bg-gradient-to-r from-gray-50 to-emerald-50/30 dark:from-gray-800 dark:to-emerald-900/10 rounded-xl px-4 py-3.5 flex items-center justify-between border border-gray-100 dark:border-gray-800">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-white dark:bg-gray-700 rounded-xl flex items-center justify-center shadow-sm border border-gray-100 dark:border-gray-600">
              <Monitor className="w-5 h-5 text-gray-600 dark:text-gray-300" />
            </div>
            <div>
              <p className="text-sm font-semibold text-gray-800 dark:text-gray-100">{t('settings.security.currentSession')}</p>
              <p className="text-xs text-gray-400 dark:text-gray-500">{t('settings.security.currentSessionMeta')}</p>
            </div>
          </div>
          <span className="text-xs bg-emerald-100 text-emerald-700 px-2.5 py-1 rounded-full font-semibold flex items-center gap-1">
            <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full" />
            {t('settings.security.active')}
          </span>
        </div>
      </Card>

      <Card danger>
        <SectionTitle sub={t('settings.security.dangerSub')}>{t('settings.security.dangerTitle')}</SectionTitle>
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">{t('settings.security.deleteWarning')}</p>
        <button
          onClick={() => setDeleteModal(true)}
          className="h-11 px-6 bg-white text-red-600 border-2 border-red-200 rounded-xl text-sm font-semibold cursor-pointer
            hover:bg-red-50 hover:border-red-300 transition-all"
        >
          {t('settings.security.deleteAccount')}
        </button>
      </Card>

      {/* Delete confirmation modal */}
      {deleteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
          <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl p-6 w-full max-w-md mx-4 border border-gray-100 dark:border-gray-800">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-11 h-11 bg-red-100 dark:bg-red-900/30 rounded-xl flex items-center justify-center">
                <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400" />
              </div>
              <div>
            <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">{t('settings.security.deleteModalTitle')}</h3>
                <p className="text-xs text-gray-400 dark:text-gray-500">{t('settings.security.deleteModalSub')}</p>
              </div>
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">{t('settings.security.deleteModalBody')}</p>
            <Label htmlFor="delete_pwd">{t('settings.security.password')}</Label>
            <Input id="delete_pwd" type="password" value={deletePwd} onChange={(e) => setDeletePwd(e.target.value)} placeholder={t('settings.security.passwordPlaceholder')} />
            {deleteError && <div className="flex items-center gap-2 text-sm text-red-500 bg-red-50 px-3 py-2 rounded-lg mt-2"><AlertTriangle className="w-4 h-4 flex-shrink-0" />{deleteError}</div>}
            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => { setDeleteModal(false); setDeletePwd(''); setDeleteError(''); }}
                className="h-10 px-5 bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-xl text-sm font-medium border-none cursor-pointer hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
              >
                {t('settings.security.cancel')}
              </button>
              <button
                onClick={deleteAccount}
                disabled={deleting || !deletePwd}
                className="h-10 px-5 bg-red-600 text-white rounded-xl text-sm font-semibold border-none cursor-pointer
                  hover:bg-red-700 disabled:opacity-60 transition-all"
              >
                {deleting ? t('settings.security.deleting') : t('settings.security.deleteAccount')}
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
  const { i18n, t } = useTranslation();
  const [lang, setLang] = useState(i18n.language || user?.preferred_language || 'en');
  const { theme, setTheme } = useThemeStore();
  const [selectedTheme, setSelectedTheme] = useState(theme);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    setSelectedTheme(theme);
  }, [theme]);

  const save = async () => {
    setSaving(true);
    try {
      await api.patch('/users/auth/update/', { preferred_language: lang });
      i18n.changeLanguage(lang);
      setTheme(selectedTheme);
      onUserUpdate();
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch { /* ignore */ }
    setSaving(false);
  };

  const LANGUAGES = [
    { value: 'en', label: 'English',  flag: '🇬🇧' },
    { value: 'ru', label: 'Русский', flag: '🇷🇺' },
    { value: 'uz', label: "O'zbekcha",   flag: '🇺🇿' },
  ];

  const THEMES = [
    { value: 'light',  labelKey: 'settings.theme.light',  icon: Sun },
    { value: 'dark',   labelKey: 'settings.theme.dark',   icon: Moon },
    { value: 'system', labelKey: 'settings.theme.system', icon: Monitor },
  ];

  return (
    <div className="space-y-6">
      <Card>
        <SectionTitle sub={t('settings.languageSub')}>{t('settings.language')}</SectionTitle>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {LANGUAGES.map((l) => (
            <button
              key={l.value}
              onClick={() => setLang(l.value)}
              className={`flex items-center gap-3 px-4 py-4 rounded-xl border-2 text-left cursor-pointer transition-all ${
                lang === l.value
                  ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/30 shadow-sm shadow-primary-500/10'
                  : 'border-gray-100 dark:border-gray-700 bg-white dark:bg-gray-800 hover:border-gray-200 dark:hover:border-gray-600 hover:shadow-sm'
              }`}
            >
              <span className="text-2xl">{l.flag}</span>
              <div>
                <p className={`text-sm font-semibold ${lang === l.value ? 'text-primary-700 dark:text-primary-400' : 'text-gray-800 dark:text-gray-200'}`}>{l.label}</p>
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
        <SectionTitle sub={t('settings.themeSub')}>{t('settings.theme')}</SectionTitle>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {THEMES.map((themeOption) => {
            const Icon = themeOption.icon;
            return (
              <button
                key={themeOption.value}
                onClick={() => setSelectedTheme(themeOption.value)}
                className={`relative flex flex-col items-center gap-3 px-4 py-5 rounded-xl border-2 cursor-pointer transition-all ${
                  selectedTheme === themeOption.value
                    ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/30 shadow-sm shadow-primary-500/10'
                    : 'border-gray-100 dark:border-gray-700 bg-white dark:bg-gray-800 hover:border-gray-200 dark:hover:border-gray-600 hover:shadow-sm'
                }`}
              >
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                  selectedTheme === themeOption.value ? 'bg-primary-100 dark:bg-primary-900/50' : 'bg-gray-100 dark:bg-gray-700'
                }`}>
                  <Icon className={`w-6 h-6 ${selectedTheme === themeOption.value ? 'text-primary-600 dark:text-primary-400' : 'text-gray-400'}`} />
                </div>
                <span className={`text-sm font-semibold ${selectedTheme === themeOption.value ? 'text-primary-700 dark:text-primary-400' : 'text-gray-600 dark:text-gray-300'}`}>
                  {t(themeOption.labelKey)}
                </span>
                {selectedTheme === themeOption.value && (
                  <div className="absolute top-2 right-2 w-5 h-5 bg-primary-600 rounded-full flex items-center justify-center">
                    <Check className="w-3 h-3 text-white" />
                  </div>
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
  const { t } = useTranslation();
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
  const Shell = currentUser?.user_type === 'recruiter' ? RecruiterLayout : DashboardLayout;

  if (loading) {
    return (
      <Shell user={currentUser}>
        <div className="flex items-center justify-center h-64">
          <div className="w-8 h-8 border-3 border-primary-600 border-t-transparent rounded-full animate-spin" />
        </div>
      </Shell>
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
    <Shell user={currentUser}>
      {/* Page header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-1">
          <div className="w-10 h-10 bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-800 dark:to-gray-700 rounded-xl flex items-center justify-center">
            <Settings className="w-5 h-5 text-gray-600 dark:text-gray-300" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">{t('settings.title')}</h1>
            <p className="text-sm text-gray-400 dark:text-gray-500">{t('settings.subtitle')}</p>
          </div>
        </div>
      </div>

      {/* Tab navigation — elegant pill bar */}
      <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-800 p-1.5 mb-6 inline-flex gap-1">
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
                  : 'bg-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-800'
              }`}
            >
              <Icon className={`w-4 h-4 ${active ? 'text-white' : 'text-gray-400'}`} />
              <span className="hidden sm:inline">{t(tab.labelKey)}</span>
            </button>
          );
        })}
      </div>

      {/* Tab content */}
      <div className="max-w-[800px]">
        {renderTab()}
      </div>
    </Shell>
  );
}
