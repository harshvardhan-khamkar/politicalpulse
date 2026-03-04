import React from 'react';
import { NavLink, Link } from 'react-router-dom';
import {
    Search,
    BarChart2,
    PieChart,
    Vote,
    Settings,
    HelpCircle,
    LogIn,
    Megaphone,
    ClipboardList,
    Globe,
    MapPin,
    LineChart,
    ShieldCheck
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

const Sidebar = () => {
    const { isAdmin } = useAuth();
    const sections = [
        {
            title: "Account",
            items: [
                { to: '/login', icon: LogIn, label: 'Login / Signup' },
            ]
        },
        {
            title: "Analytics",
            items: [
                { to: '/', icon: BarChart2, label: 'Leaderboard' },
                { to: '/analytics', icon: PieChart, label: 'Insights' },
                { to: '/party-info', icon: Megaphone, label: 'Party Information' },
            ]
        },
        {
            title: "Election Data",
            items: [
                { to: '/election-results', icon: Vote, label: 'Election Results' },
                { to: '/election-charts', icon: LineChart, label: 'Visualizations' },
            ]
        },
        {
            title: "Polls",
            items: [
                { to: '/polls', icon: ClipboardList, label: 'Polls' },
                { to: '/poll-results', icon: BarChart2, label: 'Poll Results' },
            ]
        },
        {
            title: "News",
            items: [
                { to: '/news/global', icon: Globe, label: 'Global News' },
                { to: '/news/local', icon: MapPin, label: 'Local News' },
            ]
        },
        {
            title: "Others",
            items: [
                { to: '/settings', icon: Settings, label: 'Settings' },
                { to: '/support', icon: HelpCircle, label: 'Support' },
                ...(isAdmin ? [{ to: '/admin', icon: ShieldCheck, label: 'Admin Panel' }] : []),
            ]
        }
    ];

    return (
        <div className="h-screen w-64 bg-white border-r border-gray-200 flex flex-col fixed left-0 top-0 overflow-y-auto z-50">
            {/* Search Section */}
            <div className="p-6 pb-2">
                <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input
                        type="text"
                        placeholder="Search"
                        className="w-full pl-9 pr-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-gray-50"
                    />
                </div>
            </div>

            {/* Navigation Sections */}
            <div className="flex-1 px-4 py-2 space-y-6">
                {sections.map((section, idx) => (
                    <div key={idx}>
                        {section.title && (
                            <h3 className="px-3 mb-2 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                                {section.title}
                            </h3>
                        )}
                        <ul className="space-y-1">
                            {section.items.map((item) => (
                                <li key={item.label}>
                                    {item.to === '/login' ? (
                                        <button
                                            onClick={() => window.location.href = '/login'}
                                            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors text-gray-600 hover:bg-gray-50 hover:text-gray-900 border-none bg-transparent cursor-pointer text-left"
                                        >
                                            <item.icon className="w-5 h-5" />
                                            {item.label}
                                        </button>
                                    ) : (
                                        <NavLink
                                            to={item.to}
                                            className={({ isActive }) =>
                                                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${isActive
                                                    ? 'bg-blue-50 text-blue-600'
                                                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                                                }`
                                            }
                                        >
                                            <item.icon className="w-5 h-5" />
                                            {item.label}
                                        </NavLink>
                                    )}
                                </li>
                            ))}
                        </ul>
                    </div>
                ))}
            </div>
        </div >
    );
};

export default Sidebar;
