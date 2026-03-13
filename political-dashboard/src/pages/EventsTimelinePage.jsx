import React, { useState, useEffect } from 'react';
import { Calendar, TrendingUp, TrendingDown, ArrowRight, Activity, CalendarDays, Plus, Loader2, MessageSquareText } from 'lucide-react';
import api from '../api/api';

const EventsTimelinePage = () => {
    const [events, setEvents] = useState([]);
    const [selectedEventId, setSelectedEventId] = useState(null);
    const [shiftData, setShiftData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    const fetchEvents = async () => {
        try {
            const { data } = await api.get('/events/');
            setEvents(data);
            if (data.length > 0) {
                handleSelectEvent(data[0].id);
            }
        } catch (err) {
            console.error(err);
            // Dummy data fallback
            const dummyEvents = [
                { id: 1, name: "Union Budget Announcement", date: "2024-02-01", description: "Finance minister announces interim budget." },
                { id: 2, name: "State Assembly Elections Results", date: "2023-12-03", description: "Results for 4 major states declared." }
            ];
            setEvents(dummyEvents);
            handleSelectEvent(dummyEvents[0].id);
        } finally {
            setLoading(false);
        }
    };

    const handleSelectEvent = async (id) => {
        setSelectedEventId(id);
        setShiftData(null);
        try {
            const { data } = await api.get(`/events/${id}/discourse-shift?window_days=7`);
            setShiftData(data);
        } catch (err) {
            console.error(err);
            // Mock shift data
            setShiftData({
                window_days: 7,
                shifts: {
                    twitter: { volume_change: 15430, volume_pct_change: 45.2, sentiment_change: 0.12 },
                    reddit: { volume_change: 1200, volume_pct_change: 22.1, sentiment_change: -0.05 }
                },
                pre_event: { topics: [] },
                post_event: { topics: [] },
                calculated_impact_score: 8.5
            });
        }
    };

    useEffect(() => {
        fetchEvents();
    }, []);

    const MetricCard = ({ title, value, subtitle, trend, isPositive }) => (
        <div className="bg-white rounded-xl p-5 border border-gray-100 shadow-sm">
            <h3 className="text-gray-500 text-sm font-medium mb-1">{title}</h3>
            <div className="flex items-end gap-3">
                <span className="text-2xl font-bold text-gray-900">{value}</span>
                {trend != null && (
                    <div className={`flex items-center text-sm font-medium ${isPositive ? 'text-green-600' : 'text-red-500'}`}>
                        {isPositive ? <TrendingUp className="w-4 h-4 mr-1" /> : <TrendingDown className="w-4 h-4 mr-1" />}
                        {trend}
                    </div>
                )}
            </div>
            <p className="text-gray-400 text-xs mt-2">{subtitle}</p>
        </div>
    );

    const TopicCard = ({ topic }) => {
        const isPositive = topic.average_sentiment > 0;
        const isNeutral = topic.average_sentiment === 0;
        return (
            <div className="bg-white p-4 rounded-xl border border-gray-100 shadow-sm">
                <div className="flex justify-between items-start mb-2">
                    <h4 className="font-semibold text-gray-800 text-sm flex items-center gap-1.5">
                        <MessageSquareText className="w-4 h-4 text-indigo-500" />
                        {topic.topic_name}
                    </h4>
                    <span className={`text-xs font-bold px-2 py-1 rounded-full ${isNeutral ? 'bg-gray-100 text-gray-600' : isPositive ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                        {topic.average_sentiment > 0 ? '+' : ''}{topic.average_sentiment.toFixed(2)}
                    </span>
                </div>
                <div className="flex flex-wrap gap-1 mt-2">
                    {topic.keywords.slice(0, 4).map((kw, idx) => (
                        <span key={idx} className="px-2 py-0.5 text-[10px] font-medium bg-gray-50 text-gray-500 border border-gray-200 rounded-full">
                            {kw}
                        </span>
                    ))}
                </div>
            </div>
        )
    };

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center bg-white p-5 rounded-xl shadow-sm border border-gray-100">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 border-l-4 border-rose-500 pl-3">
                        Event-Driven Discourse
                    </h1>
                    <p className="text-gray-500 text-sm mt-1 ml-4">
                        Mapping sentiment & volume shocks corresponding to major political events.
                    </p>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                {/* Timeline / Event List Sidebar */}
                <div className="lg:col-span-1 bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden flex flex-col h-[600px]">
                    <div className="p-4 border-b border-gray-100 bg-gray-50 flex justify-between items-center">
                        <h2 className="font-semibold text-gray-800 flex items-center gap-2">
                            <CalendarDays className="w-4 h-4 text-rose-500" />
                            Political Events
                        </h2>
                    </div>
                    <div className="flex-1 overflow-y-auto p-2">
                        {loading && <div className="p-4 text-center text-gray-500"><Loader2 className="w-5 h-5 animate-spin mx-auto" /></div>}
                        {events.map((event) => (
                            <button
                                key={event.id}
                                onClick={() => handleSelectEvent(event.id)}
                                className={`w-full text-left p-4 rounded-lg mb-2 border transition-all ${selectedEventId === event.id
                                    ? 'border-rose-200 bg-rose-50 shadow-sm'
                                    : 'border-transparent hover:bg-gray-50 border-b-gray-100'
                                    }`}
                            >
                                <div className="flex items-center gap-2 text-xs font-semibold text-gray-500 mb-1">
                                    <Calendar className="w-3 h-3" />
                                    {event.date}
                                </div>
                                <h3 className={`font-medium text-sm ${selectedEventId === event.id ? 'text-rose-700' : 'text-gray-900'}`}>
                                    {event.name}
                                </h3>
                            </button>
                        ))}
                    </div>
                </div>

                {/* Event Details & Shift Data */}
                <div className="lg:col-span-3">
                    {!selectedEventId ? (
                        <div className="h-full flex items-center justify-center bg-white rounded-xl border border-gray-100">
                            <p className="text-gray-500">Select an event from the timeline to view analysis.</p>
                        </div>
                    ) : (
                        <div className="space-y-6">
                            {/* Selected Event Header */}
                            {events.map(ev => ev.id === selectedEventId && (
                                <div key={ev.id} className="bg-gradient-to-r from-gray-900 to-gray-800 rounded-xl p-6 text-white shadow-md relative overflow-hidden">
                                    <div className="absolute right-0 top-0 opacity-10 transform scale-150 -translate-y-10 translate-x-10">
                                        <Activity className="w-64 h-64" />
                                    </div>
                                    <div className="relative z-10">
                                        <div className="inline-flex items-center gap-2 px-3 py-1 bg-white/10 rounded-full text-xs font-semibold text-rose-200 mb-4 backdrop-blur-sm">
                                            <Calendar className="w-4 h-4" />
                                            {ev.date}
                                        </div>
                                        <h2 className="text-2xl font-bold mb-2">{ev.name}</h2>
                                        <p className="text-gray-300 max-w-2xl">{ev.description}</p>
                                    </div>
                                </div>
                            ))}

                            {/* Shift Data Metrics */}
                            {!shiftData ? (
                                <div className="p-10 text-center text-gray-400 bg-white rounded-xl border border-gray-100">
                                    <Loader2 className="w-8 h-8 animate-spin mx-auto mb-3" />
                                    Calculating Pre/Post Event Discorse Shift...
                                </div>
                            ) : (
                                <div className="space-y-6">
                                    <div>
                                        <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-4 px-1">
                                            Twitter / X Discourse Shift (±{shiftData.window_days} Days)
                                        </h3>
                                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                            <MetricCard
                                                title="Volume Spike"
                                                value={shiftData.shifts.twitter.volume_change > 0 ? `+${shiftData.shifts.twitter.volume_change.toLocaleString()}` : shiftData.shifts.twitter.volume_change.toLocaleString()}
                                                subtitle="Posts directly generated after event"
                                                trend={`${shiftData.shifts.twitter.volume_pct_change}%`}
                                                isPositive={shiftData.shifts.twitter.volume_change > 0}
                                            />
                                            <MetricCard
                                                title="Sentiment Shift"
                                                value={shiftData.shifts.twitter.sentiment_change > 0 ? `+${shiftData.shifts.twitter.sentiment_change}` : shiftData.shifts.twitter.sentiment_change}
                                                subtitle="Overall mood shift compared to pre-event"
                                                trend={null}
                                                isPositive={shiftData.shifts.twitter.sentiment_change > 0}
                                            />
                                            <MetricCard
                                                title="Impact Rating"
                                                value={`${shiftData.calculated_impact_score}/10`}
                                                subtitle="Derived from volume and sentiment swings"
                                                trend={null}
                                                isPositive={true}
                                            />
                                        </div>
                                    </div>

                                    <div>
                                        <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-4 px-1">
                                            Reddit Discourse Shift (±{shiftData.window_days} Days)
                                        </h3>
                                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                            <MetricCard
                                                title="Volume Change"
                                                value={shiftData.shifts.reddit.volume_change > 0 ? `+${shiftData.shifts.reddit.volume_change.toLocaleString()}` : shiftData.shifts.reddit.volume_change.toLocaleString()}
                                                subtitle="Discussion threads/comments offset"
                                                trend={`${shiftData.shifts.reddit.volume_pct_change}%`}
                                                isPositive={shiftData.shifts.reddit.volume_change >= 0}
                                            />
                                            <MetricCard
                                                title="Sentiment Shift"
                                                value={shiftData.shifts.reddit.sentiment_change > 0 ? `+${shiftData.shifts.reddit.sentiment_change}` : shiftData.shifts.reddit.sentiment_change}
                                                subtitle="Mood directional change"
                                                trend={null}
                                                isPositive={shiftData.shifts.reddit.sentiment_change > 0}
                                            />
                                        </div>
                                    </div>

                                    {/* Topics Section */}
                                    {(shiftData.pre_event?.topics?.length > 0 || shiftData.post_event?.topics?.length > 0) && (
                                        <div>
                                            <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mt-8 mb-4 px-1">
                                                Topical Shifts & Sentiment Context
                                            </h3>
                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 bg-gray-50 p-6 rounded-xl border border-gray-100">
                                                <div>
                                                    <h4 className="text-sm font-medium text-gray-700 mb-3 flex items-center">
                                                        <Calendar className="w-4 h-4 mr-2" /> Pre-Event Topics
                                                    </h4>
                                                    <div className="space-y-3">
                                                        {shiftData.pre_event.topics.length === 0 ? (
                                                            <p className="text-xs text-gray-400">No topics detected.</p>
                                                        ) : (
                                                            shiftData.pre_event.topics.map((t, i) => <TopicCard key={i} topic={t} />)
                                                        )}
                                                    </div>
                                                </div>
                                                <div>
                                                    <h4 className="text-sm font-medium text-gray-700 mb-3 flex items-center">
                                                        <Activity className="w-4 h-4 mr-2" /> Post-Event Topics
                                                    </h4>
                                                    <div className="space-y-3">
                                                        {shiftData.post_event.topics.length === 0 ? (
                                                            <p className="text-xs text-gray-400">No topics detected.</p>
                                                        ) : (
                                                            shiftData.post_event.topics.map((t, i) => <TopicCard key={i} topic={t} />)
                                                        )}
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default EventsTimelinePage;
