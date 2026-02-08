import { ClipboardCheck, Compass, Search, Route, LineChart, FileText } from 'lucide-react';

const steps = [
  {
    icon: ClipboardCheck,
    title: 'Take Assessment or Upload CV',
    description: 'Complete a quick 5-minute career assessment or upload your existing CV.',
    color: 'bg-primary-600',
  },
  {
    icon: Compass,
    title: 'Get Career Recommendations',
    description: 'Receive AI-powered career path suggestions based on your profile.',
    color: 'bg-purple-600',
  },
  {
    icon: Search,
    title: 'Analyze Your Skill Gaps',
    description: 'See which skills you need to learn for your target role.',
    color: 'bg-success-600',
  },
  {
    icon: Route,
    title: 'Follow Personalized Roadmap',
    description: 'Get a step-by-step learning plan with curated resources.',
    color: 'bg-orange-600',
  },
  {
    icon: LineChart,
    title: 'Track Your Progress',
    description: 'Monitor your learning journey and skill development over time.',
    color: 'bg-pink-600',
  },
  {
    icon: FileText,
    title: 'Create Your CV',
    description: 'Generate a professional CV showcasing your new skills and projects.',
    color: 'bg-cyan-600',
  },
];

export default function HowItWorks() {
  return (
    <section className="py-24 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
            How It Works
          </h2>
          <p className="text-lg text-gray-500 max-w-2xl mx-auto">
            From assessment to career launch in six simple steps
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
          {steps.map((step, index) => (
            <div key={step.title} className="relative group">
              <div className="bg-gray-50 rounded-2xl p-8 border border-gray-100 hover:shadow-lg transition-all hover:-translate-y-1 h-full">
                {/* Step number */}
                <div className="absolute -top-3 -left-1 w-8 h-8 bg-white border-2 border-gray-200 rounded-full flex items-center justify-center text-sm font-bold text-gray-500 shadow-sm">
                  {index + 1}
                </div>

                <div className={`inline-flex items-center justify-center w-12 h-12 ${step.color} rounded-xl mb-5`}>
                  <step.icon className="w-6 h-6 text-white" />
                </div>

                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {step.title}
                </h3>
                <p className="text-sm text-gray-500 leading-relaxed">
                  {step.description}
                </p>
              </div>

              {/* Connecting arrow (hidden on last item per row) */}
              {index < steps.length - 1 && (
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
