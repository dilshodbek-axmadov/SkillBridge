import { ClipboardCheck, Compass, Search, Route, LineChart, FileText } from 'lucide-react';
import { useTranslation } from 'react-i18next';

const stepKeys = [
  { icon: ClipboardCheck, titleKey: 'howItWorks.step1.title', descKey: 'howItWorks.step1.desc', color: 'bg-primary-600' },
  { icon: Compass,        titleKey: 'howItWorks.step2.title', descKey: 'howItWorks.step2.desc', color: 'bg-purple-600' },
  { icon: Search,         titleKey: 'howItWorks.step3.title', descKey: 'howItWorks.step3.desc', color: 'bg-success-600' },
  { icon: Route,          titleKey: 'howItWorks.step4.title', descKey: 'howItWorks.step4.desc', color: 'bg-orange-600' },
  { icon: LineChart,      titleKey: 'howItWorks.step5.title', descKey: 'howItWorks.step5.desc', color: 'bg-pink-600' },
  { icon: FileText,       titleKey: 'howItWorks.step6.title', descKey: 'howItWorks.step6.desc', color: 'bg-cyan-600' },
];

export default function HowItWorks() {
  const { t } = useTranslation();

  return (
    <section className="py-24 bg-white dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-gray-100 mb-4">
            {t('howItWorks.title')}
          </h2>
          <p className="text-lg text-gray-500 dark:text-gray-400 max-w-2xl mx-auto">
            {t('howItWorks.subtitle')}
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
          {stepKeys.map((step, index) => (
            <div key={step.titleKey} className="relative group">
              <div className="bg-gray-50 dark:bg-gray-800 rounded-2xl p-8 border border-gray-100 dark:border-gray-700 hover:shadow-lg transition-all hover:-translate-y-1 h-full">
                {/* Step number */}
                <div className="absolute -top-3 -left-1 w-8 h-8 bg-white dark:bg-gray-900 border-2 border-gray-200 dark:border-gray-700 rounded-full flex items-center justify-center text-sm font-bold text-gray-500 dark:text-gray-400 shadow-sm">
                  {index + 1}
                </div>

                <div className={`inline-flex items-center justify-center w-12 h-12 ${step.color} rounded-xl mb-5`}>
                  <step.icon className="w-6 h-6 text-white" />
                </div>

                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
                  {t(step.titleKey)}
                </h3>
                <p className="text-sm text-gray-500 dark:text-gray-400 leading-relaxed">
                  {t(step.descKey)}
                </p>
              </div>

              {/* Connecting arrow */}
              {index < stepKeys.length - 1 && (
                <div className="hidden lg:block absolute top-1/2 -right-5 transform -translate-y-1/2 text-gray-300">
                  <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                    <path d="M5 10H15M15 10L10 5M15 10L10 15" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
