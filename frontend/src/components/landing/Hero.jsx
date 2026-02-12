import { Link } from 'react-router-dom';
import { ArrowRight, BarChart3 } from 'lucide-react';
import { useTranslation } from 'react-i18next';

export default function Hero() {
  const { t } = useTranslation();

  return (
    <section className="relative min-h-[90vh] flex items-center overflow-hidden">
      {/* Animated gradient background */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary-600 via-primary-700 to-purple-600">
        <div className="absolute inset-0 opacity-30">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-purple-400 rounded-full blur-3xl animate-pulse" />
          <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-primary-300 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
        </div>
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 text-center">
        <div className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-sm text-white text-sm font-medium px-4 py-2 rounded-full mb-8 border border-white/20">
          <span className="w-2 h-2 bg-success-500 rounded-full animate-pulse" />
          {t('hero.badge')}
        </div>

        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-white leading-tight mb-6 max-w-4xl mx-auto">
          {t('hero.title')}{' '}
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-200 to-purple-400">
            {t('hero.titleHighlight')}
          </span>
        </h1>

        <p className="text-lg sm:text-xl text-primary-100 max-w-2xl mx-auto mb-10 leading-relaxed">
          {t('hero.subtitle')}
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link
            to="/assessment"
            className="inline-flex items-center gap-2 px-8 py-4 text-base font-semibold text-primary-700 bg-white rounded-xl hover:bg-primary-50 no-underline transition-all shadow-lg shadow-primary-900/20 hover:shadow-xl"
          >
            {t('hero.cta')}
            <ArrowRight className="w-5 h-5" />
          </Link>

          <Link
            to="/dashboard"
            className="inline-flex items-center gap-2 px-8 py-4 text-base font-semibold text-white border-2 border-white/30 rounded-xl hover:bg-white/10 no-underline transition-all backdrop-blur-sm"
          >
            <BarChart3 className="w-5 h-5" />
            {t('hero.secondary')}
          </Link>
        </div>
      </div>
    </section>
  );
}
