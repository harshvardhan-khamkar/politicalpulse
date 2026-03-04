import React, { useState, useEffect } from 'react';
import api from '../api/api';

// ─── Skeleton ─────────────────────────────────────────────────────────────────

const Skeleton = ({ className }) => (
    <div className={`animate-pulse bg-gray-200 rounded ${className}`} />
);

const NewsSkeleton = () => (
    <div className="space-y-8">
        {/* Lead story skeleton */}
        <div className="border-b border-gray-300 pb-8">
            <Skeleton className="h-4 w-24 mb-3" />
            <Skeleton className="h-10 w-3/4 mb-2" />
            <Skeleton className="h-10 w-1/2 mb-4" />
            <div className="flex gap-6">
                <div className="flex-1 space-y-2">
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-5/6" />
                    <Skeleton className="h-4 w-4/6" />
                </div>
                <Skeleton className="w-48 h-32 flex-shrink-0" />
            </div>
        </div>
        {/* Grid skeleton */}
        <div className="grid grid-cols-2 gap-6">
            {[1, 2, 3, 4].map(i => (
                <div key={i} className="border-b border-gray-200 pb-5 space-y-2">
                    <Skeleton className="h-5 w-full" />
                    <Skeleton className="h-5 w-3/4" />
                    <Skeleton className="h-3 w-full" />
                    <Skeleton className="h-3 w-5/6" />
                    <Skeleton className="h-3 w-16" />
                </div>
            ))}
        </div>
    </div>
);

// ─── Helpers ──────────────────────────────────────────────────────────────────

const fmtTime = (str) => {
    if (!str) return '';
    try {
        return new Date(str).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true });
    } catch { return ''; }
};

const fmtDate = (str) => {
    if (!str) return '';
    try {
        return new Date(str).toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' });
    } catch { return ''; }
};

const today = () => new Date().toLocaleDateString('en-IN', {
    weekday: 'long', day: 'numeric', month: 'long', year: 'numeric'
});

// ─── Lead Article ─────────────────────────────────────────────────────────────

const LeadArticle = ({ article }) => (
    <div className="border-b-2 border-black pb-8 mb-8">
        {article.category && (
            <p className="text-[11px] font-bold uppercase tracking-widest text-gray-500 mb-2">{article.category}</p>
        )}
        <div className="flex gap-6 items-start">
            <div className="flex-1 min-w-0">
                <h2 style={{ fontFamily: "'Playfair Display', serif" }}
                    className="text-3xl md:text-4xl font-bold text-black leading-tight mb-4">
                    {article.title}
                </h2>
                {article.description && (
                    <p style={{ fontFamily: "'Merriweather', serif" }}
                        className="text-gray-700 text-sm leading-relaxed mb-4 line-clamp-4">
                        {article.description}
                    </p>
                )}
                <div className="flex items-center gap-3 text-[11px] text-gray-400 font-medium">
                    {article.source?.name && <span className="uppercase tracking-wider font-bold text-gray-600">{article.source.name}</span>}
                    {article.source?.name && article.publishedAt && <span>·</span>}
                    {article.publishedAt && <span>{fmtTime(article.publishedAt)}</span>}
                    {article.publishedAt && <span>{fmtDate(article.publishedAt)}</span>}
                    {article.url && (
                        <a href={article.url} target="_blank" rel="noopener noreferrer"
                            className="ml-auto text-gray-400 hover:text-black underline underline-offset-2 transition-colors">
                            Read full article →
                        </a>
                    )}
                </div>
            </div>
            {article.urlToImage && (
                <div className="hidden md:block flex-shrink-0 w-52 xl:w-64">
                    <img
                        src={article.urlToImage}
                        alt={article.title}
                        className="w-full h-36 object-cover grayscale"
                        onError={e => { e.target.style.display = 'none'; }}
                    />
                </div>
            )}
        </div>
    </div>
);

// ─── Grid Article ─────────────────────────────────────────────────────────────

const GridArticle = ({ article }) => (
    <div className="border-b border-gray-200 pb-5">
        {article.category && (
            <p className="text-[10px] font-bold uppercase tracking-widest text-gray-400 mb-1">{article.category}</p>
        )}
        <h3 style={{ fontFamily: "'Playfair Display', serif" }}
            className="text-base font-bold text-black leading-snug mb-2">
            {article.url ? (
                <a href={article.url} target="_blank" rel="noopener noreferrer"
                    className="hover:underline underline-offset-2">
                    {article.title}
                </a>
            ) : article.title}
        </h3>
        {article.description && (
            <p style={{ fontFamily: "'Merriweather', serif" }}
                className="text-gray-600 text-xs leading-relaxed mb-2 line-clamp-2">
                {article.description}
            </p>
        )}
        <div className="flex items-center gap-2 text-[10px] text-gray-400">
            {article.source?.name && <span className="font-bold text-gray-500 uppercase tracking-wider">{article.source.name}</span>}
            {article.publishedAt && <span>· {fmtTime(article.publishedAt)}</span>}
        </div>
    </div>
);

// ─── Main Newspaper Page Component ────────────────────────────────────────────

const NewspaperPage = ({ endpoint, edition }) => {
    const [articles, setArticles] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        const fetch = async () => {
            setLoading(true);
            setError('');
            try {
                const { data } = await api.get(endpoint);
                const list = Array.isArray(data) ? data : data.articles ?? data.results ?? [];
                setArticles(list.filter(a => a.title && a.title !== '[Removed]'));
            } catch (e) {
                setError(e.response?.data?.detail || e.message || 'Failed to load news.');
            } finally {
                setLoading(false);
            }
        };
        fetch();
    }, [endpoint]);

    const lead = articles[0];
    const rest = articles.slice(1);

    return (
        <div className="max-w-5xl mx-auto">
            {/* ── Masthead ── */}
            <div className="text-center py-6 border-b-2 border-black mb-2">
                <h1 style={{ fontFamily: "'Playfair Display', serif" }}
                    className="text-5xl md:text-6xl font-extrabold tracking-tight text-black uppercase">
                    VARTAMANPATRA
                </h1>
                <p style={{ fontFamily: "'Merriweather', serif" }}
                    className="text-sm text-gray-500 mt-1 font-light tracking-widest uppercase">
                    Your Daily Political Brief
                </p>
                <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-gray-400 mt-1">{edition}</p>
            </div>

            {/* ── Date strip ── */}
            <div className="flex items-center justify-between text-[11px] text-gray-500 uppercase tracking-widest py-2 border-b border-gray-300 mb-8">
                <span>{today()}</span>
                <span className="font-bold">Est. 2025</span>
            </div>

            {/* ── Loading ── */}
            {loading && <NewsSkeleton />}

            {/* ── Error ── */}
            {!loading && error && (
                <p className="text-sm text-red-500 text-center py-12">{error}</p>
            )}

            {/* ── No articles ── */}
            {!loading && !error && articles.length === 0 && (
                <p style={{ fontFamily: "'Merriweather', serif" }}
                    className="text-gray-400 text-sm text-center py-16 italic">
                    No stories available at this time.
                </p>
            )}

            {/* ── Content ── */}
            {!loading && !error && articles.length > 0 && (
                <>
                    {/* Lead story */}
                    {lead && <LeadArticle article={lead} />}

                    {/* Grid */}
                    {rest.length > 0 && (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-0">
                            {/* Column separator line in the middle on desktop */}
                            {rest.map((a, i) => (
                                <GridArticle key={i} article={a} />
                            ))}
                        </div>
                    )}
                </>
            )}
        </div>
    );
};

export default NewspaperPage;
