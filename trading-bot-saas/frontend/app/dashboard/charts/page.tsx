'use client';

import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { useRouter } from 'next/navigation';
import {
  TrendingUp,
  Search,
  BarChart3,
  Activity,
  Layers,
  Settings,
  Maximize2,
  Play,
  RefreshCw
} from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Symbol {
  symbol: string;
  exchange: string;
  name: string;
}

const POPULAR_SYMBOLS = [
  { symbol: 'BTCUSDT', name: 'Bitcoin', exchange: 'BYBIT' },
  { symbol: 'ETHUSDT', name: 'Ethereum', exchange: 'BYBIT' },
  { symbol: 'BNBUSDT', name: 'BNB', exchange: 'BYBIT' },
  { symbol: 'SOLUSDT', name: 'Solana', exchange: 'BYBIT' },
  { symbol: 'ADAUSDT', name: 'Cardano', exchange: 'BYBIT' },
  { symbol: 'DOGEUSDT', name: 'Dogecoin', exchange: 'BYBIT' }
];

const TIMEFRAMES = [
  { value: '1', label: '1m' },
  { value: '5', label: '5m' },
  { value: '15', label: '15m' },
  { value: '30', label: '30m' },
  { value: '60', label: '1h' },
  { value: '240', label: '4h' },
  { value: 'D', label: '1D' },
  { value: 'W', label: '1W' }
];

const INDICATORS = [
  { id: 'ma', name: 'Moving Average', shortName: 'MA' },
  { id: 'ema', name: 'Exponential MA', shortName: 'EMA' },
  { id: 'rsi', name: 'RSI', shortName: 'RSI' },
  { id: 'macd', name: 'MACD', shortName: 'MACD' },
  { id: 'bb', name: 'Bollinger Bands', shortName: 'BB' },
  { id: 'volume', name: 'Volume', shortName: 'VOL' }
];

