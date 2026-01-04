'use client'

import React, { useState } from 'react'
import Link from 'next/link'
import { Menu, X, Search } from 'lucide-react'

export default function Navbar() {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <nav className="sticky top-0 z-50 bg-slate-900/80 backdrop-blur border-b border-slate-700">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">SP</span>
            </div>
            <span className="text-xl font-bold text-white hidden sm:inline">Stock Predictor</span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-8">
            <Link href="/" className="text-gray-300 hover:text-white transition">
              Home
            </Link>
            <Link href="/search" className="text-gray-300 hover:text-white transition">
              Search
            </Link>
            <Link href="/about" className="text-gray-300 hover:text-white transition">
              About
            </Link>
          </div>

          {/* Search Bar */}
          <div className="hidden lg:flex items-center gap-2 px-4 py-2 bg-slate-800 rounded-lg">
            <Search className="w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search stocks..."
              className="bg-transparent text-white placeholder-gray-500 focus:outline-none w-32"
            />
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="md:hidden text-gray-300 hover:text-white transition"
          >
            {isOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>

        {/* Mobile Navigation */}
        {isOpen && (
          <div className="md:hidden pb-4 border-t border-slate-700">
            <Link href="/" className="block px-4 py-2 text-gray-300 hover:text-white transition">
              Home
            </Link>
            <Link href="/search" className="block px-4 py-2 text-gray-300 hover:text-white transition">
              Search
            </Link>
            <Link href="/about" className="block px-4 py-2 text-gray-300 hover:text-white transition">
              About
            </Link>
          </div>
        )}
      </div>
    </nav>
  )
}
