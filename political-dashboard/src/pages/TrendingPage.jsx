import React from 'react';
import TrendingHashtagsWidget from '../components/dashboard/TrendingHashtagsWidget';
import { TrendingUp } from 'lucide-react';

const TrendingPage = () => {
    return (
        <div className="space-y-6">
            <div className="flex items-center gap-3">
                <div className="p-2 bg-gradient-to-br from-pink-500 to-rose-600 rounded-lg shadow-sm">
                    <TrendingUp className="w-5 h-5 text-white" />
                </div>
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Trending Topics</h1>
                    <p className="text-sm text-gray-500 mt-1">
                        Real-time political pulse and hashtag momentum across social platforms.
                    </p>
                </div>
            </div>

            <div className="max-w-4xl mx-auto mt-8">
                {/* Notice we do not pass compact=true here, so it gets the full UI */}
                <TrendingHashtagsWidget className="w-full" />
            </div>
        </div>
    );
};

export default TrendingPage;
