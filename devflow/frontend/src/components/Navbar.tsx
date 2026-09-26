import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';

const navLinks = [
  { label: 'Product', href: '/#product' },
  { label: 'Workflow', href: '/#workflow' },
  { label: 'Features', href: '/#features' },
  { label: 'Architecture', href: '/architecture' },
];

export default function Navbar() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  const handleAnchor = (href: string) => {
    setMobileOpen(false);
    if (href.startsWith('/#')) {
      if (location.pathname !== '/') {
        navigate('/');
        setTimeout(() => {
          const id = href.replace('/#', '');
          document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
        }, 100);
      } else {
        const id = href.replace('/#', '');
        document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
      }
    } else {
      navigate(href);
    }
  };

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-white border-b border-[#D0D0D0]">
      <div className="max-w-7xl mx-auto px-6 h-12 flex items-center justify-between">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-3 no-underline">
          <div className="flex items-center gap-2">
            <div className="w-5 h-5 bg-[#0F62FE] flex items-center justify-center">
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                <rect x="1" y="1" width="4" height="4" fill="white" />
                <rect x="7" y="1" width="4" height="4" fill="white" opacity="0.6" />
                <rect x="1" y="7" width="4" height="4" fill="white" opacity="0.6" />
                <rect x="7" y="7" width="4" height="4" fill="white" />
              </svg>
            </div>
            <span className="text-[#161616] font-semibold text-sm tracking-tight">CodeLens</span>
          </div>
          <span className="hidden sm:block text-[10px] font-mono text-[#525252] uppercase tracking-widest border-l border-[#D0D0D0] pl-3">
            Developer Intelligence
          </span>
        </Link>

        {/* Desktop nav */}
        <nav className="hidden md:flex items-center gap-1">
          {navLinks.map((link) => (
            <button
              key={link.label}
              onClick={() => handleAnchor(link.href)}
              className={`px-3 py-1.5 text-sm font-medium transition-colors cursor-pointer border-none bg-transparent ${
                location.pathname === link.href
                  ? 'text-[#0F62FE]'
                  : 'text-[#525252] hover:text-[#161616]'
              }`}
            >
              {link.label}
            </button>
          ))}
        </nav>

        {/* CTA */}
        <div className="hidden md:flex items-center gap-3">
          <Link
            to="/analyzer"
            className="px-4 py-1.5 bg-[#0F62FE] text-white text-sm font-medium hover:bg-[#0353E9] transition-colors no-underline"
          >
            Open Analyzer
          </Link>
        </div>

        {/* Mobile hamburger */}
        <button
          className="md:hidden p-1.5 text-[#525252] hover:text-[#161616]"
          onClick={() => setMobileOpen(!mobileOpen)}
          aria-label="Toggle menu"
        >
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            {mobileOpen ? (
              <path d="M4 4L16 16M4 16L16 4" stroke="currentColor" strokeWidth="1.5" />
            ) : (
              <>
                <line x1="3" y1="6" x2="17" y2="6" stroke="currentColor" strokeWidth="1.5" />
                <line x1="3" y1="10" x2="17" y2="10" stroke="currentColor" strokeWidth="1.5" />
                <line x1="3" y1="14" x2="17" y2="14" stroke="currentColor" strokeWidth="1.5" />
              </>
            )}
          </svg>
        </button>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="md:hidden bg-white border-t border-[#D0D0D0] px-6 py-4 flex flex-col gap-2">
          {navLinks.map((link) => (
            <button
              key={link.label}
              onClick={() => handleAnchor(link.href)}
              className="text-left py-2 text-sm text-[#161616] border-none bg-transparent cursor-pointer"
            >
              {link.label}
            </button>
          ))}
          <Link
            to="/analyzer"
            className="mt-2 px-4 py-2 bg-[#0F62FE] text-white text-sm font-medium text-center no-underline"
            onClick={() => setMobileOpen(false)}
          >
            Open Analyzer
          </Link>
        </div>
      )}
    </header>
  );
}
