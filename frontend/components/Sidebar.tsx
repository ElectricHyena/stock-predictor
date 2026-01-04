'use client'

import React from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  Search,
  LayoutDashboard,
  Bell,
  Eye,
  TrendingUp,
  LineChart,
  Settings,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'

interface SidebarProps {
  isOpen: boolean
  onToggle: () => void
}

interface NavItem {
  href: string
  label: string
  icon: React.ReactNode
}

const navItems: NavItem[] = [
  {
    href: '/search',
    label: 'Search Stocks',
    icon: <Search className="w-5 h-5" />,
  },
  {
    href: '/watchlist',
    label: 'Watchlist',
    icon: <Eye className="w-5 h-5" />,
  },
  {
    href: '/alerts',
    label: 'Alerts',
    icon: <Bell className="w-5 h-5" />,
  },
  {
    href: '/backtest',
    label: 'Backtest',
    icon: <LineChart className="w-5 h-5" />,
  },
]

export default function Sidebar({ isOpen, onToggle }: SidebarProps) {
  const pathname = usePathname()

  return (
    <aside
      className={`fixed left-0 top-16 h-[calc(100vh-4rem)] bg-slate-900 border-r border-slate-700 transition-all duration-300 z-40 ${
        isOpen ? 'w-64' : 'w-16'
      }`}
    >
      {/* Toggle Button */}
      <button
        onClick={onToggle}
        className="absolute -right-3 top-6 bg-slate-800 border border-slate-700 rounded-full p-1.5 hover:bg-slate-700 transition-colors"
        aria-label={isOpen ? 'Collapse sidebar' : 'Expand sidebar'}
      >
        {isOpen ? (
          <ChevronLeft className="w-4 h-4 text-gray-400" />
        ) : (
          <ChevronRight className="w-4 h-4 text-gray-400" />
        )}
      </button>

      {/* Navigation Links */}
      <nav className="p-4 space-y-2">
        {navItems.map((item) => {
          const isActive = pathname === item.href || pathname?.startsWith(`${item.href}/`)

          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors ${
                isActive
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-400 hover:bg-slate-800 hover:text-white'
              }`}
              title={!isOpen ? item.label : undefined}
            >
              <span className="flex-shrink-0">{item.icon}</span>
              {isOpen && (
                <span className="font-medium whitespace-nowrap">{item.label}</span>
              )}
            </Link>
          )
        })}
      </nav>

      {/* Bottom Section */}
      <div className="absolute bottom-4 left-0 right-0 px-4">
        <Link
          href="/settings"
          className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors text-gray-400 hover:bg-slate-800 hover:text-white ${
            pathname === '/settings' ? 'bg-blue-600 text-white' : ''
          }`}
          title={!isOpen ? 'Settings' : undefined}
        >
          <Settings className="w-5 h-5 flex-shrink-0" />
          {isOpen && <span className="font-medium">Settings</span>}
        </Link>
      </div>
    </aside>
  )
}