export default function ChartsPage() {
  const router = useRouter();
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const [selectedSymbol, setSelectedSymbol] = useState('BTCUSDT');
  const [selectedTimeframe, setSelectedTimeframe] = useState('15');
  const [selectedIndicators, setSelectedIndicators] = useState<string[]>(['volume']);
  const [searchQuery, setSearchQuery] = useState('');
  const [chartData, setChartData] = useState<any[]>([]);
  const [currentPrice, setCurrentPrice] = useState<number>(0);
  const [priceChange, setPriceChange] = useState<number>(0);
  const [priceChangePercent, setPriceChangePercent] = useState<number>(0);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadChartData();
    const interval = setInterval(loadChartData, 5000); // Update every 5 seconds
    return () => clearInterval(interval);
  }, [selectedSymbol, selectedTimeframe]);

  useEffect(() => {
    // Load TradingView widget script
    const script = document.createElement('script');
    script.src = 'https://s3.tradingview.com/tv.js';
    script.async = true;
    script.onload = () => initTradingViewWidget();
    document.head.appendChild(script);

    return () => {
      document.head.removeChild(script);
    };
  }, [selectedSymbol, selectedTimeframe]);

  const initTradingViewWidget = () => {
    if (typeof (window as any).TradingView !== 'undefined' && chartContainerRef.current) {
      new (window as any).TradingView.widget({
        container_id: 'tradingview_chart',
        autosize: true,
        symbol: `BYBIT:${selectedSymbol}`,
        interval: selectedTimeframe,
        timezone: 'Etc/UTC',
        theme: 'dark',
        style: '1',
        locale: 'en',
        toolbar_bg: '#1f2937',
        enable_publishing: false,
        hide_side_toolbar: false,
        allow_symbol_change: true,
        save_image: false,
        studies: selectedIndicators.map(id => {
          const indicatorMap: Record<string, string> = {
            'ma': 'MASimple@tv-basicstudies',
            'ema': 'MAExp@tv-basicstudies',
            'rsi': 'RSI@tv-basicstudies',
            'macd': 'MACD@tv-basicstudies',
            'bb': 'BB@tv-basicstudies',
            'volume': 'Volume@tv-basicstudies'
          };
          return indicatorMap[id];
        }),
        details: true,
        hotlist: true,
        calendar: false,
        show_popup_button: true,
        popup_width: '1000',
        popup_height: '650'
      });
    }
  };

  const loadChartData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('access_token') || localStorage.getItem('token');

      // Fetch OHLCV data from our backend
      const response = await axios.get(
        `${API_URL}/api/market/ohlcv?symbol=${selectedSymbol}&timeframe=${selectedTimeframe}m&limit=100`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      if (response.data && response.data.length > 0) {
        setChartData(response.data);

        const latest = response.data[response.data.length - 1];
        const previous = response.data[response.data.length - 2];

        setCurrentPrice(latest[4]); // Close price
        const change = latest[4] - previous[4];
        const changePercent = (change / previous[4]) * 100;
        setPriceChange(change);
        setPriceChangePercent(changePercent);
      }
    } catch (error: any) {
      console.error('Failed to load chart data:', error);
      // Don't redirect on error, just log it
    } finally {
      setLoading(false);
    }
  };

  const toggleIndicator = (indicatorId: string) => {
    setSelectedIndicators(prev =>
      prev.includes(indicatorId)
        ? prev.filter(id => id !== indicatorId)
        : [...prev, indicatorId]
    );
  };

  const filteredSymbols = POPULAR_SYMBOLS.filter(s =>
    s.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    s.symbol.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center gap-3 mb-2">
            <BarChart3 className="w-8 h-8 text-purple-400" />
            <h1 className="text-3xl font-bold text-white">Advanced Charts</h1>
          </div>
          <p className="text-gray-300">
            Professional-grade TradingView charts with technical indicators
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Sidebar */}
          <div className="lg:col-span-1 space-y-6">
            {/* Symbol Search */}
            <div className="bg-white/10 backdrop-blur-lg rounded-xl p-4 border border-white/10">
              <h3 className="text-white font-semibold mb-3 flex items-center gap-2">
                <Search className="w-4 h-4" />
                Symbols
              </h3>

              <div className="relative mb-3">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <input
                  type="text"
                  placeholder="Search..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white text-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>

              <div className="space-y-1 max-h-96 overflow-y-auto">
                {filteredSymbols.map(sym => (
                  <button
                    key={sym.symbol}
                    onClick={() => setSelectedSymbol(sym.symbol)}
                    className={`w-full text-left px-3 py-2 rounded-lg transition ${
                      selectedSymbol === sym.symbol
                        ? 'bg-purple-500 text-white'
                        : 'bg-white/5 text-gray-300 hover:bg-white/10'
                    }`}
                  >
                    <div className="font-semibold text-sm">{sym.symbol}</div>
                    <div className="text-xs opacity-75">{sym.name}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Indicators */}
            <div className="bg-white/10 backdrop-blur-lg rounded-xl p-4 border border-white/10">
              <h3 className="text-white font-semibold mb-3 flex items-center gap-2">
                <Layers className="w-4 h-4" />
                Indicators
              </h3>

              <div className="space-y-2">
                {INDICATORS.map(indicator => (
                  <label
                    key={indicator.id}
                    className="flex items-center gap-2 cursor-pointer p-2 rounded-lg hover:bg-white/5 transition"
                  >
                    <input
                      type="checkbox"
                      checked={selectedIndicators.includes(indicator.id)}
                      onChange={() => toggleIndicator(indicator.id)}
                      className="w-4 h-4 rounded border-gray-600 bg-gray-700 text-purple-500 focus:ring-purple-500"
                    />
                    <span className="text-gray-300 text-sm flex-1">{indicator.name}</span>
                    <span className="text-gray-500 text-xs">{indicator.shortName}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>

          {/* Chart Area */}
          <div className="lg:col-span-3 space-y-6">
            {/* Price Info */}
            <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/10">
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-3 mb-2">
                    <h2 className="text-2xl font-bold text-white">{selectedSymbol}</h2>
                    <span className="px-2 py-1 bg-purple-500/20 text-purple-300 rounded-lg text-xs font-semibold">
                      {POPULAR_SYMBOLS.find(s => s.symbol === selectedSymbol)?.name}
                    </span>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-3xl font-bold text-white">
                      ${currentPrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </div>
                    <div className={`flex items-center gap-1 text-lg font-semibold ${
                      priceChange >= 0 ? 'text-green-400' : 'text-red-400'
                    }`}>
                      {priceChange >= 0 ? <TrendingUp className="w-5 h-5" /> : <TrendingUp className="w-5 h-5 rotate-180" />}
                      {priceChange >= 0 ? '+' : ''}{priceChange.toFixed(2)} ({priceChangePercent >= 0 ? '+' : ''}{priceChangePercent.toFixed(2)}%)
                    </div>
                  </div>
                </div>

                <button
                  onClick={loadChartData}
                  disabled={loading}
                  className="px-4 py-2 bg-purple-500/20 text-purple-300 rounded-lg font-semibold hover:bg-purple-500/30 transition disabled:opacity-50 flex items-center gap-2"
                >
                  <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                  Refresh
                </button>
              </div>
            </div>

            {/* Timeframe Selector */}
            <div className="bg-white/10 backdrop-blur-lg rounded-xl p-4 border border-white/10">
              <div className="flex items-center gap-2">
                <Activity className="w-5 h-5 text-gray-400" />
                <span className="text-gray-400 text-sm font-semibold">Timeframe:</span>
                <div className="flex gap-2 flex-wrap">
                  {TIMEFRAMES.map(tf => (
                    <button
                      key={tf.value}
                      onClick={() => setSelectedTimeframe(tf.value)}
                      className={`px-3 py-1 rounded-lg text-sm font-semibold transition ${
                        selectedTimeframe === tf.value
                          ? 'bg-purple-500 text-white'
                          : 'bg-white/10 text-gray-400 hover:bg-white/20'
                      }`}
                    >
                      {tf.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* TradingView Chart */}
            <div className="bg-white/10 backdrop-blur-lg rounded-xl border border-white/10 overflow-hidden">
              <div
                id="tradingview_chart"
                ref={chartContainerRef}
                style={{ height: '600px', width: '100%' }}
              />
            </div>

            {/* Chart Info */}
            <div className="bg-blue-500/10 border border-blue-500/30 rounded-xl p-4">
              <div className="flex items-start gap-3">
                <Activity className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <h4 className="text-blue-400 font-semibold mb-2">Chart Features</h4>
                  <ul className="text-gray-300 text-sm space-y-1">
                    <li>• Real-time price data from Bybit exchange</li>
                    <li>• Multiple timeframes from 1m to 1W</li>
                    <li>• Technical indicators (MA, EMA, RSI, MACD, Bollinger Bands)</li>
                    <li>• Drawing tools and chart patterns</li>
                    <li>• Auto-refresh every 5 seconds</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
