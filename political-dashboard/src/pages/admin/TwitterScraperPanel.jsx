import React, { useState } from 'react';
import {
  Twitter, Hash, Users, Globe2, Settings2, Play,
  Loader2, CheckCircle2, AlertCircle, ChevronDown, ChevronUp,
  Languages, Zap
} from 'lucide-react';
import api from '../../api/api';

// ─── Constants ────────────────────────────────────────────────────────────────

const PARTIES = ['BJP', 'INC', 'AAP', 'SP', 'TMC', 'BSP', 'CPIM'];

const PARTY_COLORS = {
  BJP:  { bg: 'bg-orange-100', text: 'text-orange-700', dot: 'bg-orange-500' },
  INC:  { bg: 'bg-blue-100',   text: 'text-blue-700',   dot: 'bg-blue-500' },
  AAP:  { bg: 'bg-cyan-100',   text: 'text-cyan-700',   dot: 'bg-cyan-500' },
  SP:   { bg: 'bg-red-100',    text: 'text-red-700',    dot: 'bg-red-500' },
  TMC:  { bg: 'bg-green-100',  text: 'text-green-700',  dot: 'bg-green-500' },
  BSP:  { bg: 'bg-sky-100',    text: 'text-sky-700',    dot: 'bg-sky-500' },
  CPIM: { bg: 'bg-rose-100',   text: 'text-rose-700',   dot: 'bg-rose-500' },
};

const MODES = [
  { id: 'party',   label: 'Party',    icon: Globe2,  desc: 'Scrape by political party' },
  { id: 'handle',  label: 'Handle',   icon: Users,   desc: 'Scrape specific Twitter handles' },
  { id: 'hashtag', label: 'Hashtag',  icon: Hash,    desc: 'Scrape a hashtag or keyword' },
  { id: 'all',     label: 'All',      icon: Zap,     desc: 'Scrape all configured parties' },
];

const LANG_OPTIONS = [
  { value: 'en',  label: '🇬🇧 English only' },
  { value: 'hi',  label: '🇮🇳 Hindi only' },
  { value: 'all', label: '🌐 All languages' },
];

const COUNT_OPTIONS = [50, 100, 200, 500, 1000];

// ─── Stat Badge ───────────────────────────────────────────────────────────────

const StatBadge = ({ label, value, color = 'sky' }) => (
  <div className={`rounded-xl px-3 py-2 bg-${color}-50 border border-${color}-100 text-center min-w-[70px]`}>
    <div className={`text-lg font-bold text-${color}-700`}>{value ?? 0}</div>
    <div className={`text-[10px] text-${color}-500 font-medium uppercase tracking-wide`}>{label}</div>
  </div>
);

// ─── Result Panel ─────────────────────────────────────────────────────────────

const ResultPanel = ({ result }) => {
  if (!result) return null;
  const { ok, data } = result;

  const stats = ok
    ? data?.stats || data?.results || data?.en || null
    : null;

  const newInserted =
    typeof stats?.new_inserted === 'number' ? stats.new_inserted
    : Object.values(stats || {}).reduce((s, v) => s + (v?.new_inserted || 0), 0);

  const totalFetched =
    typeof stats?.total_fetched === 'number' ? stats.total_fetched
    : Object.values(stats || {}).reduce((s, v) => s + (v?.total_fetched || 0), 0);

  return (
    <div className={`border-t px-5 py-4 ${ok ? 'bg-emerald-50 border-emerald-100' : 'bg-red-50 border-red-100'}`}>
      <div className={`flex items-center gap-1.5 text-xs font-semibold mb-3 ${ok ? 'text-emerald-600' : 'text-red-600'}`}>
        {ok ? <CheckCircle2 className="w-3.5 h-3.5" /> : <AlertCircle className="w-3.5 h-3.5" />}
        {ok ? data?.message || 'Completed' : 'Failed'}
      </div>

      {ok && (
        <div className="flex flex-wrap gap-2 mb-3">
          <StatBadge label="New" value={newInserted} color="emerald" />
          <StatBadge label="Fetched" value={totalFetched} color="sky" />
          {data?.stats?.duplicates !== undefined && (
            <StatBadge label="Dupes" value={data.stats.duplicates} color="yellow" />
          )}
          {data?.automation?.sentiment?.analyzed !== undefined && (
            <StatBadge label="Sentiment" value={data.automation.sentiment.analyzed} color="purple" />
          )}
        </div>
      )}

      {!ok && (
        <pre className="text-xs text-red-700 font-mono whitespace-pre-wrap break-words max-h-32 overflow-y-auto">
          {JSON.stringify(data, null, 2)}
        </pre>
      )}
    </div>
  );
};

