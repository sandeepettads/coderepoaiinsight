import React, { useState, useRef, useEffect } from 'react';
import { User, Settings, LogIn, LogOut, ChevronDown } from 'lucide-react';

const Header: React.FC = () => {
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [isSignedIn, setIsSignedIn] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const toggleDropdown = () => {
    setIsDropdownOpen(!isDropdownOpen);
  };

  const handleSignIn = () => {
    setIsSignedIn(true);
    setIsDropdownOpen(false);
  };

  const handleSignOut = () => {
    setIsSignedIn(false);
    setIsDropdownOpen(false);
  };

  const handleSettings = () => {
    setIsDropdownOpen(false);
    // Settings functionality can be implemented here
    console.log('Settings clicked');
  };

  return (
    <header className="h-12 bg-gray-900 border-b border-gray-700 flex items-center justify-between px-4">
      {/* Left side - App Name */}
      <div className="flex items-center">
        <h1 className="text-lg font-semibold text-white">
          RepoInsight AI
        </h1>
      </div>

      {/* Right side - User Dropdown */}
      <div className="relative" ref={dropdownRef}>
        <button
          onClick={toggleDropdown}
          className="flex items-center gap-2 px-3 py-1.5 text-gray-300 hover:text-white hover:bg-gray-800 rounded-md transition-colors"
        >
          <User className="w-4 h-4" />
          <span className="text-sm">
            {isSignedIn ? 'User' : 'Guest'}
          </span>
          <ChevronDown className={`w-4 h-4 transition-transform ${isDropdownOpen ? 'rotate-180' : ''}`} />
        </button>

        {/* Dropdown Menu */}
        {isDropdownOpen && (
          <div className="absolute right-0 mt-1 w-48 bg-gray-800 border border-gray-700 rounded-md shadow-lg z-50">
            <div className="py-1">
              {!isSignedIn ? (
                <button
                  onClick={handleSignIn}
                  className="flex items-center gap-2 w-full px-4 py-2 text-sm text-gray-300 hover:text-white hover:bg-gray-700 transition-colors"
                >
                  <LogIn className="w-4 h-4" />
                  Sign In
                </button>
              ) : (
                <button
                  onClick={handleSignOut}
                  className="flex items-center gap-2 w-full px-4 py-2 text-sm text-gray-300 hover:text-white hover:bg-gray-700 transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                  Sign Out
                </button>
              )}
              
              <div className="border-t border-gray-700 my-1"></div>
              
              <button
                onClick={handleSettings}
                className="flex items-center gap-2 w-full px-4 py-2 text-sm text-gray-300 hover:text-white hover:bg-gray-700 transition-colors"
              >
                <Settings className="w-4 h-4" />
                Settings
              </button>
            </div>
          </div>
        )}
      </div>
    </header>
  );
};

export default Header;