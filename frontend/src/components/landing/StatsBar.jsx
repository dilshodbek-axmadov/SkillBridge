import { Briefcase, Compass, TrendingUp, Building2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';

const statKeys = [
  { icon: Briefcase,  value: '1,300+', labelKey: 'stats.activeJobs',    color: 'text-primary-600', bg: 'bg-primary-50' },
  { icon: Compass,    value: '25',     labelKey: 'stats.careerPaths',   color: 'text-purple-600',  bg: 'bg-purple-50' },
  { icon: TrendingUp, value: '87',     labelKey: 'stats.trendingSkills',color: 'text-success-600', bg: 'bg-green-50' },
  { icon: Building2,  value: '600+',   labelKey: 'stats.companies',     color: 'text-orange-600',  bg: 'bg-orange-50' },
];

export default function StatsBar() {
  const { t } = useTranslation();

  return (
    <section className="relative -mt-16 z-20 max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {statKeys.map((stat) => (
          <div
            key={stat.labelKey}
            className="bg-white rounded-2xl p-6 shadow-lg shadow-gray-200/50 border border-gray-100 text-center hover:shadow-xl transition-shadow"
          >
            <div className={`inline-flex items-center justify-center w-12 h-12 ${stat.bg} rounded-xl mb-3`}>
              <stat.icon className={`w-6 h-6 ${stat.color}`} />
            </div>
            <div className="text-3xl font-bold text-gray-900 mb-1">{stat.value}</div>
            <div className="text-sm text-gray-500 font-medium">{t(stat.labelKey)}</div>
          </div>
        ))}
      </div>
    </section>
  );
}
