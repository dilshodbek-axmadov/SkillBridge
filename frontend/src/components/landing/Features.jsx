import { Bot, BarChart3, Target, FileText } from 'lucide-react';

const features = [
  {
    icon: Bot,
    title: 'AI-Powered Career Matching',
    description:
      'Take our 5-minute assessment and get personalized role recommendations based on your skills and interests.',
    color: 'from-primary-500 to-primary-600',
    iconBg: 'bg-primary-50',
    iconColor: 'text-primary-600',
  },
  {
    icon: BarChart3,
    title: 'Real-Time Market Data',
    description:
      'Access live job openings, salary insights, and trending skills across the Uzbekistan IT market.',
    color: 'from-purple-500 to-purple-600',
    iconBg: 'bg-purple-50',
    iconColor: 'text-purple-600',
  },
  {
    icon: Target,
    title: 'Personalized Learning Roadmap',
    description:
      'Get AI-generated skill gap analysis and step-by-step learning plans tailored to your career goals.',
    color: 'from-success-500 to-success-600',
    iconBg: 'bg-green-50',
    iconColor: 'text-success-600',
  },
  {
    icon: FileText,
    title: 'Professional CV Generation',
    description:
      'Build polished CVs with multiple templates, auto-populated from your profile and achievements.',
    color: 'from-orange-500 to-orange-600',
    iconBg: 'bg-orange-50',
    iconColor: 'text-orange-600',
  },
];

export default function Features() {
  return (
    <section className="py-24 bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
            Everything You Need to Launch Your IT Career
          </h2>
          <p className="text-lg text-gray-500 max-w-2xl mx-auto">
            Our platform combines AI intelligence with real market data to guide you
            from beginner to professional.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {features.map((feature) => (
            <div
              key={feature.title}
              className="bg-white rounded-2xl p-8 border border-gray-100 hover:shadow-lg transition-all hover:-translate-y-1 group"
            >
              <div className={`inline-flex items-center justify-center w-14 h-14 ${feature.iconBg} rounded-2xl mb-6 group-hover:scale-110 transition-transform`}>
                <feature.icon className={`w-7 h-7 ${feature.iconColor}`} />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">
                {feature.title}
              </h3>
              <p className="text-sm text-gray-500 leading-relaxed">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
