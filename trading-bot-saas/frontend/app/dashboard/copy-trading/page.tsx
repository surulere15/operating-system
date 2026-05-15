'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  Copy,
  Users,
  TrendingUp,
  TrendingDown,
  Activity,
  DollarSign,
  Pause,
  Play,
  Trash2,
  Settings,
  AlertCircle,
  BarChart3,
  Calendar,
  Target
} from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface CopyRelationship {
  id: number;
  trader: {
    id: number;
    display_name: string;
    avatar_url: string;
    total_pnl: number;
    win_rate: number;
    total_trades: number;
    rating: number;
  };
  is_active: boolean;
  copy_amount: number;
  copy_multiplier: number;
  max_daily_loss: number;
  total_copied_trades: number;
  total_pnl: number;
  started_at: string;
}

export default function CopyTradingPage() {
  const router = useRouter();
  const [copies, setCopies] = useState<CopyRelationship[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<number | null>(null);

  useEffect(() => {
    fetchMyCopies();
  }, []);

  const fetchMyCopies = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await axios.get(`${API_URL}/api/social/my-copies`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.data.success) {
        setCopies(response.data.copies);
      }
    } catch (error: any) {
      console.error('Failed to fetch copies:', error);
      if (error.response?.status === 401) {
        router.push('/login');
      }
    } finally {
      setLoading(false);
    }
  };

  const stopCopying = async (copyId: number, traderName: string) => {
    if (!confirm(`Are you sure you want to stop copying ${traderName}? This will close all open copied positions.`)) {
      return;
    }

    setActionLoading(copyId);
    try {
      const token = localStorage.getItem('access_token');
      const response = await axios.delete(`${API_URL}/api/social/copy/${copyId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.data.success) {
        alert(`✅ Stopped copying ${traderName}`);
        fetchMyCopies(); // Refresh list
      }
    } catch (error: any) {
      console.error('Failed to stop copying:', error);
      alert(error.response?.data?.detail || 'Failed to stop copying trader');
    } finally {
      setActionLoading(null);
    }
  };

  const calculateDaysSince = (dateString: string) => {
    const startDate = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now.getTime() - startDate.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  const getTotalStats = () => {
    const totalPnL = copies.reduce((sum, c) => sum + c.total_pnl, 0);
    const totalTrades = copies.reduce((sum, c) => sum + c.total_copied_trades, 0);
    const activeCopies = copies.filter(c => c.is_active).length;
    const totalAllocated = copies.filter(c => c.is_active).reduce((sum, c) => sum + c.copy_amount, 0);

    return { totalPnL, totalTrades, activeCopies, totalAllocated };
  };

  const stats = getTotalStats();

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center text-white">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto"></div>
            <p className="mt-4">Loading your copy trading...</p>
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
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-3">
              <Copy className="w-8 h-8 text-purple-400" />
              <h1 className="text-3xl font-bold text-white">My Copy Trading</h1>
            </div>
            <Link
              href="/dashboard/leaderboard"
              className="px-4 py-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg font-semibold hover:from-purple-600 hover:to-pink-600 transition-all flex items-center gap-2"
            >
              <Users className="w-5 h-5" />
              Browse Traders
            </Link>
          </div>
          <p className="text-gray-300">
            Manage your copy trading relationships and track performance
          </p>
        </div>

        {/* Overview Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6">
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 bg-purple-500/20 rounded-lg">
                <Users className="w-6 h-6 text-purple-400" />
              </div>
              <div>
                <div className="text-gray-400 text-sm">Active Copies</div>
                <div className="text-2xl font-bold text-white">{stats.activeCopies}</div>
              </div>
            </div>
          </div>

          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6">
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 bg-green-500/20 rounded-lg">
                <DollarSign className="w-6 h-6 text-green-400" />
              </div>
              <div>
                <div className="text-gray-400 text-sm">Total P&L</div>
                <div className={`text-2xl font-bold ${stats.totalPnL >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  ${stats.totalPnL >= 0 ? '+' : ''}{stats.totalPnL.toFixed(2)}
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6">
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 bg-blue-500/20 rounded-lg">
                <Activity className="w-6 h-6 text-blue-400" />
              </div>
              <div>
                <div className="text-gray-400 text-sm">Copied Trades</div>
                <div className="text-2xl font-bold text-white">{stats.totalTrades}</div>
              </div>
            </div>
          </div>

          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6">
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 bg-yellow-500/20 rounded-lg">
                <Target className="w-6 h-6 text-yellow-400" />
              </div>
              <div>
                <div className="text-gray-400 text-sm">Total Allocated</div>
                <div className="text-2xl font-bold text-white">${stats.totalAllocated.toFixed(0)}</div>
              </div>
            </div>
          </div>
        </div>

        {/* Copy Relationships */}
        {copies.length === 0 ? (
          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-12 text-center">
            <Copy className="w-16 h-16 text-gray-500 mx-auto mb-4" />
            <h3 className="text-xl font-bold text-white mb-2">No Active Copy Trading</h3>
            <p className="text-gray-400 mb-6">
              You're not copying any traders yet. Browse the leaderboard to find successful traders to copy.
            </p>
            <Link
              href="/dashboard/leaderboard"
              className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg font-semibold hover:from-purple-600 hover:to-pink-600 transition-all"
            >
              <Users className="w-5 h-5" />
              Browse Leaderboard
            </Link>
          </div>
        ) : (
          <div className="space-y-6">
            {copies.map((copy) => (
              <div
                key={copy.id}
                className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/10 hover:border-purple-500/50 transition-all"
              >
                <div className="flex items-start justify-between mb-6">
                  {/* Trader Info */}
                  <div className="flex items-center gap-4">
                    <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center text-white font-bold text-2xl">
                      {copy.trader.display_name[0].toUpperCase()}
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-white mb-1">
                        {copy.trader.display_name}
                      </h3>
                      <div className="flex items-center gap-4 text-sm">
                        <span className="text-gray-400 flex items-center gap-1">
                          <Calendar className="w-4 h-4" />
                          Copying for {calculateDaysSince(copy.started_at)} days
                        </span>
                        <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                          copy.is_active
                            ? 'bg-green-500/20 text-green-400'
                            : 'bg-red-500/20 text-red-400'
                        }`}>
                          {copy.is_active ? '● Active' : '● Paused'}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Actions */}
                  <button
                    onClick={() => stopCopying(copy.id, copy.trader.display_name)}
                    disabled={actionLoading === copy.id}
                    className="px-4 py-2 bg-red-500/20 text-red-400 rounded-lg font-semibold hover:bg-red-500/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                  >
                    {actionLoading === copy.id ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-red-400"></div>
                        Stopping...
                      </>
                    ) : (
                      <>
                        <Trash2 className="w-4 h-4" />
                        Stop Copying
                      </>
                    )}
                  </button>
                </div>

                {/* Stats Grid */}
                <div className="grid grid-cols-2 md:grid-cols-6 gap-4 mb-6">
                  {/* Copy Settings */}
                  <div className="bg-white/5 rounded-lg p-4">
                    <div className="text-gray-400 text-xs mb-1">Copy Amount</div>
                    <div className="text-lg font-bold text-white">
                      ${copy.copy_amount.toFixed(0)}
                    </div>
                  </div>

                  <div className="bg-white/5 rounded-lg p-4">
                    <div className="text-gray-400 text-xs mb-1">Multiplier</div>
                    <div className="text-lg font-bold text-purple-400">
                      {copy.copy_multiplier}x
                    </div>
                  </div>

                  <div className="bg-white/5 rounded-lg p-4">
                    <div className="text-gray-400 text-xs mb-1">Max Loss</div>
                    <div className="text-lg font-bold text-yellow-400">
                      {copy.max_daily_loss}%
                    </div>
                  </div>

                  {/* Performance */}
                  <div className="bg-white/5 rounded-lg p-4">
                    <div className="text-gray-400 text-xs mb-1">Copied Trades</div>
                    <div className="text-lg font-bold text-white flex items-center gap-1">
                      <BarChart3 className="w-4 h-4 text-gray-400" />
                      {copy.total_copied_trades}
                    </div>
                  </div>

                  <div className="bg-white/5 rounded-lg p-4">
                    <div className="text-gray-400 text-xs mb-1">Your P&L</div>
                    <div className={`text-lg font-bold ${copy.total_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      ${copy.total_pnl >= 0 ? '+' : ''}{copy.total_pnl.toFixed(2)}
                    </div>
                  </div>

                  <div className="bg-white/5 rounded-lg p-4">
                    <div className="text-gray-400 text-xs mb-1">ROI</div>
                    <div className={`text-lg font-bold ${
                      (copy.total_pnl / copy.copy_amount * 100) >= 0 ? 'text-green-400' : 'text-red-400'
                    }`}>
                      {(copy.total_pnl / copy.copy_amount * 100).toFixed(1)}%
                    </div>
                  </div>
                </div>

                {/* Trader Performance */}
                <div className="border-t border-white/10 pt-4">
                  <div className="text-sm text-gray-400 mb-3">Trader Performance</div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                      <div className="text-gray-400 text-xs mb-1">Trader P&L</div>
                      <div className={`text-sm font-semibold ${copy.trader.total_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        ${copy.trader.total_pnl >= 0 ? '+' : ''}{copy.trader.total_pnl.toFixed(2)}
                      </div>
                    </div>
                    <div>
                      <div className="text-gray-400 text-xs mb-1">Win Rate</div>
                      <div className="text-sm font-semibold text-white">
                        {copy.trader.win_rate.toFixed(1)}%
                      </div>
                    </div>
                    <div>
                      <div className="text-gray-400 text-xs mb-1">Total Trades</div>
                      <div className="text-sm font-semibold text-white">
                        {copy.trader.total_trades}
                      </div>
                    </div>
                    <div>
                      <div className="text-gray-400 text-xs mb-1">Rating</div>
                      <div className="text-sm font-semibold text-yellow-400">
                        ⭐ {copy.trader.rating.toFixed(1)}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Info Card */}
        <div className="mt-8 bg-blue-500/10 border border-blue-500/30 rounded-xl p-6">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-6 h-6 text-blue-400 flex-shrink-0 mt-1" />
            <div>
              <h4 className="text-blue-400 font-semibold mb-2">How Copy Trading Works</h4>
              <ul className="text-gray-300 text-sm space-y-2">
                <li>• Trades from your selected traders are automatically replicated to your account</li>
                <li>• Position sizes are adjusted based on your copy multiplier setting</li>
                <li>• Copy trading stops automatically if your daily loss limit is reached</li>
                <li>• You can stop copying any trader at any time</li>
                <li>• Past performance does not guarantee future results</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
