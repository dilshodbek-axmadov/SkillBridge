import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronLeft, ChevronRight, Loader2, Zap, Send } from 'lucide-react';
import api from '../services/api';

// Emoji map for option display — maps keywords in option text to emojis
const EMOJI_MAP = [
  [/logic|algorithm|problem.solving|backend|server/i, '🧩'],
  [/visual|design|frontend|ui|interface|css|style/i, '🎨'],
  [/data|analy|statistic|machine.learn|ai/i, '📊'],
  [/user.experience|ux|pm|product|manage/i, '🤝'],
  [/mobile|app|android|ios|phone/i, '📱'],
  [/secur|protect|hack|cyber/i, '🔒'],
  [/cloud|devops|infra|deploy|docker/i, '☁️'],
  [/game|unity|unreal|3d/i, '🎮'],
  [/communi|team|collaborat|people/i, '👥'],
  [/independ|alone|solo|focus/i, '🎯'],
  [/fast.paced|startup|agile|rapid/i, '⚡'],
  [/stable|steady|methodic|plan/i, '📋'],
  [/creat|innovat|new.idea|experiment/i, '💡'],
  [/learn|study|cours|tutorial|read/i, '📚'],
  [/build|project|hands.on|practic/i, '🛠️'],
  [/teach|mentor|help|explain/i, '🎓'],
  [/money|salary|earn|financ/i, '💰'],
  [/passion|love|enjoy|fun/i, '❤️'],
  [/impact|change|world|social/i, '🌍'],
  [/free|flex|remote|balance/i, '🏡'],
];

function getEmoji(text) {
  for (const [pattern, emoji] of EMOJI_MAP) {
    if (pattern.test(text)) return emoji;
  }
  return '✨';
}

