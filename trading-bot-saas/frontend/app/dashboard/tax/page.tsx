'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';
import { useRouter } from 'next/navigation';
import {
  FileText,
  Download,
  Calendar,
  DollarSign,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle,
  BarChart3,
  Info,
  Clock
} from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface TaxReport {
  tax_year: number;
  method: string;
  total_transactions: number;
  total_proceeds: number;
  total_cost_basis: number;
  total_gain_loss: number;
  short_term_gain_loss: number;
  long_term_gain_loss: number;
  estimated_short_term_tax: number;
  estimated_long_term_tax: number;
  total_estimated_tax: number;
  transactions: any[];
  symbol_summary: any[];
}

export default function TaxPage() {
  const router = useRouter();
  const [availableYears, setAvailableYears] = useState<number[]>([]);
  const [selectedYear, setSelectedYear] = useState<number>(new Date().getFullYear());
  const [method, setMethod] = useState<'fifo' | 'lifo' | 'hifo'>('fifo');
  const [report, setReport] = useState<TaxReport | null>(null);
  const [washSales, setWashSales] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAvailableYears();
  }, []);

  useEffect(() => {
    if (selectedYear) {
      fetchTaxReport();
      fetchWashSales();
    }
  }, [selectedYear, method]);

  const fetchAvailableYears = async () => {
    try {
      const token = localStorage.getItem('access_token') || localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/api/tax/years`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.data.success) {
        setAvailableYears(response.data.years);
        if (response.data.years.length > 0) {
          setSelectedYear(response.data.years[response.data.years.length - 1]);
        }
      }
    } catch (error: any) {
      console.error('Failed to fetch tax years:', error);
      if (error.response?.status === 401) {
        router.push('/login');
      }
    }
  };

  const fetchTaxReport = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('access_token') || localStorage.getItem('token');
      const response = await axios.get(
        `${API_URL}/api/tax/report?year=${selectedYear}&method=${method}`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      if (response.data.success) {
        setReport(response.data.report);
      }
    } catch (error: any) {
      console.error('Failed to fetch tax report:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchWashSales = async () => {
    try {
      const token = localStorage.getItem('access_token') || localStorage.getItem('token');
      const response = await axios.get(
        `${API_URL}/api/tax/wash-sales?year=${selectedYear}`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      if (response.data.success) {
        setWashSales(response.data.wash_sales);
      }
    } catch (error: any) {
      console.error('Failed to fetch wash sales:', error);
    }
  };

  const downloadForm8949 = async () => {
    try {
      const token = localStorage.getItem('access_token') || localStorage.getItem('token');
      const response = await axios.get(
        `${API_URL}/api/tax/form-8949?year=${selectedYear}&method=${method}`,
        {
          headers: { Authorization: `Bearer ${token}` },
          responseType: 'blob'
        }
      );

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `Form_8949_${selectedYear}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();

      alert('✅ Form 8949 downloaded!');
    } catch (error: any) {
      console.error('Failed to download Form 8949:', error);
      alert('Failed to download Form 8949');
    }
  };

  const downloadTransactionHistory = async () => {
    try {
      const token = localStorage.getItem('access_token') || localStorage.getItem('token');
      const response = await axios.get(
        `${API_URL}/api/tax/transaction-history?year=${selectedYear}`,
        {
          headers: { Authorization: `Bearer ${token}` },
          responseType: 'blob'
        }
      );

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `Transaction_History_${selectedYear}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();

      alert('✅ Transaction history downloaded!');
    } catch (error: any) {
      console.error('Failed to download transaction history:', error);
      alert('Failed to download transaction history');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center text-white">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto"></div>
            <p className="mt-4">Loading tax report...</p>
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
            <FileText className="w-8 h-8 text-purple-400" />
            <h1 className="text-3xl font-bold text-white">Tax Reporting</h1>
          </div>
          <p className="text-gray-300">
            Automated capital gains calculations and IRS Form 8949 generation
          </p>
        </div>

        {/* Controls */}
        <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 mb-8 border border-white/10">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Tax Year */}
            <div>
              <label className="block text-sm font-semibold text-white mb-2">
                Tax Year
              </label>
              <select
                value={selectedYear}
                onChange={(e) => setSelectedYear(parseInt(e.target.value))}
                className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                {availableYears.map(year => (
                  <option key={year} value={year} className="bg-gray-800">
                    {year}
                  </option>
                ))}
              </select>
            </div>

            {/* Cost Basis Method */}
            <div>
              <label className="block text-sm font-semibold text-white mb-2">
                Cost Basis Method
              </label>
              <select
                value={method}
                onChange={(e) => setMethod(e.target.value as any)}
                className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <option value="fifo" className="bg-gray-800">FIFO (First In, First Out)</option>
                <option value="lifo" className="bg-gray-800">LIFO (Last In, First Out)</option>
                <option value="hifo" className="bg-gray-800">HIFO (Highest In, First Out)</option>
              </select>
            </div>

            {/* Downloads */}
            <div>
              <label className="block text-sm font-semibold text-white mb-2">
                Export Reports
              </label>
              <div className="flex gap-2">
                <button
                  onClick={downloadForm8949}
                  className="flex-1 px-4 py-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg font-semibold hover:from-purple-600 hover:to-pink-600 transition flex items-center justify-center gap-2 text-sm"
                >
                  <Download className="w-4 h-4" />
                  Form 8949
                </button>
                <button
                  onClick={downloadTransactionHistory}
                  className="flex-1 px-4 py-2 bg-blue-500/20 text-blue-400 rounded-lg font-semibold hover:bg-blue-500/30 transition flex items-center justify-center gap-2 text-sm"
                >
                  <Download className="w-4 h-4" />
                  History
                </button>
              </div>
            </div>
          </div>
        </div>

        {report && (
          <>
            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/10">
                <div className="flex items-center gap-3 mb-2">
                  <div className="p-2 bg-blue-500/20 rounded-lg">
                    <BarChart3 className="w-6 h-6 text-blue-400" />
                  </div>
                  <div>
                    <div className="text-gray-400 text-sm">Total Transactions</div>
                    <div className="text-2xl font-bold text-white">{report.total_transactions}</div>
                  </div>
                </div>
              </div>

              <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/10">
                <div className="flex items-center gap-3 mb-2">
                  <div className="p-2 bg-green-500/20 rounded-lg">
                    <DollarSign className="w-6 h-6 text-green-400" />
                  </div>
                  <div>
                    <div className="text-gray-400 text-sm">Total Proceeds</div>
                    <div className="text-2xl font-bold text-green-400">
                      ${report.total_proceeds.toLocaleString()}
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/10">
                <div className="flex items-center gap-3 mb-2">
                  <div className={`p-2 rounded-lg ${report.total_gain_loss >= 0 ? 'bg-green-500/20' : 'bg-red-500/20'}`}>
                    {report.total_gain_loss >= 0 ? (
                      <TrendingUp className="w-6 h-6 text-green-400" />
                    ) : (
                      <TrendingDown className="w-6 h-6 text-red-400" />
                    )}
                  </div>
                  <div>
                    <div className="text-gray-400 text-sm">Total Gain/Loss</div>
                    <div className={`text-2xl font-bold ${report.total_gain_loss >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      ${report.total_gain_loss >= 0 ? '+' : ''}{report.total_gain_loss.toLocaleString()}
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/10">
                <div className="flex items-center gap-3 mb-2">
                  <div className="p-2 bg-yellow-500/20 rounded-lg">
                    <FileText className="w-6 h-6 text-yellow-400" />
                  </div>
                  <div>
                    <div className="text-gray-400 text-sm">Est. Tax Liability</div>
                    <div className="text-2xl font-bold text-yellow-400">
                      ${report.total_estimated_tax.toLocaleString()}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Capital Gains Breakdown */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
              <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/10">
                <h2 className="text-xl font-bold text-white mb-6">Short-Term Capital Gains</h2>
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-4 bg-white/5 rounded-lg">
                    <div>
                      <div className="text-gray-400 text-sm mb-1">Gain/Loss (≤365 days)</div>
                      <p className="text-xs text-gray-500">Taxed as ordinary income</p>
                    </div>
                    <div className={`text-2xl font-bold ${report.short_term_gain_loss >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      ${report.short_term_gain_loss >= 0 ? '+' : ''}{report.short_term_gain_loss.toLocaleString()}
                    </div>
                  </div>
                  <div className="flex items-center justify-between p-4 bg-white/5 rounded-lg">
                    <div className="text-gray-400 text-sm">Estimated Tax (24% bracket)</div>
                    <div className="text-xl font-bold text-white">
                      ${report.estimated_short_term_tax.toLocaleString()}
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/10">
                <h2 className="text-xl font-bold text-white mb-6">Long-Term Capital Gains</h2>
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-4 bg-white/5 rounded-lg">
                    <div>
                      <div className="text-gray-400 text-sm mb-1">Gain/Loss (>365 days)</div>
                      <p className="text-xs text-gray-500">Preferential tax rates</p>
                    </div>
                    <div className={`text-2xl font-bold ${report.long_term_gain_loss >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      ${report.long_term_gain_loss >= 0 ? '+' : ''}{report.long_term_gain_loss.toLocaleString()}
                    </div>
                  </div>
                  <div className="flex items-center justify-between p-4 bg-white/5 rounded-lg">
                    <div className="text-gray-400 text-sm">Estimated Tax (15% rate)</div>
                    <div className="text-xl font-bold text-white">
                      ${report.estimated_long_term_tax.toLocaleString()}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Symbol Summary */}
            {report.symbol_summary.length > 0 && (
              <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 mb-8 border border-white/10">
                <h2 className="text-xl font-bold text-white mb-4">Performance by Symbol</h2>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-white/5 border-b border-white/10">
                      <tr>
                        <th className="px-4 py-3 text-left text-sm font-semibold text-gray-300">Symbol</th>
                        <th className="px-4 py-3 text-left text-sm font-semibold text-gray-300">Trades</th>
                        <th className="px-4 py-3 text-left text-sm font-semibold text-gray-300">Proceeds</th>
                        <th className="px-4 py-3 text-left text-sm font-semibold text-gray-300">Cost Basis</th>
                        <th className="px-4 py-3 text-left text-sm font-semibold text-gray-300">Gain/Loss</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/10">
                      {report.symbol_summary.map((item, index) => (
                        <tr key={index} className="hover:bg-white/5">
                          <td className="px-4 py-3 text-white font-semibold">{item.symbol}</td>
                          <td className="px-4 py-3 text-gray-300">{item.trades}</td>
                          <td className="px-4 py-3 text-gray-300">${item.proceeds.toLocaleString()}</td>
                          <td className="px-4 py-3 text-gray-300">${item.cost_basis.toLocaleString()}</td>
                          <td className={`px-4 py-3 font-semibold ${item.gain_loss >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                            ${item.gain_loss >= 0 ? '+' : ''}{item.gain_loss.toLocaleString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Wash Sales Warning */}
            {washSales.length > 0 && (
              <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-xl p-6 mb-8">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="w-6 h-6 text-yellow-400 flex-shrink-0 mt-1" />
                  <div className="flex-1">
                    <h3 className="text-yellow-400 font-semibold mb-2">
                      ⚠️ Potential Wash Sales Detected ({washSales.length})
                    </h3>
                    <p className="text-gray-300 text-sm mb-4">
                      Wash sale rules may apply when you sell a security at a loss and repurchase it within 30 days.
                      Losses from wash sales may be disallowed for tax purposes.
                    </p>
                    <div className="space-y-2">
                      {washSales.slice(0, 3).map((ws, index) => (
                        <div key={index} className="bg-black/20 p-3 rounded-lg text-sm">
                          <div className="text-white font-semibold">{ws.symbol}</div>
                          <div className="text-gray-400">
                            Loss: ${ws.loss_amount} on {ws.sale_date} | Repurchased: {ws.repurchase_date}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Disclaimer */}
            <div className="bg-blue-500/10 border border-blue-500/30 rounded-xl p-6">
              <div className="flex items-start gap-3">
                <Info className="w-6 h-6 text-blue-400 flex-shrink-0 mt-1" />
                <div>
                  <h4 className="text-blue-400 font-semibold mb-2">Tax Disclaimer</h4>
                  <ul className="text-gray-300 text-sm space-y-1">
                    <li>• This report provides estimates based on your trading data using the {report.method} method</li>
                    <li>• Actual tax liability depends on your total income, filing status, and applicable tax brackets</li>
                    <li>• Short-term gains are taxed as ordinary income (10-37% depending on bracket)</li>
                    <li>• Long-term gains have preferential rates (0%, 15%, or 20% depending on income)</li>
                    <li>• <strong>This is not tax advice.</strong> Consult a qualified tax professional or CPA for filing</li>
                    <li>• Download Form 8949 CSV and provide it to your tax preparer</li>
                  </ul>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
