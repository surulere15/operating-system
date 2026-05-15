'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';
import { Trophy, Users, Calendar, DollarSign, TrendingUp, Clock, Award, Target, Activity, Crown } from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Competition {
  id: number;
  name: string;
  description: string;
  status: string;
  start_date: string;
  end_date: string;
  virtual_balance: number;
  max_participants: number;
  current_participants: number;
  total_prize_pool: number;
  first_prize: number;
  second_prize: number;
  third_prize: number;
  rules: string;
  created_at: string;
}

interface CompetitionEntry {
  id: number;
  competition_id: number;
  user_id: number;
  username: string;
  starting_balance: number;
  current_balance: number;
  total_pnl: number;
  total_pnl_percent: number;
  trades_count: number;
  win_rate: number;
  current_rank: number;
  prize_won: number;
  joined_at: string;
}

interface LeaderboardEntry {
  rank: number;
  username: string;
  pnl_percent: number;
  pnl: number;
  trades: number;
  win_rate: number;
  is_current_user: boolean;
}

export default function CompetitionsPage() {
  const [competitions, setCompetitions] = useState<Competition[]>([]);
  const [myCompetitions, setMyCompetitions] = useState<CompetitionEntry[]>([]);
  const [selectedCompetition, setSelectedCompetition] = useState<Competition | null>(null);
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [activeTab, setActiveTab] = useState<'browse' | 'my-competitions' | 'leaderboard'>('browse');
  const [loading, setLoading] = useState(true);
  const [joining, setJoining] = useState(false);

  useEffect(() => {
    fetchCompetitions();
    fetchMyCompetitions();
  }, []);

  const fetchCompetitions = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/api/competitions`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCompetitions(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch competitions:', error);
      setLoading(false);
    }
  };

  const fetchMyCompetitions = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/api/competitions/my`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setMyCompetitions(response.data);
    } catch (error) {
      console.error('Failed to fetch my competitions:', error);
    }
  };

  const fetchLeaderboard = async (competitionId: number) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/api/competitions/${competitionId}/leaderboard`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setLeaderboard(response.data);
    } catch (error) {
      console.error('Failed to fetch leaderboard:', error);
    }
  };

  const joinCompetition = async (competitionId: number) => {
    try {
      setJoining(true);
      const token = localStorage.getItem('token');
      await axios.post(
        `${API_URL}/api/competitions/${competitionId}/join`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      alert('Successfully joined competition! 🎉');
      fetchCompetitions();
      fetchMyCompetitions();
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to join competition');
    } finally {
      setJoining(false);
    }
  };

  const viewLeaderboard = (competition: Competition) => {
    setSelectedCompetition(competition);
    fetchLeaderboard(competition.id);
    setActiveTab('leaderboard');
  };

  const getStatusBadge = (status: string) => {
    const styles = {
      upcoming: 'bg-blue-100 text-blue-800',
      active: 'bg-green-100 text-green-800',
      completed: 'bg-gray-100 text-gray-800'
    };
    return styles[status as keyof typeof styles] || styles.upcoming;
  };

  const getRankIcon = (rank: number) => {
    if (rank === 1) return <Crown className="w-5 h-5 text-yellow-500" />;
    if (rank === 2) return <Award className="w-5 h-5 text-gray-400" />;
    if (rank === 3) return <Award className="w-5 h-5 text-orange-600" />;
    return <span className="text-gray-600 font-semibold">#{rank}</span>;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(amount);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-6 flex items-center justify-center">
        <div className="text-center">
          <Trophy className="w-16 h-16 text-blue-600 mx-auto animate-pulse" />
          <p className="mt-4 text-gray-600">Loading competitions...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <Trophy className="w-8 h-8 text-blue-600" />
            <h1 className="text-3xl font-bold text-gray-900">Trading Competitions</h1>
          </div>
          <p className="text-gray-600">
            Compete with other traders and win prizes! Test your skills in virtual trading competitions.
          </p>
        </div>

        {/* Tabs */}
        <div className="mb-6 border-b border-gray-200">
          <div className="flex gap-6">
            <button
              onClick={() => setActiveTab('browse')}
              className={`pb-3 px-1 font-medium border-b-2 transition-colors ${
                activeTab === 'browse'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              Browse Competitions
            </button>
            <button
              onClick={() => setActiveTab('my-competitions')}
              className={`pb-3 px-1 font-medium border-b-2 transition-colors ${
                activeTab === 'my-competitions'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              My Competitions ({myCompetitions.length})
            </button>
            {selectedCompetition && (
              <button
                onClick={() => setActiveTab('leaderboard')}
                className={`pb-3 px-1 font-medium border-b-2 transition-colors ${
                  activeTab === 'leaderboard'
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-gray-600 hover:text-gray-900'
                }`}
              >
                Leaderboard
              </button>
            )}
          </div>
        </div>

        {/* Browse Competitions Tab */}
        {activeTab === 'browse' && (
          <div className="space-y-6">
            {competitions.length === 0 ? (
              <div className="bg-white rounded-lg shadow p-12 text-center">
                <Trophy className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  No Active Competitions
                </h3>
                <p className="text-gray-600">
                  Check back soon for new trading competitions!
                </p>
              </div>
            ) : (
              competitions.map((competition) => (
                <div key={competition.id} className="bg-white rounded-lg shadow-lg overflow-hidden">
                  <div className="p-6">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="text-2xl font-bold text-gray-900">{competition.name}</h3>
                          <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusBadge(competition.status)}`}>
                            {competition.status.toUpperCase()}
                          </span>
                        </div>
                        <p className="text-gray-600 mb-4">{competition.description}</p>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                      <div className="bg-blue-50 rounded-lg p-4">
                        <div className="flex items-center gap-2 text-blue-600 mb-1">
                          <DollarSign className="w-4 h-4" />
                          <span className="text-sm font-medium">Prize Pool</span>
                        </div>
                        <p className="text-2xl font-bold text-gray-900">
                          {formatCurrency(competition.total_prize_pool)}
                        </p>
                      </div>

                      <div className="bg-green-50 rounded-lg p-4">
                        <div className="flex items-center gap-2 text-green-600 mb-1">
                          <Trophy className="w-4 h-4" />
                          <span className="text-sm font-medium">1st Prize</span>
                        </div>
                        <p className="text-2xl font-bold text-gray-900">
                          {formatCurrency(competition.first_prize)}
                        </p>
                      </div>

                      <div className="bg-purple-50 rounded-lg p-4">
                        <div className="flex items-center gap-2 text-purple-600 mb-1">
                          <Users className="w-4 h-4" />
                          <span className="text-sm font-medium">Participants</span>
                        </div>
                        <p className="text-2xl font-bold text-gray-900">
                          {competition.current_participants}/{competition.max_participants}
                        </p>
                      </div>

                      <div className="bg-orange-50 rounded-lg p-4">
                        <div className="flex items-center gap-2 text-orange-600 mb-1">
                          <Target className="w-4 h-4" />
                          <span className="text-sm font-medium">Starting Balance</span>
                        </div>
                        <p className="text-2xl font-bold text-gray-900">
                          {formatCurrency(competition.virtual_balance)}
                        </p>
                      </div>
                    </div>

                    <div className="mb-6 space-y-3">
                      <div className="flex items-center gap-2 text-gray-600">
                        <Calendar className="w-5 h-5" />
                        <span>
                          <strong>Start:</strong> {formatDate(competition.start_date)}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 text-gray-600">
                        <Clock className="w-5 h-5" />
                        <span>
                          <strong>End:</strong> {formatDate(competition.end_date)}
                        </span>
                      </div>
                    </div>

                    <div className="mb-6">
                      <h4 className="font-semibold text-gray-900 mb-2">Rules:</h4>
                      <p className="text-gray-600 whitespace-pre-line">{competition.rules}</p>
                    </div>

                    <div className="flex gap-3">
                      {competition.status === 'upcoming' || competition.status === 'active' ? (
                        <button
                          onClick={() => joinCompetition(competition.id)}
                          disabled={joining || competition.current_participants >= competition.max_participants}
                          className={`flex-1 py-3 px-6 rounded-lg font-semibold transition-colors ${
                            competition.current_participants >= competition.max_participants
                              ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                              : 'bg-blue-600 text-white hover:bg-blue-700'
                          }`}
                        >
                          {competition.current_participants >= competition.max_participants
                            ? 'Competition Full'
                            : joining
                            ? 'Joining...'
                            : 'Join Competition'}
                        </button>
                      ) : null}
                      <button
                        onClick={() => viewLeaderboard(competition)}
                        className="px-6 py-3 border border-gray-300 rounded-lg font-semibold text-gray-700 hover:bg-gray-50 transition-colors"
                      >
                        View Leaderboard
                      </button>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* My Competitions Tab */}
        {activeTab === 'my-competitions' && (
          <div className="space-y-6">
            {myCompetitions.length === 0 ? (
              <div className="bg-white rounded-lg shadow p-12 text-center">
                <Trophy className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  No Competitions Yet
                </h3>
                <p className="text-gray-600 mb-4">
                  Join a competition to start competing!
                </p>
                <button
                  onClick={() => setActiveTab('browse')}
                  className="px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors"
                >
                  Browse Competitions
                </button>
              </div>
            ) : (
              myCompetitions.map((entry) => {
                const competition = competitions.find(c => c.id === entry.competition_id);
                if (!competition) return null;

                return (
                  <div key={entry.id} className="bg-white rounded-lg shadow-lg p-6">
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <h3 className="text-xl font-bold text-gray-900 mb-1">{competition.name}</h3>
                        <p className="text-gray-600">Joined: {formatDate(entry.joined_at)}</p>
                      </div>
                      <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusBadge(competition.status)}`}>
                        {competition.status.toUpperCase()}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-4">
                      <div className="bg-gray-50 rounded-lg p-4">
                        <div className="flex items-center gap-2 text-gray-600 mb-1">
                          <Activity className="w-4 h-4" />
                          <span className="text-xs font-medium">Current Rank</span>
                        </div>
                        <p className="text-xl font-bold text-gray-900">#{entry.current_rank}</p>
                      </div>

                      <div className="bg-green-50 rounded-lg p-4">
                        <div className="flex items-center gap-2 text-green-600 mb-1">
                          <TrendingUp className="w-4 h-4" />
                          <span className="text-xs font-medium">P&L</span>
                        </div>
                        <p className={`text-xl font-bold ${entry.total_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {entry.total_pnl >= 0 ? '+' : ''}{entry.total_pnl_percent.toFixed(2)}%
                        </p>
                      </div>

                      <div className="bg-blue-50 rounded-lg p-4">
                        <div className="flex items-center gap-2 text-blue-600 mb-1">
                          <DollarSign className="w-4 h-4" />
                          <span className="text-xs font-medium">Balance</span>
                        </div>
                        <p className="text-xl font-bold text-gray-900">
                          {formatCurrency(entry.current_balance)}
                        </p>
                      </div>

                      <div className="bg-purple-50 rounded-lg p-4">
                        <div className="flex items-center gap-2 text-purple-600 mb-1">
                          <Target className="w-4 h-4" />
                          <span className="text-xs font-medium">Trades</span>
                        </div>
                        <p className="text-xl font-bold text-gray-900">{entry.trades_count}</p>
                      </div>

                      <div className="bg-orange-50 rounded-lg p-4">
                        <div className="flex items-center gap-2 text-orange-600 mb-1">
                          <Trophy className="w-4 h-4" />
                          <span className="text-xs font-medium">Win Rate</span>
                        </div>
                        <p className="text-xl font-bold text-gray-900">{entry.win_rate.toFixed(1)}%</p>
                      </div>
                    </div>

                    {entry.prize_won > 0 && (
                      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
                        <div className="flex items-center gap-2">
                          <Crown className="w-5 h-5 text-yellow-600" />
                          <span className="font-semibold text-yellow-900">
                            Prize Won: {formatCurrency(entry.prize_won)}
                          </span>
                        </div>
                      </div>
                    )}

                    <button
                      onClick={() => viewLeaderboard(competition)}
                      className="w-full py-3 px-6 border border-gray-300 rounded-lg font-semibold text-gray-700 hover:bg-gray-50 transition-colors"
                    >
                      View Leaderboard
                    </button>
                  </div>
                );
              })
            )}
          </div>
        )}

        {/* Leaderboard Tab */}
        {activeTab === 'leaderboard' && selectedCompetition && (
          <div className="bg-white rounded-lg shadow-lg">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">{selectedCompetition.name}</h2>
              <p className="text-gray-600">Live Rankings</p>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Rank</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Trader</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">P&L %</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">P&L ($)</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Trades</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Win Rate</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {leaderboard.map((entry) => (
                    <tr
                      key={entry.rank}
                      className={entry.is_current_user ? 'bg-blue-50' : 'hover:bg-gray-50'}
                    >
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center gap-2">
                          {getRankIcon(entry.rank)}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="font-medium text-gray-900">
                          {entry.username}
                          {entry.is_current_user && (
                            <span className="ml-2 text-xs text-blue-600 font-semibold">(You)</span>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right">
                        <span className={`font-semibold ${entry.pnl_percent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {entry.pnl_percent >= 0 ? '+' : ''}{entry.pnl_percent.toFixed(2)}%
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right">
                        <span className={entry.pnl >= 0 ? 'text-green-600' : 'text-red-600'}>
                          {formatCurrency(entry.pnl)}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-gray-900">
                        {entry.trades}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-gray-900">
                        {entry.win_rate.toFixed(1)}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {leaderboard.length === 0 && (
              <div className="p-12 text-center">
                <Users className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-600">No participants yet</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
