'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';
import { useRouter } from 'next/navigation';
import {
  Store,
  TrendingUp,
  Star,
  Download,
  Search,
  Filter,
  Award,
  CheckCircle,
  BarChart3,
  Target,
  Zap,
  Crown,
  Users,
  Clock,
  DollarSign
} from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Strategy {
  id: string;
  name: string;
  description: string;
  author: string;
  category: string;
  price: number;
  isPremium: boolean;
  isPopular: boolean;
  rating: number;
  totalRatings: number;
  totalDownloads: number;
  winRate: number;
  avgReturn: number;
  sharpeRatio: number;
  maxDrawdown: number;
  backtestPeriod: string;
  tags: string[];
  difficulty: 'Beginner' | 'Intermediate' | 'Advanced';
  timeframe: string;
  markets: string[];
}

const MARKETPLACE_STRATEGIES: Strategy[] = [
  {
    id: 'ma-crossover-pro',
    name: 'MA Crossover Pro',
    description: 'Advanced moving average crossover strategy with dynamic position sizing and trend filters. Optimized for trending markets.',
    author: 'TradingBot Team',
    category: 'Trend Following',
    price: 0,
    isPremium: false,
    isPopular: true,
    rating: 4.5,
    totalRatings: 342,
    totalDownloads: 1250,
    winRate: 62.5,
    avgReturn: 8.3,
    sharpeRatio: 1.8,
    maxDrawdown: 12.5,
    backtestPeriod: '2 years',
    tags: ['trending', 'indicators', 'beginner-friendly'],
    difficulty: 'Beginner',
    timeframe: '15m - 4h',
    markets: ['BTC/USDT', 'ETH/USDT', 'All Pairs']
  },
  {
    id: 'grid-master',
    name: 'Grid Trading Master',
    description: 'Professional grid trading system with auto-adjustment for volatility. Perfect for ranging markets and stable coins.',
    author: 'GridPro',
    category: 'Range Trading',
    price: 49,
    isPremium: true,
    isPopular: true,
    rating: 4.8,
    totalRatings: 189,
    totalDownloads: 456,
    winRate: 75.2,
    avgReturn: 12.7,
    sharpeRatio: 2.1,
    maxDrawdown: 8.3,
    backtestPeriod: '18 months',
    tags: ['grid', 'ranging', 'stable'],
    difficulty: 'Intermediate',
    timeframe: '5m - 1h',
    markets: ['All Pairs']
  },
  {
    id: 'ai-momentum',
    name: 'AI Momentum Trader',
    description: 'Machine learning powered momentum strategy using neural networks to predict price movements with 70%+ accuracy.',
    author: 'AlphaQuant',
    category: 'AI/ML',
    price: 199,
    isPremium: true,
    isPopular: true,
    rating: 4.9,
    totalRatings: 87,
    totalDownloads: 234,
    winRate: 71.3,
    avgReturn: 18.9,
    sharpeRatio: 2.5,
    maxDrawdown: 15.2,
    backtestPeriod: '3 years',
    tags: ['ai', 'ml', 'momentum', 'advanced'],
    difficulty: 'Advanced',
    timeframe: '1h - 4h',
    markets: ['BTC/USDT', 'ETH/USDT', 'Major Pairs']
  },
  {
    id: 'scalper-elite',
    name: 'Scalper Elite',
    description: 'High-frequency scalping strategy for quick profits. Executes 50-100 trades per day with tight stop losses.',
    author: 'ScalpMaster',
    category: 'Scalping',
    price: 99,
    isPremium: true,
    isPopular: false,
    rating: 4.3,
    totalRatings: 156,
    totalDownloads: 389,
    winRate: 58.7,
    avgReturn: 6.2,
    sharpeRatio: 1.4,
    maxDrawdown: 18.9,
    backtestPeriod: '1 year',
    tags: ['scalping', 'high-frequency', 'aggressive'],
    difficulty: 'Advanced',
    timeframe: '1m - 5m',
    markets: ['BTC/USDT', 'ETH/USDT']
  },
  {
    id: 'breakout-hunter',
    name: 'Breakout Hunter',
    description: 'Identifies and trades breakouts from consolidation patterns. Uses volume and volatility filters.',
    author: 'TradingBot Team',
    category: 'Breakout',
    price: 0,
    isPremium: false,
    isPopular: true,
    rating: 4.4,
    totalRatings: 278,
    totalDownloads: 892,
    winRate: 64.1,
    avgReturn: 9.8,
    sharpeRatio: 1.7,
    maxDrawdown: 14.2,
    backtestPeriod: '2 years',
    tags: ['breakout', 'patterns', 'intermediate'],
    difficulty: 'Intermediate',
    timeframe: '15m - 1h',
    markets: ['All Pairs']
  },
  {
    id: 'dca-optimizer',
    name: 'DCA Optimizer',
    description: 'Smart dollar-cost averaging with dynamic entry timing. Optimizes entry points for long-term accumulation.',
    author: 'HODL Pro',
    category: 'DCA',
    price: 29,
    isPremium: true,
    isPopular: false,
    rating: 4.6,
    totalRatings: 124,
    totalDownloads: 567,
    winRate: 68.9,
    avgReturn: 15.3,
    sharpeRatio: 1.9,
    maxDrawdown: 22.1,
    backtestPeriod: '4 years',
    tags: ['dca', 'accumulation', 'long-term'],
    difficulty: 'Beginner',
    timeframe: '1d - 1w',
    markets: ['BTC/USDT', 'ETH/USDT', 'Blue Chips']
  }
];

