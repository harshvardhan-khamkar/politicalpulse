import React, { useState, useEffect, useRef } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';

const slides = [
    { type: 'countdown' },
    {
        type: 'image',
        image: 'https://images.unsplash.com/photo-1585829365295-ab7cd400c167?q=80&w=2070&auto=format&fit=crop',
        caption: 'Democracy in Action',
        sub: 'Millions of votes shaping the future of the nation.',
    },
    {
        type: 'image',
        image: 'https://images.unsplash.com/photo-1529107386315-e1a2ed48a620?q=80&w=2070&auto=format&fit=crop',
        caption: 'Your Vote Matters',
        sub: 'Every single vote counts in building a stronger democracy.',
    },
    {
        type: 'image',
        image: 'https://images.unsplash.com/photo-1541872703-74c59636a2fd?q=80&w=2062&auto=format&fit=crop',
        caption: 'A Nation Decides',
        sub: 'Follow the live election coverage and results here.',
    },
];

const CountdownTimer = () => {
    const [timeLeft, setTimeLeft] = useState({ days: '02', hours: '00', minutes: '00', seconds: '00' });

    useEffect(() => {
        const timer = setInterval(() => {
            const now = new Date();
            setTimeLeft({
                days: '02',
                hours: String(23 - now.getHours()).padStart(2, '0'),
                minutes: String(59 - now.getMinutes()).padStart(2, '0'),
                seconds: String(59 - now.getSeconds()).padStart(2, '0'),
            });
        }, 1000);
        return () => clearInterval(timer);
    }, []);

    const units = [
        { label: 'Days', value: timeLeft.days },
        { label: 'Hours', value: timeLeft.hours },
        { label: 'Minutes', value: timeLeft.minutes },
        { label: 'Seconds', value: timeLeft.seconds },
    ];

    return (
        <div className="relative w-full h-full rounded-2xl overflow-hidden text-white">
            {/* Background */}
            <div
                className="absolute inset-0 bg-cover bg-center"
                style={{ backgroundImage: 'url("https://images.unsplash.com/photo-1532375810709-75b1da00537c?q=80&w=2076&auto=format&fit=crop")' }}
            />
            <div className="absolute inset-0 bg-gradient-to-r from-black/85 via-black/60 to-black/40" />

            <div className="relative h-full flex flex-col justify-center px-10 pt-6 space-y-6">
                <div>
                    <h1 className="text-4xl font-bold leading-tight">
                        Indian General Elections <br />
                        <span className="text-orange-400">2025</span>
                    </h1>
                </div>

                <div>
                    <p className="text-xs text-gray-300 uppercase tracking-widest mb-3 font-semibold">Election Starts In</p>
                    <div className="flex items-center gap-4">
                        {units.map((u, i) => (
                            <React.Fragment key={u.label}>
                                <div className="text-center">
                                    <div className="bg-white/10 backdrop-blur-md border border-white/20 rounded-xl px-4 py-2">
                                        <div className="text-3xl font-bold font-mono tabular-nums">{u.value}</div>
                                    </div>
                                    <div className="text-[10px] text-gray-400 uppercase mt-1">{u.label}</div>
                                </div>
                                {i < units.length - 1 && (
                                    <div className="text-2xl font-light text-gray-500 mb-4">:</div>
                                )}
                            </React.Fragment>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};

const ImageSlide = ({ image, caption, sub }) => (
    <div className="relative w-full h-full rounded-2xl overflow-hidden text-white">
        <div
            className="absolute inset-0 bg-cover bg-center transition-all duration-700"
            style={{ backgroundImage: `url("${image}")` }}
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/30 to-transparent" />
        <div className="relative h-full flex flex-col justify-end px-10 pb-10">
            <h2 className="text-3xl font-bold leading-tight">{caption}</h2>
            <p className="text-gray-300 mt-2 text-sm max-w-md">{sub}</p>
        </div>
    </div>
);

const CountdownCarousel = () => {
    const [current, setCurrent] = useState(0);
    const timerRef = useRef(null);

    const startAutoSlide = () => {
        clearInterval(timerRef.current);
        timerRef.current = setInterval(() => {
            setCurrent(prev => (prev + 1) % slides.length);
        }, 5000);
    };

    useEffect(() => {
        startAutoSlide();
        return () => clearInterval(timerRef.current);
    }, []);

    const goTo = (index) => {
        setCurrent(index);
        startAutoSlide();
    };

    const prev = () => goTo((current - 1 + slides.length) % slides.length);
    const next = () => goTo((current + 1) % slides.length);

    const slide = slides[current];

    return (
        <div className="relative w-full h-64 rounded-2xl overflow-hidden shadow-2xl group">
            {/* Slides */}
            <div className="w-full h-full transition-all duration-500 ease-in-out">
                {slide.type === 'countdown' ? (
                    <CountdownTimer />
                ) : (
                    <ImageSlide {...slide} />
                )}
            </div>

            {/* Left Arrow */}
            <button
                onClick={prev}
                className="absolute left-3 top-1/2 -translate-y-1/2 bg-black/40 hover:bg-black/70 text-white rounded-full p-1.5 opacity-0 group-hover:opacity-100 transition-opacity z-10"
                aria-label="Previous"
            >
                <ChevronLeft className="w-5 h-5" />
            </button>

            {/* Right Arrow */}
            <button
                onClick={next}
                className="absolute right-3 top-1/2 -translate-y-1/2 bg-black/40 hover:bg-black/70 text-white rounded-full p-1.5 opacity-0 group-hover:opacity-100 transition-opacity z-10"
                aria-label="Next"
            >
                <ChevronRight className="w-5 h-5" />
            </button>

            {/* Navigation Dots */}
            <div className="absolute bottom-3 left-1/2 -translate-x-1/2 flex gap-2 z-10">
                {slides.map((_, i) => (
                    <button
                        key={i}
                        onClick={() => goTo(i)}
                        className={`rounded-full transition-all duration-300 ${i === current
                            ? 'bg-white w-5 h-2'
                            : 'bg-white/50 w-2 h-2 hover:bg-white/80'
                            }`}
                        aria-label={`Slide ${i + 1}`}
                    />
                ))}
            </div>
        </div>
    );
};

export default CountdownCarousel;
