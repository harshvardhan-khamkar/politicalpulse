import React, { useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
    ArrowLeft,
    ArrowRight,
    BookOpen,
    ChevronsLeft,
    ChevronsRight,
    Download,
    Search
} from 'lucide-react';

const TOTAL_PAGES = 162;
const TOTAL_SPREADS = Math.ceil((TOTAL_PAGES + 1) / 2);
const EBOOK_BASE_PATH = `${import.meta.env.BASE_URL}ebook`;
const TURN_DURATION_MS = 800;

// Premium Light Theme CSS
const lightThemeStyles = `
/* Light Master Background */
.ebook-master-container {
  height: calc(100vh - 64px); 
  width: 100%;
  position: relative;
  background: #f1f5f9; 
  background-image: 
    radial-gradient(circle at top left, rgba(255, 255, 255, 1) 0%, transparent 60%),
    radial-gradient(circle at bottom right, rgba(226, 232, 240, 1) 0%, transparent 60%);
  overflow: hidden;
  font-family: 'Inter', system-ui, sans-serif;
  color: #0f172a; 
}

/* Light Header - Floating Overlay */
.ebook-topbar {
  position: absolute;
  top: 0; left: 0; right: 0;
  padding: 1rem 2rem;
  background: linear-gradient(to bottom, rgba(255,255,255,0.9) 0%, rgba(255,255,255,0) 100%);
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  z-index: 50;
  pointer-events: none; /* Let clicks pass to the book */
}
.ebook-topbar > * {
  pointer-events: auto; /* Buttons are clickable */
}

/* Canvas Area - Edge to Edge */
.ebook-3d-scene {
  position: absolute;
  inset: 0;
  display: flex;
  justify-content: center;
  align-items: center;
  perspective: 3500px;
  overflow: hidden;
  padding: 2rem 1rem; /* Minimal padding */
}

/* Light Footer Controls - Floating Overlay */
.ebook-bottombar {
  position: absolute;
  bottom: 0; left: 0; right: 0;
  padding: 1rem 2rem;
  background: linear-gradient(to top, rgba(255,255,255,0.95) 0%, rgba(255,255,255,0) 100%);
  display: flex;
  flex-direction: column;
  align-items: center;
  z-index: 50;
  pointer-events: none;
}
.ebook-bottombar > * {
  pointer-events: auto;
}

/* Wide Horizontal Book Dimensions */
.book-volume {
  position: relative;
  /* Accurate horizontal aspect ratio: ~2.665 width to 1 height (two 1800x1351 images side-by-side) */
  aspect-ratio: 2.665 / 1; 
  width: 100%;             /* Start by taking full width */
  max-width: 100%;         /* Do not overflow horizontally */
  max-height: 100%;        /* Do not overflow vertically; allow aspect-ratio to shrink width if needed */
  display: flex;
  transform-style: preserve-3d;
  transition: transform 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.book-volume.is-cover { transform: translateX(-25%); }
.book-volume.is-back-cover { transform: translateX(25%); }

.book-spine {
  position: absolute;
  left: 50%;
  top: -4px;
  bottom: -4px;
  width: 40px;
  transform: translateX(-50%) translateZ(-2px);
  background: linear-gradient(90deg, #94a3b8 0%, #cbd5e1 15%, #f1f5f9 50%, #cbd5e1 85%, #94a3b8 100%);
  border-radius: 4px;
  box-shadow: inset 0 0 10px rgba(0,0,0,0.1), 0 10px 30px rgba(0,0,0,0.2);
  z-index: 0;
}

.sheet {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 50%;
  background: #ffffff;
  transform-style: preserve-3d;
  border: 1px solid rgba(0,0,0,0.05); /* Sharp crisp edge */
  box-shadow: 0 10px 40px rgba(0,0,0,0.1);
}
.sheet.left { left: 0; border-radius: 8px 0 0 8px; transform-origin: right center; }
.sheet.right { left: 50%; border-radius: 0 8px 8px 0; transform-origin: left center; }

/* The physical page turning element */
.turner {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 50%;
  z-index: 100;
  transform-style: preserve-3d;
  transition: transform ${TURN_DURATION_MS}ms cubic-bezier(0.645, 0.045, 0.355, 1);
}
.turner.turn-fwd { left: 50%; transform-origin: left center; transform: rotateY(-180deg); }
.turner.turn-bck { left: 0; transform-origin: right center; transform: rotateY(180deg); }

.turner-side {
  position: absolute;
  inset: 0;
  backface-visibility: hidden;
  background: #ffffff;
  overflow: hidden;
  border: 1px solid rgba(0,0,0,0.05);
}
.turner.turn-fwd .turner-side.front { transform: rotateY(0deg); border-radius: 0 8px 8px 0; }
.turner.turn-fwd .turner-side.back { transform: rotateY(180deg); border-radius: 8px 0 0 8px; }
.turner.turn-bck .turner-side.front { transform: rotateY(0deg); border-radius: 8px 0 0 8px; }
.turner.turn-bck .turner-side.back { transform: rotateY(180deg); border-radius: 0 8px 8px 0; }

.page-graphic {
  width: 100%;
  height: 100%;
  object-fit: contain; /* Guarantee entire election graphic is visible */
  background: #ffffff;
}

/* Crease & Lighting Shadows (Light Theme Adjusted) */
.sheet.left::after, .turner.turn-fwd .turner-side.back::after, .turner.turn-bck .turner-side.front::after {
  content: ''; position: absolute; inset: 0; background: linear-gradient(90deg, transparent 92%, rgba(0,0,0,0.08) 100%); pointer-events: none;
}
.sheet.right::after, .turner.turn-fwd .turner-side.front::after, .turner.turn-bck .turner-side.back::after {
  content: ''; position: absolute; inset: 0; background: linear-gradient(270deg, transparent 92%, rgba(0,0,0,0.08) 100%); pointer-events: none;
}
.turner-side::before {
  content: ''; position: absolute; inset: 0; background: linear-gradient(to right, rgba(255,255,255,0.4), rgba(0,0,0,0.05));
  opacity: 0; transition: opacity ${TURN_DURATION_MS / 2}ms; pointer-events: none; z-index: 10;
}
.turner.turn-fwd .turner-side.front::before { opacity: 1; background: linear-gradient(to left, rgba(255,255,255,0.8), rgba(0,0,0,0.1)); }
.turner.turn-bck .turner-side.front::before { opacity: 1; background: linear-gradient(to right, rgba(255,255,255,0.8), rgba(0,0,0,0.1)); }

/* Base Book Drop Shadow */
.book-volume::after {
  content: ''; position: absolute; left: 1%; right: 1%; bottom: -10px; height: 10px;
  background: rgba(0,0,0,0.3); filter: blur(15px); z-index: -1; transition: all 0.6s ease;
}
.book-volume.is-cover::after { left: 51%; right: 1%; }
.book-volume.is-back-cover::after { left: 1%; right: 51%; }

/* Highly Visible Large Next/Prev Arrows */
.nav-arrow-btn {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  color: #0f172a;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 40;
  box-shadow: 0 10px 25px rgba(0,0,0,0.1);
}
.nav-arrow-btn:hover:not(:disabled) {
  background: #f8fafc;
  border-color: #cbd5e1;
  box-shadow: 0 15px 35px rgba(0,0,0,0.15);
  transform: translateY(-50%) scale(1.05);
}
.nav-arrow-btn:active:not(:disabled) {
  transform: translateY(-50%) scale(0.95);
}
.nav-arrow-btn:disabled { opacity: 0; pointer-events: none; }
.nav-arrow-btn.prev { left: 2%; } /* Pin to outer edges */
.nav-arrow-btn.next { right: 2%; }

/* Solid High Contrast Buttons */
.btn-solid {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  background: #ffffff;
  border: 1px solid #cbd5e1;
  color: #0f172a;
  font-weight: 700;
  font-size: 0.875rem;
  transition: all 0.2s;
  cursor: pointer;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}
.btn-solid:hover:not(:disabled) {
  background: #f8fafc;
  border-color: #94a3b8;
  transform: translateY(-1px);
  box-shadow: 0 4px 6px rgba(0,0,0,0.05);
}
.btn-solid:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}
.btn-solid-primary {
  background: #0284c7; /* Sky 600 */
  border-color: #0284c7;
  color: #ffffff;
}
.btn-solid-primary:hover:not(:disabled) {
  background: #0369a1; /* Sky 700 */
  border-color: #0369a1;
}

/* Light Theme Inputs */
.input-solid {
  background: #ffffff;
  border: 1px solid #cbd5e1;
  color: #0f172a;
  padding: 0.75rem 1rem;
  border-radius: 8px 0 0 8px;
  font-size: 0.875rem;
  font-weight: 500;
  outline: none;
  width: 140px;
  transition: all 0.2s;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05) inset;
}
.input-solid:focus {
  border-color: #0ea5e9;
  box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.2);
}

/* Bright Progress Bar */
.progress-track-light {
  width: 100%;
  height: 8px;
  background: #e2e8f0;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 0.75rem;
  box-shadow: inset 0 1px 2px rgba(0,0,0,0.1);
}
.progress-fill-light {
  height: 100%;
  background: #0ea5e9;
  border-radius: 4px;
  transition: width 0.4s ease;
}

/* Status Pill */
.status-pill {
  padding: 0.5rem 1.5rem;
  border-radius: 99px;
  background: #f1f5f9;
  border: 1px solid #cbd5e1;
  color: #475569;
  font-weight: 700;
  font-size: 0.875rem;
}

/* Mobile Restyle */
.mobile-view { display: none; }
@media (max-width: 1024px) {
  .nav-arrow-btn.prev { left: 1%; } 
  .nav-arrow-btn.next { right: 1%; }
}
@media (max-width: 768px) {
  .ebook-3d-scene { display: none; } 
  .mobile-view {
    display: flex;
    flex-direction: column;
    flex: 1 1 auto;
    overflow-y: auto;
    padding: 1.5rem;
    gap: 1.5rem;
    background: #f1f5f9;
  }
  .mobile-page {
    width: 100%;
    border-radius: 8px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    background: #fff;
    object-fit: contain;
  }
}
`;