export default function AssessmentPage() {
  const navigate = useNavigate();

  const [questions, setQuestions] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [responses, setResponses] = useState({});
  const [loadingQuestions, setLoadingQuestions] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [direction, setDirection] = useState('next'); // for animation

  // Fetch questions on mount
  useEffect(() => {
    const fetchQuestions = async () => {
      try {
        const { data } = await api.get('/career/questions/');
        if (data.questions && data.questions.length > 0) {
          setQuestions(data.questions);
        } else {
          setError('No assessment questions available. Please contact support.');
        }
      } catch (err) {
        if (err.response?.status === 401) {
          navigate('/login?redirect=/assessment', { replace: true });
          return;
        }
        setError('Failed to load questions. Please try again.');
      } finally {
        setLoadingQuestions(false);
      }
    };

    fetchQuestions();
  }, [navigate]);

  const totalQuestions = questions.length;
  const currentQuestion = questions[currentIndex];
  const progress = totalQuestions > 0 ? ((currentIndex + 1) / totalQuestions) * 100 : 0;
  const allAnswered = totalQuestions > 0 && Object.keys(responses).length === totalQuestions;
  const isLastQuestion = currentIndex === totalQuestions - 1;
  const currentAnswer = currentQuestion ? responses[currentQuestion.id] : undefined;

  const selectOption = useCallback((optionIndex) => {
    if (!currentQuestion) return;
    setResponses((prev) => ({
      ...prev,
      [currentQuestion.id]: optionIndex,
    }));
  }, [currentQuestion]);

  const goNext = useCallback(() => {
    if (currentIndex < totalQuestions - 1) {
      setDirection('next');
      setCurrentIndex((i) => i + 1);
    }
  }, [currentIndex, totalQuestions]);

  const goBack = useCallback(() => {
    if (currentIndex > 0) {
      setDirection('back');
      setCurrentIndex((i) => i - 1);
    }
  }, [currentIndex]);

  // Auto-advance after selecting an option (with short delay)
  useEffect(() => {
    if (currentAnswer !== undefined && !isLastQuestion) {
      const timer = setTimeout(() => goNext(), 400);
      return () => clearTimeout(timer);
    }
  }, [currentAnswer, isLastQuestion, goNext]);

  const handleSubmit = async () => {
    if (!allAnswered) return;

    setSubmitting(true);
    setError('');

    try {
      // Format responses: { "question_id": option_index }
      const formattedResponses = {};
      for (const [qId, optIndex] of Object.entries(responses)) {
        formattedResponses[String(qId)] = optIndex;
      }

      await api.post('/career/assessment/', {
        responses: formattedResponses,
      });

      navigate('/recommendations');
    } catch (err) {
      const msg =
        err.response?.data?.detail ||
        err.response?.data?.error ||
        'Failed to submit assessment. Please try again.';
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  // Keyboard navigation
  useEffect(() => {
    const handler = (e) => {
      if (e.key === 'ArrowRight' || e.key === 'Enter') {
        if (isLastQuestion && allAnswered) handleSubmit();
        else if (currentAnswer !== undefined) goNext();
      }
      if (e.key === 'ArrowLeft') goBack();
      if (['1', '2', '3', '4'].includes(e.key)) {
        const idx = parseInt(e.key) - 1;
        if (currentQuestion && currentQuestion.options && idx < currentQuestion.options.length) {
          selectOption(idx);
        }
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  });

  // Loading state
  if (loadingQuestions) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-10 h-10 text-primary-600 animate-spin mx-auto mb-4" />
          <p className="text-gray-500 dark:text-gray-400 text-sm">Loading your career assessment...</p>
        </div>
      </div>
    );
  }

  // Error state (no questions)
  if (error && questions.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
        <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-800 p-8 max-w-md text-center">
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-6 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 transition-colors cursor-pointer border-none"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 dark:border-gray-800 px-4 sm:px-6 lg:px-8 py-4">
        <div className="max-w-3xl mx-auto">
          {/* Top row */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gradient-to-br from-primary-600 to-purple-500 rounded-lg flex items-center justify-center">
                <Zap className="w-4 h-4 text-white" />
              </div>
              <span className="text-sm font-semibold text-gray-900 dark:text-gray-100">Career Assessment</span>
            </div>
            <span className="text-sm text-gray-500 dark:text-gray-400 dark:text-gray-500">
              Question {currentIndex + 1} of {totalQuestions}
            </span>
          </div>

          {/* Progress bar */}
          <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-primary-500 to-primary-600 rounded-full transition-all duration-500 ease-out"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      </header>

      {/* Question area */}
      <main className="flex-1 flex items-center justify-center px-4 sm:px-6 py-8 sm:py-12">
        <div className="w-full max-w-2xl">
          {/* Question text */}
          <div
            key={currentQuestion.id}
            className={`transition-all duration-300 ease-out ${
              direction === 'next'
                ? 'animate-[slideInRight_0.3s_ease-out]'
                : 'animate-[slideInLeft_0.3s_ease-out]'
            }`}
          >
            <p className="text-xs font-semibold uppercase tracking-wide text-primary-600 mb-3">
              {currentQuestion.category}
            </p>
            <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-gray-100 mb-8 leading-snug">
              {currentQuestion.question_text}
            </h2>

            {/* Options grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
              {currentQuestion.options.map((option, idx) => {
                const isSelected = currentAnswer === idx;
                const emoji = getEmoji(option.text);

                return (
                  <button
                    key={idx}
                    onClick={() => selectOption(idx)}
                    className={`group relative text-left p-5 rounded-xl border-2 transition-all duration-200 cursor-pointer bg-white ${
                      isSelected
                        ? 'border-primary-500 bg-primary-50 shadow-md shadow-primary-100'
                        : 'border-gray-200 hover:border-primary-300 hover:shadow-sm'
                    }`}
                  >
                    {/* Selection indicator */}
                    <div
                      className={`absolute top-3 right-3 w-5 h-5 rounded-full border-2 flex items-center justify-center transition-colors ${
                        isSelected
                          ? 'border-primary-500 bg-primary-500'
                          : 'border-gray-300 group-hover:border-primary-300'
                      }`}
                    >
                      {isSelected && (
                        <svg className="w-3 h-3 text-white" viewBox="0 0 12 12" fill="none">
                          <path d="M2 6l3 3 5-5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                      )}
                    </div>

                    <span className="text-2xl mb-2 block">{emoji}</span>
                    <span
                      className={`text-sm font-medium leading-snug block pr-6 ${
                        isSelected ? 'text-primary-700' : 'text-gray-700 group-hover:text-gray-900'
                      }`}
                    >
                      {option.text}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Error */}
          {error && (
            <div className="mt-6 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 rounded-lg text-sm text-red-600 text-center">
              {error}
            </div>
          )}
        </div>
      </main>

      {/* Navigation */}
      <footer className="bg-white border-t border-gray-200 dark:border-gray-800 px-4 sm:px-6 lg:px-8 py-4">
        <div className="max-w-3xl mx-auto flex items-center justify-between">
          <button
            onClick={goBack}
            disabled={currentIndex === 0}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-medium transition-colors border-none cursor-pointer ${
              currentIndex === 0
                ? 'text-gray-300 bg-transparent cursor-not-allowed'
                : 'text-gray-600 bg-gray-100 hover:bg-gray-200'
            }`}
          >
            <ChevronLeft className="w-4 h-4" />
            Back
          </button>

          {/* Dots indicator */}
          <div className="hidden sm:flex items-center gap-1.5">
            {questions.map((q, idx) => (
              <button
                key={q.id}
                onClick={() => { setDirection(idx > currentIndex ? 'next' : 'back'); setCurrentIndex(idx); }}
                className={`w-2 h-2 rounded-full transition-all border-none cursor-pointer p-0 ${
                  idx === currentIndex
                    ? 'w-6 bg-primary-600'
                    : responses[q.id] !== undefined
                    ? 'bg-primary-300'
                    : 'bg-gray-300'
                }`}
              />
            ))}
          </div>

          {isLastQuestion ? (
            <button
              onClick={handleSubmit}
              disabled={!allAnswered || submitting}
              className={`flex items-center gap-2 px-6 py-2.5 rounded-lg text-sm font-semibold transition-colors border-none cursor-pointer ${
                allAnswered && !submitting
                  ? 'bg-primary-600 text-white hover:bg-primary-700'
                  : 'bg-gray-200 text-gray-400 cursor-not-allowed'
              }`}
            >
              {submitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Submitting...
                </>
              ) : (
                <>
                  Get Results
                  <Send className="w-4 h-4" />
                </>
              )}
            </button>
          ) : (
            <button
              onClick={goNext}
              disabled={currentAnswer === undefined}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-medium transition-colors border-none cursor-pointer ${
                currentAnswer !== undefined
                  ? 'bg-primary-600 text-white hover:bg-primary-700'
                  : 'bg-gray-200 text-gray-400 cursor-not-allowed'
              }`}
            >
              Next
              <ChevronRight className="w-4 h-4" />
            </button>
          )}
        </div>
      </footer>

      {/* CSS animations */}
      <style>{`
        @keyframes slideInRight {
          from { opacity: 0; transform: translateX(30px); }
          to { opacity: 1; transform: translateX(0); }
        }
        @keyframes slideInLeft {
          from { opacity: 0; transform: translateX(-30px); }
          to { opacity: 1; transform: translateX(0); }
        }
      `}</style>
    </div>
  );
}
