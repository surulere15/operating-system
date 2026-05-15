'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';
import { useRouter } from 'next/navigation';
import {
  Trophy,
  TrendingUp,
  Users,
  Star,
  Copy,
  Search,
  Filter,
  ArrowUpDown,
  CheckCircle,
  Activity,
  Target,
  BarChart3,
  Clock
} from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Trader {
  id: number;
  display_name: string;
  bio: string;
  avatar_url: string;
  total_pnl: number;
  win_rate: number;
  total_trades: number;
  total_followers: number;
  avg_roi: number;
  sharpe_ratio: number;
  rating: number;
  last_trade_at: string;
}

interface CopySettings {
  trader_id: number;
  copy_amount: number;
  copy_multiplier: number;
  max_daily_loss: number;
}

export default function LeaderboardPage() {
  const router = useRouter();
  const [traders, setTraders] = useState<Trader[]>([]);
  const [filteredTraders, setFilteredTraders] = useState<Trader[]>([]);
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState<'total_pnl' | 'win_rate' | 'sharpe_ratio' | 'total_followers'>('total_pnl');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTrader, setSelectedTrader] = useState<Trader | null>(null);
  const [showCopyModal, setShowCopyModal] = useState(false);
  const [copySettings, setCopySettings] = useState<CopySettings>({
    trader_id: 0,
    copy_amount: 100,
    copy_multiplier: 1.0,
    max_daily_loss: 10
  });
  const [copying, setCopying] = useState(false);

  useEffect(() => {
    fetchLeaderboard();
  }, [sortBy]);

  useEffect(() => {
    filterTraders();
  }, [searchQuery, traders]);

  const fetchLeaderboard = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await axios.get(
        `${API_URL}/api/social/leaderboard?limit=50&sort_by=${sortBy}`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      if (response.data.success) {
        setTraders(response.data.traders);
        setFilteredTraders(response.data.traders);
      }
    } catch (error: any) {
      console.error('Failed to fetch leaderboard:', error);
      if (error.response?.status === 401) {
        router.push('/login');
      }
    } finally {
      setLoading(false);
    }
  };

  const filterTraders = () => {
    if (!searchQuery.trim()) {
      setFilteredTraders(traders);
      return;
    }

    const filtered = traders.filter(trader =>
      trader.display_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      trader.bio?.toLowerCase().includes(searchQuery.toLowerCase())
    );
    setFilteredTraders(filtered);
  };

  const openCopyModal = (trader: Trader) => {
    setSelectedTrader(trader);
    setCopySettings({
      trader_id: trader.id,
      copy_amount: 100,
      copy_multiplier: 1.0,
      max_daily_loss: 10
    });
    setShowCopyModal(true);
  };

  const startCopying = async () => {
    if (!selectedTrader) return;

    setCopying(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await axios.post(
        `${API_URL}/api/social/copy/${selectedTrader.id}`,
        {
          copy_amount: copySettings.copy_amount,
          copy_multiplier: copySettings.copy_multiplier,
          max_daily_loss: copySettings.max_daily_loss
        },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      if (response.data.success) {
        alert(`✅ Now copying ${selectedTrader.display_name}!`);
        setShowCopyModal(false);
        fetchLeaderboard(); // Refresh to update follower count
      }
    } catch (error: any) {
      console.error('Failed to start copying:', error);
      alert(error.response?.data?.detail || 'Failed to start copying trader');
    } finally {
      setCopying(false);
    }
  };

  const getRankBadge = (index: number) => {
    if (index === 0) return { icon: '🥇', color: 'text-yellow-400', bg: 'bg-yellow-400/10' };
    if (index === 1) return { icon: '🥈', color: 'text-gray-400', bg: 'bg-gray-400/10' };
    if (index === 2) return { icon: '🥉', color: 'text-orange-400', bg: 'bg-orange-400/10' };
    return { icon: `#${index + 1}`, color: 'text-gray-500', bg: 'bg-gray-500/10' };
  };

  const getPerformanceColor = (value: number) => {
    if (value > 0) return 'text-green-500';
    if (value < 0) return 'text-red-500';
    return 'text-gray-500';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center text-white">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto"></div>
            <p className="mt-4">Loading leaderboard...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <Trophy className="w-8 h-8 text-yellow-400" />
            <h1 className="text-3xl font-bold text-white">Trader Leaderboard</h1>
          </div>
          <p className="text-gray-300">
            Copy the best traders and automatically replicate their winning strategies
          </p>
        </div>

        {/* Controls */}
        <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="Search traders..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>

            {/* Sort */}
            <div className="flex items-center gap-2">
              <Filter className="w-5 h-5 text-gray-400" />
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as any)}
                className="flex-1 px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <option value="total_pnl" className="bg-gray-800">Total Profit</option>
                <option value="win_rate" className="bg-gray-800">Win Rate</option>
                <option value="sharpe_ratio" className="bg-gray-800">Sharpe Ratio</option>
                <option value="total_followers" className="bg-gray-800">Most Followers</option>
              </select>
            </div>
          </div>

          {/* Stats Overview */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
            <div className="bg-white/5 rounded-lg p-4">
              <div className="flex items-center gap-2 text-gray-400 text-sm mb-1">
                <Users className="w-4 h-4" />
                <span>Top Traders</span>
              </div>
              <div className="text-2xl font-bold text-white">{traders.length}</div>
            </div>
            <div className="bg-white/5 rounded-lg p-4">
              <div className="flex items-center gap-2 text-gray-400 text-sm mb-1">
                <TrendingUp className="w-4 h-4" />
                <span>Avg Win Rate</span>
              </div>
              <div className="text-2xl font-bold text-green-400">
                {traders.length > 0 ? (traders.reduce((sum, t) => sum + t.win_rate, 0) / traders.length).toFixed(1) : 0}%
              </div>
            </div>
            <div className="bg-white/5 rounded-lg p-4">
              <div className="flex items-center gap-2 text-gray-400 text-sm mb-1">
                <Activity className="w-4 h-4" />
                <span>Total Trades</span>
              </div>
              <div className="text-2xl font-bold text-white">
                {traders.reduce((sum, t) => sum + t.total_trades, 0).toLocaleString()}
              </div>
            </div>
            <div className="bg-white/5 rounded-lg p-4">
              <div className="flex items-center gap-2 text-gray-400 text-sm mb-1">
                <Trophy className="w-4 h-4" />
                <span>Total Followers</span>
              </div>
              <div className="text-2xl font-bold text-purple-400">
                {traders.reduce((sum, t) => sum + t.total_followers, 0).toLocaleString()}
              </div>
            </div>
          </div>
        </div>

        {/* Leaderboard Table */}
        <div className="bg-white/10 backdrop-blur-lg rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-white/5 border-b border-white/10">
                <tr>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">Rank</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">Trader</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">Total P&L</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">Win Rate</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">Trades</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">Sharpe</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">Followers</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">Rating</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/10">
                {filteredTraders.map((trader, index) => {
                  const rankBadge = getRankBadge(index);
                  return (
                    <tr key={trader.id} className="hover:bg-white/5 transition-colors">
                      {/* Rank */}
                      <td className="px-6 py-4">
                        <div className={`inline-flex items-center justify-center w-10 h-10 rounded-full ${rankBadge.bg}`}>
                          <span className={`text-lg font-bold ${rankBadge.color}`}>
                            {rankBadge.icon}
                          </span>
                        </div>
                      </td>

                      {/* Trader */}
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center text-white font-bold">
                            {trader.display_name[0].toUpperCase()}
                          </div>
                          <div>
                            <div className="font-semibold text-white">{trader.display_name}</div>
                            {trader.bio && (
                              <div className="text-sm text-gray-400 truncate max-w-xs">
                                {trader.bio}
                              </div>
                            )}
                          </div>
                        </div>
                      </td>

                      {/* Total P&L */}
                      <td className="px-6 py-4">
                        <div className={`text-lg font-bold ${getPerformanceColor(trader.total_pnl)}`}>
                          ${trader.total_pnl >= 0 ? '+' : ''}{trader.total_pnl.toFixed(2)}
                        </div>
                        <div className="text-xs text-gray-400">
                          ROI: {trader.avg_roi.toFixed(1)}%
                        </div>
                      </td>

                      {/* Win Rate */}
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <div className={`text-lg font-bold ${trader.win_rate >= 60 ? 'text-green-400' : trader.win_rate >= 50 ? 'text-yellow-400' : 'text-red-400'}`}>
                            {trader.win_rate.toFixed(1)}%
                          </div>
                          {trader.win_rate >= 60 && (
                            <CheckCircle className="w-4 h-4 text-green-400" />
                          )}
                        </div>
                      </td>

                      {/* Trades */}
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2 text-white">
                          <BarChart3 className="w-4 h-4 text-gray-400" />
                          <span className="font-semibold">{trader.total_trades}</span>
                        </div>
                      </td>

                      {/* Sharpe Ratio */}
                      <td className="px-6 py-4">
                        <div className={`font-semibold ${trader.sharpe_ratio > 1 ? 'text-green-400' : trader.sharpe_ratio > 0 ? 'text-yellow-400' : 'text-red-400'}`}>
                          {trader.sharpe_ratio.toFixed(2)}
                        </div>
                      </td>

                      {/* Followers */}
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2 text-purple-400">
                          <Users className="w-4 h-4" />
                          <span className="font-semibold">{trader.total_followers}</span>
                        </div>
                      </td>

                      {/* Rating */}
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-1">
                          <Star className="w-4 h-4 text-yellow-400 fill-yellow-400" />
                          <span className="text-white font-semibold">
                            {trader.rating.toFixed(1)}
                          </span>
                        </div>
                      </td>

                      {/* Action */}
                      <td className="px-6 py-4">
                        <button
                          onClick={() => openCopyModal(trader)}
                          className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg font-semibold hover:from-purple-600 hover:to-pink-600 transition-all"
                        >
                          <Copy className="w-4 h-4" />
                          Copy
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {filteredTraders.length === 0 && (
            <div className="text-center py-12 text-gray-400">
              <Search className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>No traders found matching your search</p>
            </div>
          )}
        </div>

        {/* Copy Trading Modal */}
        {showCopyModal && selectedTrader && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <div className="bg-gradient-to-br from-gray-900 to-purple-900 rounded-2xl p-8 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              {/* Header */}
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center text-white font-bold text-xl">
                    {selectedTrader.display_name[0].toUpperCase()}
                  </div>
                  <div>
                    <h2 className="text-2xl font-bold text-white">Copy {selectedTrader.display_name}</h2>
                    <p className="text-gray-400">Configure your copy trading settings</p>
                  </div>
                </div>
                <button
                  onClick={() => setShowCopyModal(false)}
                  className="text-gray-400 hover:text-white"
                >
                  ✕
                </button>
              </div>

              {/* Trader Stats */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div className="bg-white/10 rounded-lg p-4">
                  <div className="text-gray-400 text-sm mb-1">Total P&L</div>
                  <div className={`text-xl font-bold ${getPerformanceColor(selectedTrader.total_pnl)}`}>
                    ${selectedTrader.total_pnl >= 0 ? '+' : ''}{selectedTrader.total_pnl.toFixed(2)}
                  </div>
                </div>
                <div className="bg-white/10 rounded-lg p-4">
                  <div className="text-gray-400 text-sm mb-1">Win Rate</div>
                  <div className="text-xl font-bold text-green-400">
                    {selectedTrader.win_rate.toFixed(1)}%
                  </div>
                </div>
                <div className="bg-white/10 rounded-lg p-4">
                  <div className="text-gray-400 text-sm mb-1">Sharpe</div>
                  <div className="text-xl font-bold text-white">
                    {selectedTrader.sharpe_ratio.toFixed(2)}
                  </div>
                </div>
                <div className="bg-white/10 rounded-lg p-4">
                  <div className="text-gray-400 text-sm mb-1">Followers</div>
                  <div className="text-xl font-bold text-purple-400">
                    {selectedTrader.total_followers}
                  </div>
                </div>
              </div>

              {/* Copy Settings Form */}
              <div className="space-y-6">
                {/* Copy Amount */}
                <div>
                  <label className="block text-sm font-semibold text-white mb-2">
                    Copy Amount (USDT)
                  </label>
                  <input
                    type="number"
                    min="10"
                    step="10"
                    value={copySettings.copy_amount}
                    onChange={(e) => setCopySettings({...copySettings, copy_amount: parseFloat(e.target.value)})}
                    className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                    placeholder="100"
                  />
                  <p className="text-gray-400 text-sm mt-2">
                    Amount of capital to allocate for copying this trader
                  </p>
                </div>

                {/* Copy Multiplier */}
                <div>
                  <label className="block text-sm font-semibold text-white mb-2">
                    Position Size Multiplier
                  </label>
                  <div className="flex items-center gap-4">
                    <input
                      type="range"
                      min="0.1"
                      max="3"
                      step="0.1"
                      value={copySettings.copy_multiplier}
                      onChange={(e) => setCopySettings({...copySettings, copy_multiplier: parseFloat(e.target.value)})}
                      className="flex-1"
                    />
                    <div className="w-20 px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white text-center font-semibold">
                      {copySettings.copy_multiplier.toFixed(1)}x
                    </div>
                  </div>
                  <p className="text-gray-400 text-sm mt-2">
                    {copySettings.copy_multiplier < 1 && '🔽 Copy smaller positions (less risk)'}
                    {copySettings.copy_multiplier === 1 && '✅ Copy exact same position sizes'}
                    {copySettings.copy_multiplier > 1 && '⚠️ Copy larger positions (higher risk)'}
                  </p>
                </div>

                {/* Max Daily Loss */}
                <div>
                  <label className="block text-sm font-semibold text-white mb-2">
                    Max Daily Loss (%)
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="50"
                    step="1"
                    value={copySettings.max_daily_loss}
                    onChange={(e) => setCopySettings({...copySettings, max_daily_loss: parseFloat(e.target.value)})}
                    className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                    placeholder="10"
                  />
                  <p className="text-gray-400 text-sm mt-2">
                    Stop copying if daily loss exceeds this percentage
                  </p>
                </div>

                {/* Warning */}
                <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4">
                  <div className="flex items-start gap-3">
                    <div className="text-yellow-400 text-2xl">⚠️</div>
                    <div className="flex-1">
                      <h4 className="text-yellow-400 font-semibold mb-1">Risk Warning</h4>
                      <p className="text-gray-300 text-sm">
                        Copy trading involves risk. Past performance does not guarantee future results.
                        Only allocate capital you can afford to lose. You can stop copying at any time.
                      </p>
                    </div>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex gap-4">
                  <button
                    onClick={() => setShowCopyModal(false)}
                    className="flex-1 px-6 py-3 bg-white/10 text-white rounded-lg font-semibold hover:bg-white/20 transition-all"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={startCopying}
                    disabled={copying}
                    className="flex-1 px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg font-semibold hover:from-purple-600 hover:to-pink-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    {copying ? (
                      <>
                        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                        Starting...
                      </>
                    ) : (
                      <>
                        <Copy className="w-5 h-5" />
                        Start Copying
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