const CATEGORIES = ['All', 'Trend Following', 'Range Trading', 'AI/ML', 'Scalping', 'Breakout', 'DCA'];
const SORT_OPTIONS = [
  { value: 'popular', label: 'Most Popular' },
  { value: 'rating', label: 'Highest Rated' },
  { value: 'downloads', label: 'Most Downloaded' },
  { value: 'performance', label: 'Best Performance' }
];

export default function MarketplacePage() {
  const router = useRouter();
  const [strategies, setStrategies] = useState<Strategy[]>(MARKETPLACE_STRATEGIES);
  const [filteredStrategies, setFilteredStrategies] = useState<Strategy[]>(MARKETPLACE_STRATEGIES);
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState('popular');
  const [selectedStrategy, setSelectedStrategy] = useState<Strategy | null>(null);
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    filterAndSortStrategies();
  }, [selectedCategory, searchQuery, sortBy]);

  const filterAndSortStrategies = () => {
    let filtered = strategies;

    // Filter by category
    if (selectedCategory !== 'All') {
      filtered = filtered.filter(s => s.category === selectedCategory);
    }

    // Filter by search
    if (searchQuery.trim()) {
      filtered = filtered.filter(s =>
        s.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        s.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
        s.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
      );
    }

    // Sort
    filtered = [...filtered].sort((a, b) => {
      switch (sortBy) {
        case 'popular':
          return b.totalDownloads - a.totalDownloads;
        case 'rating':
          return b.rating - a.rating;
        case 'downloads':
          return b.totalDownloads - a.totalDownloads;
        case 'performance':
          return b.avgReturn - a.avgReturn;
        default:
          return 0;
      }
    });

    setFilteredStrategies(filtered);
  };

  const openStrategyDetails = (strategy: Strategy) => {
    setSelectedStrategy(strategy);
    setShowModal(true);
  };

  const deployStrategy = (strategy: Strategy) => {
    if (strategy.isPremium && strategy.price > 0) {
      alert(`💳 Purchase "${strategy.name}" for $${strategy.price} to deploy it to your bots.`);
    } else {
      alert(`✅ Strategy "${strategy.name}" deployed! Configure it in your bot settings.`);
    }
    setShowModal(false);
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'Beginner':
        return 'text-green-400 bg-green-500/20';
      case 'Intermediate':
        return 'text-yellow-400 bg-yellow-500/20';
      case 'Advanced':
        return 'text-red-400 bg-red-500/20';
      default:
        return 'text-gray-400 bg-gray-500/20';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <Store className="w-8 h-8 text-purple-400" />
            <h1 className="text-3xl font-bold text-white">Strategy Marketplace</h1>
          </div>
          <p className="text-gray-300">
            Browse and deploy professional trading strategies to your bots
          </p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-4 border border-white/10">
            <div className="flex items-center gap-2 text-gray-400 text-sm mb-1">
              <Store className="w-4 h-4" />
              <span>Total Strategies</span>
            </div>
            <div className="text-2xl font-bold text-white">{strategies.length}</div>
          </div>
          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-4 border border-white/10">
            <div className="flex items-center gap-2 text-gray-400 text-sm mb-1">
              <Download className="w-4 h-4" />
              <span>Total Downloads</span>
            </div>
            <div className="text-2xl font-bold text-purple-400">
              {strategies.reduce((sum, s) => sum + s.totalDownloads, 0).toLocaleString()}
            </div>
          </div>
          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-4 border border-white/10">
            <div className="flex items-center gap-2 text-gray-400 text-sm mb-1">
              <Star className="w-4 h-4" />
              <span>Avg Rating</span>
            </div>
            <div className="text-2xl font-bold text-yellow-400">
              {(strategies.reduce((sum, s) => sum + s.rating, 0) / strategies.length).toFixed(1)}★
            </div>
          </div>
          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-4 border border-white/10">
            <div className="flex items-center gap-2 text-gray-400 text-sm mb-1">
              <TrendingUp className="w-4 h-4" />
              <span>Free Strategies</span>
            </div>
            <div className="text-2xl font-bold text-green-400">
              {strategies.filter(s => !s.isPremium).length}
            </div>
          </div>
        </div>

        {/* Controls */}
        <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 mb-6 border border-white/10">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Search */}
            <div className="relative md:col-span-2">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="Search strategies, tags, or keywords..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>

            {/* Sort */}
            <div className="flex items-center gap-2">
              <Filter className="w-5 h-5 text-gray-400 flex-shrink-0" />
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="flex-1 px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                {SORT_OPTIONS.map(option => (
                  <option key={option.value} value={option.value} className="bg-gray-800">
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Categories */}
          <div className="flex gap-2 mt-4 overflow-x-auto pb-2">
            {CATEGORIES.map(category => (
              <button
                key={category}
                onClick={() => setSelectedCategory(category)}
                className={`px-4 py-2 rounded-lg text-sm font-semibold whitespace-nowrap transition ${
                  selectedCategory === category
                    ? 'bg-purple-500 text-white'
                    : 'bg-white/10 text-gray-400 hover:bg-white/20'
                }`}
              >
                {category}
              </button>
            ))}
          </div>
        </div>

        {/* Strategy Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredStrategies.map(strategy => (
            <div
              key={strategy.id}
              className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/10 hover:border-purple-500/50 transition cursor-pointer"
              onClick={() => openStrategyDetails(strategy)}
            >
              {/* Header */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <h3 className="text-lg font-bold text-white">{strategy.name}</h3>
                    {strategy.isPopular && (
                      <Zap className="w-4 h-4 text-yellow-400 fill-yellow-400" />
                    )}
                  </div>
                  <p className="text-gray-400 text-xs mb-2">by {strategy.author}</p>
                </div>
                {strategy.isPremium ? (
                  <div className="px-3 py-1 bg-gradient-to-r from-yellow-500 to-orange-500 rounded-lg flex items-center gap-1">
                    <Crown className="w-4 h-4 text-white" />
                    <span className="text-white font-bold text-sm">${strategy.price}</span>
                  </div>
                ) : (
                  <div className="px-3 py-1 bg-green-500/20 text-green-400 rounded-lg font-semibold text-sm">
                    FREE
                  </div>
                )}
              </div>

              {/* Description */}
              <p className="text-gray-300 text-sm mb-4 line-clamp-2">
                {strategy.description}
              </p>

              {/* Metrics */}
              <div className="grid grid-cols-2 gap-3 mb-4">
                <div className="bg-white/5 rounded-lg p-2">
                  <div className="text-gray-400 text-xs mb-1">Win Rate</div>
                  <div className="text-green-400 font-bold">{strategy.winRate}%</div>
                </div>
                <div className="bg-white/5 rounded-lg p-2">
                  <div className="text-gray-400 text-xs mb-1">Avg Return</div>
                  <div className="text-purple-400 font-bold">+{strategy.avgReturn}%</div>
                </div>
                <div className="bg-white/5 rounded-lg p-2">
                  <div className="text-gray-400 text-xs mb-1">Sharpe</div>
                  <div className="text-blue-400 font-bold">{strategy.sharpeRatio}</div>
                </div>
                <div className="bg-white/5 rounded-lg p-2">
                  <div className="text-gray-400 text-xs mb-1">Max DD</div>
                  <div className="text-red-400 font-bold">{strategy.maxDrawdown}%</div>
                </div>
              </div>

              {/* Footer */}
              <div className="flex items-center justify-between pt-4 border-t border-white/10">
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-1 text-yellow-400">
                    <Star className="w-4 h-4 fill-yellow-400" />
                    <span className="text-sm font-semibold">{strategy.rating}</span>
                    <span className="text-gray-400 text-xs">({strategy.totalRatings})</span>
                  </div>
                  <div className="flex items-center gap-1 text-gray-400 text-xs">
                    <Download className="w-3 h-3" />
                    <span>{strategy.totalDownloads}</span>
                  </div>
                </div>
                <div className={`px-2 py-1 rounded text-xs font-semibold ${getDifficultyColor(strategy.difficulty)}`}>
                  {strategy.difficulty}
                </div>
              </div>
            </div>
          ))}
        </div>

        {filteredStrategies.length === 0 && (
          <div className="text-center py-12 text-gray-400">
            <Search className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>No strategies found matching your criteria</p>
          </div>
        )}

        {/* Strategy Details Modal */}
        {showModal && selectedStrategy && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <div className="bg-gradient-to-br from-gray-900 to-purple-900 rounded-2xl p-8 max-w-3xl w-full max-h-[90vh] overflow-y-auto border border-white/20">
              {/* Header */}
              <div className="flex items-start justify-between mb-6">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h2 className="text-3xl font-bold text-white">{selectedStrategy.name}</h2>
                    {selectedStrategy.isPopular && (
                      <div className="px-2 py-1 bg-yellow-500/20 text-yellow-400 rounded-lg text-xs font-semibold flex items-center gap-1">
                        <Zap className="w-3 h-3" />
                        Popular
                      </div>
                    )}
                  </div>
                  <p className="text-gray-400">by {selectedStrategy.author} • {selectedStrategy.category}</p>
                </div>
                <button
                  onClick={() => setShowModal(false)}
                  className="text-gray-400 hover:text-white text-2xl"
                >
                  ✕
                </button>
              </div>

              {/* Description */}
              <p className="text-gray-300 mb-6">{selectedStrategy.description}</p>

              {/* Performance Metrics */}
              <div className="bg-white/10 rounded-xl p-6 mb-6 border border-white/10">
                <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
                  <BarChart3 className="w-5 h-5 text-purple-400" />
                  Backtest Performance ({selectedStrategy.backtestPeriod})
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <div className="text-gray-400 text-sm mb-1">Win Rate</div>
                    <div className="text-2xl font-bold text-green-400">{selectedStrategy.winRate}%</div>
                  </div>
                  <div>
                    <div className="text-gray-400 text-sm mb-1">Avg Return</div>
                    <div className="text-2xl font-bold text-purple-400">+{selectedStrategy.avgReturn}%</div>
                  </div>
                  <div>
                    <div className="text-gray-400 text-sm mb-1">Sharpe Ratio</div>
                    <div className="text-2xl font-bold text-blue-400">{selectedStrategy.sharpeRatio}</div>
                  </div>
                  <div>
                    <div className="text-gray-400 text-sm mb-1">Max Drawdown</div>
                    <div className="text-2xl font-bold text-red-400">{selectedStrategy.maxDrawdown}%</div>
                  </div>
                </div>
              </div>

              {/* Details */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                <div className="bg-white/5 rounded-lg p-4">
                  <div className="flex items-center gap-2 text-gray-400 mb-2">
                    <Clock className="w-4 h-4" />
                    <span className="text-sm font-semibold">Timeframe</span>
                  </div>
                  <div className="text-white font-semibold">{selectedStrategy.timeframe}</div>
                </div>
                <div className="bg-white/5 rounded-lg p-4">
                  <div className="flex items-center gap-2 text-gray-400 mb-2">
                    <Target className="w-4 h-4" />
                    <span className="text-sm font-semibold">Difficulty</span>
                  </div>
                  <div className={`font-semibold inline-block px-2 py-1 rounded ${getDifficultyColor(selectedStrategy.difficulty)}`}>
                    {selectedStrategy.difficulty}
                  </div>
                </div>
              </div>

              {/* Markets */}
              <div className="mb-6">
                <h4 className="text-white font-semibold mb-2">Supported Markets</h4>
                <div className="flex flex-wrap gap-2">
                  {selectedStrategy.markets.map(market => (
                    <div key={market} className="px-3 py-1 bg-white/10 rounded-lg text-gray-300 text-sm">
                      {market}
                    </div>
                  ))}
                </div>
              </div>

              {/* Tags */}
              <div className="mb-6">
                <h4 className="text-white font-semibold mb-2">Tags</h4>
                <div className="flex flex-wrap gap-2">
                  {selectedStrategy.tags.map(tag => (
                    <div key={tag} className="px-3 py-1 bg-purple-500/20 text-purple-300 rounded-lg text-sm">
                      #{tag}
                    </div>
                  ))}
                </div>
              </div>

              {/* Reviews */}
              <div className="flex items-center gap-4 mb-6 pb-6 border-b border-white/10">
                <div className="flex items-center gap-2">
                  <Star className="w-6 h-6 text-yellow-400 fill-yellow-400" />
                  <span className="text-2xl font-bold text-white">{selectedStrategy.rating}</span>
                  <span className="text-gray-400">({selectedStrategy.totalRatings} ratings)</span>
                </div>
                <div className="flex items-center gap-2 text-gray-400">
                  <Download className="w-5 h-5" />
                  <span>{selectedStrategy.totalDownloads.toLocaleString()} downloads</span>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-4">
                <button
                  onClick={() => setShowModal(false)}
                  className="flex-1 px-6 py-3 bg-white/10 text-white rounded-lg font-semibold hover:bg-white/20 transition"
                >
                  Close
                </button>
                <button
                  onClick={() => deployStrategy(selectedStrategy)}
                  className="flex-1 px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg font-semibold hover:from-purple-600 hover:to-pink-600 transition flex items-center justify-center gap-2"
                >
                  {selectedStrategy.isPremium && selectedStrategy.price > 0 ? (
                    <>
                      <DollarSign className="w-5 h-5" />
                      Purchase ${selectedStrategy.price}
                    </>
                  ) : (
                    <>
                      <Download className="w-5 h-5" />
                      Deploy Strategy
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
