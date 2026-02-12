import { Bot, BarChart3, Target, FileText } from 'lucide-react';
import { useTranslation } from 'react-i18next';

const featureKeys = [
  {
    icon: Bot,
    titleKey: 'features.aiMatching.title',
    descKey: 'features.aiMatching.desc',
    iconBg: 'bg-primary-50',
    iconColor: 'text-primary-600',
  },
  {
    icon: BarChart3,
    titleKey: 'features.marketData.title',
    descKey: 'features.marketData.desc',
    iconBg: 'bg-purple-50',
    iconColor: 'text-purple-600',
  },
  {
    icon: Target,
    titleKey: 'features.roadmap.title',
    descKey: 'features.roadmap.desc',
    iconBg: 'bg-green-50',
    iconColor: 'text-success-600',
  },
  {
    icon: FileText,
    titleKey: 'features.cv.title',
    descKey: 'features.cv.desc',
    iconBg: 'bg-orange-50',
    iconColor: 'text-orange-600',
  },
];

export default function Features() {
  const { t } = useTranslation();

  return (
    <section className="py-24 bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
            {t('features.title')}
          </h2>
          <p className="text-lg text-gray-500 max-w-2xl mx-auto">
            {t('features.subtitle')}
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {featureKeys.map((feature) => (
            <div
              key={feature.titleKey}
              className="bg-white rounded-2xl p-8 border border-gray-100 hover:shadow-lg transition-all hover:-translate-y-1 group"
            >
              <div className={`inline-flex items-center justify-center w-14 h-14 ${feature.iconBg} rounded-2xl mb-6 group-hover:scale-110 transition-transform`}>
                <feature.icon className={`w-7 h-7 ${feature.iconColor}`} />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">
                {t(feature.titleKey)}
              </h3>
              <p className="text-sm text-gray-500 leading-relaxed">
                {t(feature.descKey)}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
