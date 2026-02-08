import { Link } from 'react-router-dom';
import { Zap } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="bg-gray-900 text-gray-400">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand */}
          <div className="col-span-1 md:col-span-2">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-8 h-8 bg-gradient-to-br from-primary-600 to-purple-500 rounded-lg flex items-center justify-center">
                <Zap className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold text-white">
                Skill<span className="text-primary-400">Bridge</span>
              </span>
            </div>
            <p className="text-sm leading-relaxed max-w-md">
              AI-powered career guidance platform helping IT newcomers in Uzbekistan
              make data-driven career decisions with real market insights.
            </p>
          </div>

          {/* Links */}
          <div>
            <h4 className="text-sm font-semibold text-white uppercase tracking-wider mb-4">Platform</h4>
            <ul className="space-y-2 list-none p-0 m-0">
              <li><Link to="/dashboard" className="text-sm text-gray-400 hover:text-white no-underline transition-colors">Dashboard</Link></li>
              <li><Link to="/roadmap" className="text-sm text-gray-400 hover:text-white no-underline transition-colors">Roadmaps</Link></li>
              <li><Link to="/projects" className="text-sm text-gray-400 hover:text-white no-underline transition-colors">Projects</Link></li>
              <li><Link to="/cv" className="text-sm text-gray-400 hover:text-white no-underline transition-colors">CV Builder</Link></li>
            </ul>
          </div>

          <div>
            <h4 className="text-sm font-semibold text-white uppercase tracking-wider mb-4">Company</h4>
            <ul className="space-y-2 list-none p-0 m-0">
              <li><Link to="/about" className="text-sm text-gray-400 hover:text-white no-underline transition-colors">About</Link></li>
              <li><Link to="/contact" className="text-sm text-gray-400 hover:text-white no-underline transition-colors">Contact</Link></li>
              <li><Link to="/faq" className="text-sm text-gray-400 hover:text-white no-underline transition-colors">FAQ</Link></li>
            </ul>
          </div>
        </div>

        <div className="mt-10 pt-8 border-t border-gray-800 text-center">
          <p className="text-sm text-gray-500">
            &copy; {new Date().getFullYear()} SkillBridge. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
}
