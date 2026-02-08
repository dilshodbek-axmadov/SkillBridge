import { Link } from 'react-router-dom';
import { ArrowRight, Compass, Clock, Sparkles } from 'lucide-react';

export default function AssessmentCTA() {
  return (
    <section className="py-20 px-4 sm:px-6 lg:px-8 bg-white">
      <div className="max-w-6xl mx-auto">
        <div className="relative bg-gradient-to-br from-primary-600 via-primary-700 to-purple-600 rounded-3xl overflow-hidden">
          {/* Decorative blurs */}
          <div className="absolute top-0 right-0 w-80 h-80 bg-purple-400/20 rounded-full blur-3xl" />
          <div className="absolute bottom-0 left-0 w-64 h-64 bg-primary-300/20 rounded-full blur-3xl" />

          <div className="relative z-10 px-8 py-14 sm:px-12 sm:py-16 lg:px-16 lg:py-20">
            <div className="grid lg:grid-cols-2 gap-10 lg:gap-16 items-center">
              {/* Left - Text */}
              <div>
                <div className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-sm text-white text-sm font-medium px-4 py-2 rounded-full mb-6 border border-white/20">
                  <Compass className="w-4 h-4" />
                  Free Career Assessment
                </div>

                <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4 leading-tight">
                  Not sure which IT field is right for you?
                </h2>

                <p className="text-white/80 text-lg leading-relaxed mb-8">
                  You don&apos;t need to figure it out alone. Our AI-powered quiz analyzes your interests,
                  strengths, and goals to recommend the best career path for you — whether it&apos;s
                  frontend, backend, data science, or something else entirely.
                </p>

                <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
                  <Link
                    to="/assessment"
                    className="inline-flex items-center gap-2 px-8 py-4 text-base font-semibold text-primary-700 bg-white rounded-xl hover:bg-primary-50 no-underline transition-all shadow-lg shadow-primary-900/20 hover:shadow-xl"
                  >
                    Take the Quiz
                    <ArrowRight className="w-5 h-5" />
                  </Link>
                  <div className="flex items-center gap-2 text-white/70 text-sm">
                    <Clock className="w-4 h-4" />
                    Takes only 5 minutes
                  </div>
                </div>
              </div>

              {/* Right - Benefits cards */}
              <div className="space-y-4">
                <div className="bg-white/10 backdrop-blur-sm rounded-xl p-5 border border-white/10">
                  <div className="flex items-start gap-4">
                    <div className="w-10 h-10 bg-white/15 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5">
                      <span className="text-lg">🎯</span>
                    </div>
                    <div>
                      <h3 className="text-white font-semibold mb-1">Personalized Recommendations</h3>
                      <p className="text-white/70 text-sm leading-relaxed">
                        Get role suggestions matched to your unique interests and aptitudes, not generic advice.
                      </p>
                    </div>
                  </div>
                </div>

                <div className="bg-white/10 backdrop-blur-sm rounded-xl p-5 border border-white/10">
                  <div className="flex items-start gap-4">
                    <div className="w-10 h-10 bg-white/15 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5">
                      <span className="text-lg">📚</span>
                    </div>
                    <div>
                      <h3 className="text-white font-semibold mb-1">Course & Learning Path</h3>
                      <p className="text-white/70 text-sm leading-relaxed">
                        After the quiz, get a step-by-step learning roadmap with free resources to start right away.
                      </p>
                    </div>
                  </div>
                </div>

                <div className="bg-white/10 backdrop-blur-sm rounded-xl p-5 border border-white/10">
                  <div className="flex items-start gap-4">
                    <div className="w-10 h-10 bg-white/15 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5">
                      <Sparkles className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <h3 className="text-white font-semibold mb-1">Powered by AI</h3>
                      <p className="text-white/70 text-sm leading-relaxed">
                        Our AI analyzes real market data from Uzbekistan to give you relevant, up-to-date career advice.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