const getPageUrl = (pg) => {
    if (pg < 1 || pg > TOTAL_PAGES) return null;
    return `${EBOOK_BASE_PATH}/${pg}.jpg`;
};

const getSpreadIndices = (sprd) => {
    if (sprd === 0) return { lIdx: null, rIdx: 1 };
    const lIdx = sprd * 2;
    const rIdx = lIdx + 1 <= TOTAL_PAGES ? lIdx + 1 : null;
    return { lIdx, rIdx };
};

export default function EBookPage() {
    const [searchParams, setSearchParams] = useSearchParams();
    const initPage = parseInt(searchParams.get('page') || '1', 10);
    const initSpread = initPage <= 1 ? 0 : Math.floor(initPage / 2);
    
    const [spread, setSpread] = useState(Math.min(Math.max(initSpread, 0), TOTAL_SPREADS));
    const [jumpInput, setJumpInput] = useState('');
    const [animState, setAnimState] = useState(null); // 'fwd' | 'bck' | null
    const timerRef = useRef(null);

    // Sync Query Params cleanly
    useEffect(() => {
        const { lIdx, rIdx } = getSpreadIndices(spread);
        const displayPage = rIdx || lIdx || 1;
        const newParams = new URLSearchParams(searchParams);
        if (displayPage <= 1) newParams.delete('page');
        else newParams.set('page', String(displayPage));
        setSearchParams(newParams, { replace: true });
    }, [spread, searchParams, setSearchParams]);

    // Keyboard bindings cleanly
    useEffect(() => {
        const handleKeyDown = (e) => {
            if (e.target.tagName === 'INPUT' || animState) return;
            if (e.key === 'ArrowRight' || e.key === ' ') {
                e.preventDefault(); triggerTurn('fwd');
            } else if (e.key === 'ArrowLeft') {
                e.preventDefault(); triggerTurn('bck');
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [spread, animState]);

    useEffect(() => {
        return () => { if (timerRef.current) clearTimeout(timerRef.current); };
    }, []);

    const triggerTurn = (direction) => {
        if (animState) return;
        if (direction === 'fwd' && spread < TOTAL_SPREADS) {
            setAnimState('fwd');
            timerRef.current = setTimeout(() => {
                setSpread(s => s + 1);
                setAnimState(null);
            }, TURN_DURATION_MS);
        } else if (direction === 'bck' && spread > 0) {
            setAnimState('bck');
            timerRef.current = setTimeout(() => {
                setSpread(s => s - 1);
                setAnimState(null);
            }, TURN_DURATION_MS);
        }
    };

    const handleSpeedJump = (e) => {
        e.preventDefault();
        const num = parseInt(jumpInput, 10);
        if (!isNaN(num) && num >= 1 && num <= TOTAL_PAGES) {
            setSpread(num <= 1 ? 0 : Math.floor(num / 2));
            setJumpInput('');
        }
    };

    const { lIdx, rIdx } = getSpreadIndices(spread);
    
    // Resolve animation flip surfaces
    let flipFaceA, flipFaceB;
    if (animState === 'fwd') {
        flipFaceA = rIdx;
        flipFaceB = getSpreadIndices(spread + 1).lIdx;
    } else if (animState === 'bck') {
        flipFaceA = lIdx;
        flipFaceB = getSpreadIndices(spread - 1).rIdx;
    }

    const isCover = spread === 0;
    const isBackCover = spread === TOTAL_SPREADS;
    const completionPct = Math.round((spread / TOTAL_SPREADS) * 100);

    return (
        <div className="ebook-master-container">
            <style>{lightThemeStyles}</style>

            <header className="ebook-topbar">
                <div className="flex items-center gap-4">
                    <div className="bg-sky-100 p-3 rounded-lg border border-sky-200">
                        <BookOpen className="w-6 h-6 text-sky-600" />
                    </div>
                    <div>
                        <h1 className="text-2xl font-black text-slate-800 tracking-tight">
                            Election Returns 2024
                        </h1>
                        <p className="text-xs font-bold text-slate-500 uppercase tracking-[0.15em] mt-0.5">Interactive Document Viewer</p>
                    </div>
                </div>

                <div className="flex items-center gap-6">
                    <form onSubmit={handleSpeedJump} className="flex shadow-sm rounded-lg">
                        <input
                            type="number"
                            min="1"
                            max={TOTAL_PAGES}
                            value={jumpInput}
                            onChange={(e) => setJumpInput(e.target.value)}
                            placeholder={`Go to Pagè`}
                            className="input-solid"
                        />
                        <button type="submit" className="btn-solid btn-solid-primary" style={{ borderRadius: '0 8px 8px 0', borderLeft: 0 }}>
                            <Search className="w-4 h-4 text-white" />
                        </button>
                    </form>
                    <a href={getPageUrl(rIdx || lIdx)} download={`Page-${rIdx || lIdx}.jpg`} className="btn-solid hidden md:flex items-center gap-2">
                        <Download className="w-5 h-5 text-slate-600" /> Save Image
                    </a>
                </div>
            </header>

            <main className="ebook-3d-scene">
                {/* Outboard Navigation Arrows */}
                <button onClick={() => triggerTurn('bck')} disabled={isCover || animState} className="nav-arrow-btn prev" aria-label="Previous">
                    <ArrowLeft className="w-10 h-10" />
                </button>
                <button onClick={() => triggerTurn('fwd')} disabled={isBackCover || animState} className="nav-arrow-btn next" aria-label="Next">
                    <ArrowRight className="w-10 h-10" />
                </button>

                <div className={`book-volume ${isCover ? 'is-cover' : ''} ${isBackCover ? 'is-back-cover' : ''}`}>
                    {!isCover && !isBackCover && <div className="book-spine" />}
                    
                    {/* Left Static Side */}
                    <div className="sheet left" style={{ opacity: isCover ? 0 : 1 }}>
                        {animState === 'bck' ? (
                            <img src={getPageUrl(getSpreadIndices(spread - 1).lIdx)} className="page-graphic" alt="" />
                        ) : (
                            lIdx && <img src={getPageUrl(lIdx)} className="page-graphic" alt={`Page ${lIdx}`} />
                        )}
                    </div>

                    {/* Right Static Side */}
                    <div className="sheet right" style={{ opacity: isBackCover ? 0 : 1 }}>
                        {animState === 'fwd' ? (
                            <img src={getPageUrl(getSpreadIndices(spread + 1).rIdx)} className="page-graphic" alt="" />
                        ) : (
                            rIdx && <img src={getPageUrl(rIdx)} className="page-graphic" alt={`Page ${rIdx}`} />
                        )}
                    </div>

                    {/* Animated Flipper */}
                    {animState && (
                        <div className={`turner turn-${animState}`}>
                            <div className="turner-side front">
                                {flipFaceA && <img src={getPageUrl(flipFaceA)} className="page-graphic" alt="" />}
                            </div>
                            <div className="turner-side back">
                                <div style={{ transform: 'scaleX(-1)', height: '100%' }}>
                                    {flipFaceB && <img src={getPageUrl(flipFaceB)} className="page-graphic" alt="" />}
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </main>

            <main className="mobile-view">
                {lIdx && <img src={getPageUrl(lIdx)} className="mobile-page" alt={`Page ${lIdx}`} />}
                {rIdx && <img src={getPageUrl(rIdx)} className="mobile-page" alt={`Page ${rIdx}`} />}
            </main>

            <footer className="ebook-bottombar">
                <div className="w-full max-w-4xl">
                    <div className="flex justify-between items-center text-xs font-bold text-slate-500 uppercase tracking-widest mb-2 px-1">
                        <span>Front Cover</span>
                        <span className="text-sky-600 font-extrabold">{completionPct}% Document Read</span>
                        <span>Back Cover</span>
                    </div>
                    <div className="progress-track-light">
                        <div className="progress-fill-light" style={{ width: `${completionPct}%` }} />
                    </div>
                </div>

                <div className="flex justify-between w-full max-w-4xl mt-4">
                    <button 
                        onClick={() => { setSpread(0); setAnimState(null); }}
                        disabled={isCover || animState}
                        className="btn-solid"
                    >
                        <ChevronsLeft className="w-5 h-5 text-slate-500" /> Start Over
                    </button>
                    
                    <div className="status-pill">
                        Spread {spread} of {TOTAL_SPREADS}
                    </div>

                    <button 
                        onClick={() => { setSpread(TOTAL_SPREADS); setAnimState(null); }}
                        disabled={isBackCover || animState}
                        className="btn-solid"
                    >
                        Skip to End <ChevronsRight className="w-5 h-5 text-slate-500" />
                    </button>
                </div>
            </footer>
        </div>
    );
}