// ─── Main Component ───────────────────────────────────────────────────────────

const TwitterScraperPanel = () => {
  const [mode, setMode]         = useState('party');
  const [party, setParty]       = useState('BJP');
  const [handles, setHandles]   = useState('');
  const [hashtag, setHashtag]   = useState('');
  const [language, setLanguage] = useState('en');
  const [bilingual, setBilingual] = useState(false);
  const [sinceDays, setSinceDays] = useState(7);
  const [tweetCount, setTweetCount] = useState(200);
  const [product, setProduct]   = useState('Latest');
  const [includePublic, setIncludePublic] = useState(true);
  const [advanced, setAdvanced] = useState(false);
  const [loading, setLoading]   = useState(false);
  const [result, setResult]     = useState(null);

  const run = async () => {
    setLoading(true);
    setResult(null);
    try {
      let endpoint, params;

      if (bilingual) {
        endpoint = '/admin/scrape/twitter/bilingual';
        params = {
          mode,
          since_days: sinceDays,
          target_count: tweetCount,
          include_public: includePublic,
          product,
          ...(mode === 'party'   && { party }),
          ...(mode === 'handle'  && { handles }),
          ...(mode === 'hashtag' && { hashtag }),
        };
      } else if (mode === 'hashtag') {
        endpoint = '/admin/scrape/twitter/hashtag';
        params = { hashtag, language, since_days: sinceDays, target_count: tweetCount, product };
      } else {
        endpoint = '/admin/scrape/twitter';
        params = {
          language,
          since_days: sinceDays,
          target_count: tweetCount,
          include_public: includePublic,
          product,
          ...(mode === 'party'  && { party }),
          ...(mode === 'handle' && { handles }),
        };
      }

      const { data } = await api.post(endpoint, null, { params });
      setResult({ ok: true, data });
    } catch (e) {
      setResult({ ok: false, data: e.response?.data ?? { error: e.message } });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-5 pt-5 pb-4 border-b border-gray-50">
        <div className="flex items-center gap-3 mb-1">
          <div className="w-9 h-9 rounded-xl bg-sky-50 flex items-center justify-center flex-shrink-0">
            <Twitter className="w-5 h-5 text-sky-500" />
          </div>
          <div>
            <h3 className="font-bold text-gray-900 text-sm">Twitter Scraper</h3>
            <p className="text-xs text-gray-400">Select mode, target, and language then run</p>
          </div>
        </div>
      </div>

      <div className="p-5 space-y-4">

        {/* Mode selector */}
        <div>
          <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2 block">Mode</label>
          <div className="grid grid-cols-4 gap-1.5">
            {MODES.map(m => (
              <button
                key={m.id}
                onClick={() => setMode(m.id)}
                title={m.desc}
                className={`flex flex-col items-center gap-1 py-2 px-1 rounded-xl text-xs font-semibold transition-all border
                  ${mode === m.id
                    ? 'bg-sky-600 text-white border-sky-600 shadow-sm'
                    : 'bg-gray-50 text-gray-500 border-gray-100 hover:border-sky-200 hover:text-sky-600'}`}
              >
                <m.icon className="w-4 h-4" />
                {m.label}
              </button>
            ))}
          </div>
        </div>

        {/* Target input based on mode */}
        {mode === 'party' && (
          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2 block">Party</label>
            <div className="flex flex-wrap gap-2">
              {PARTIES.map(p => {
                const c = PARTY_COLORS[p] || {};
                return (
                  <button
                    key={p}
                    onClick={() => setParty(p)}
                    className={`px-3 py-1.5 rounded-full text-xs font-bold border transition-all
                      ${party === p
                        ? `${c.bg} ${c.text} border-current shadow-sm`
                        : 'bg-gray-50 text-gray-400 border-gray-100 hover:border-gray-300'}`}
                  >
                    <span className={`inline-block w-1.5 h-1.5 rounded-full ${party === p ? c.dot : 'bg-gray-300'} mr-1.5`} />
                    {p}
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {mode === 'handle' && (
          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5 block">
              Twitter Handles <span className="normal-case font-normal text-gray-400">(comma-separated, no @)</span>
            </label>
            <input
              type="text"
              value={handles}
              onChange={e => setHandles(e.target.value)}
              placeholder="narendramodi, AmitShah, RahulGandhi"
              className="w-full border border-gray-200 rounded-xl px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-sky-300 focus:border-sky-400"
            />
          </div>
        )}

        {mode === 'hashtag' && (
          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5 block">
              Hashtag or Keyword
            </label>
            <div className="relative">
              <Hash className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                value={hashtag}
                onChange={e => setHashtag(e.target.value)}
                placeholder="#BJP, #Congress, OperationSindoor"
                className="w-full border border-gray-200 rounded-xl pl-9 pr-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-sky-300 focus:border-sky-400"
              />
            </div>
          </div>
        )}

        {/* Language + Bilingual */}
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5 block">Language</label>
            <select
              value={language}
              onChange={e => setLanguage(e.target.value)}
              disabled={bilingual}
              className="w-full border border-gray-200 rounded-xl px-3 py-2.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-sky-300 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {LANG_OPTIONS.map(l => (
                <option key={l.value} value={l.value}>{l.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5 block">Bilingual</label>
            <button
              onClick={() => setBilingual(b => !b)}
              className={`w-full flex items-center justify-center gap-2 py-2.5 px-3 rounded-xl text-sm font-semibold border transition-all
                ${bilingual
                  ? 'bg-indigo-600 text-white border-indigo-600 shadow-sm'
                  : 'bg-gray-50 text-gray-500 border-gray-200 hover:border-indigo-300 hover:text-indigo-600'}`}
            >
              <Languages className="w-4 h-4" />
              {bilingual ? 'EN + HI ✓' : 'EN + HI'}
            </button>
          </div>
        </div>

        {/* Advanced options */}
        <div>
          <button
            onClick={() => setAdvanced(a => !a)}
            className="flex items-center gap-1.5 text-xs font-semibold text-gray-400 hover:text-gray-600 transition-colors"
          >
            <Settings2 className="w-3.5 h-3.5" />
            Advanced options
            {advanced ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
          </button>

          {advanced && (
            <div className="mt-3 grid grid-cols-2 gap-3 p-3.5 bg-gray-50 rounded-xl border border-gray-100">
              {/* Since days */}
              <div className="col-span-2">
                <label className="text-xs font-semibold text-gray-500 mb-1 block">
                  Look-back: <span className="text-gray-800 font-bold">{sinceDays} day{sinceDays !== 1 ? 's' : ''}</span>
                </label>
                <input
                  type="range" min="1" max="180" value={sinceDays}
                  onChange={e => setSinceDays(Number(e.target.value))}
                  className="w-full accent-sky-500"
                />
                <div className="flex justify-between text-[10px] text-gray-400 mt-0.5">
                  <span>1 day</span><span>30d</span><span>90d</span><span>180d</span>
                </div>
              </div>

              {/* Tweet count */}
              <div>
                <label className="text-xs font-semibold text-gray-500 mb-1.5 block">Tweet count</label>
                <select
                  value={tweetCount}
                  onChange={e => setTweetCount(Number(e.target.value))}
                  className="w-full border border-gray-200 rounded-lg px-2.5 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-sky-300"
                >
                  {COUNT_OPTIONS.map(c => <option key={c} value={c}>{c} tweets</option>)}
                </select>
              </div>

              {/* Product */}
              <div>
                <label className="text-xs font-semibold text-gray-500 mb-1.5 block">Search type</label>
                <select
                  value={product}
                  onChange={e => setProduct(e.target.value)}
                  className="w-full border border-gray-200 rounded-lg px-2.5 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-sky-300"
                >
                  <option value="Latest">Latest</option>
                  <option value="Top">Top</option>
                </select>
              </div>

              {/* Include public */}
              {mode === 'party' && (
                <div className="col-span-2 flex items-center gap-2">
                  <input
                    type="checkbox" id="include-public" checked={includePublic}
                    onChange={e => setIncludePublic(e.target.checked)}
                    className="w-4 h-4 rounded accent-sky-500"
                  />
                  <label htmlFor="include-public" className="text-xs text-gray-600 cursor-pointer">
                    Include public conversation (hashtags + mentions)
                  </label>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Run button */}
        <button
          onClick={run}
          disabled={loading || (mode === 'hashtag' && !hashtag.trim()) || (mode === 'handle' && !handles.trim())}
          className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl bg-sky-600 hover:bg-sky-700 text-white text-sm font-bold transition-all shadow-sm shadow-sky-200 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading
            ? <><Loader2 className="w-4 h-4 animate-spin" /> Scraping...</>
            : <><Play className="w-4 h-4" /> Run Scraper</>
          }
        </button>
      </div>

      {/* Result */}
      <ResultPanel result={result} />
    </div>
  );
};

export default TwitterScraperPanel;
