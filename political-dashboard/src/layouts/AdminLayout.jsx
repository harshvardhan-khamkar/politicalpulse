import React from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import {
    LayoutDashboard,
    ClipboardList,
    Megaphone,
    Settings2,
    ChevronLeft,
    ShieldCheck,
} from 'lucide-react';
import AdminRoute from '../components/AdminRoute';

// ─── Sidebar nav items ────────────────────────────────────────────────────────

const NAV_ITEMS = [
    { to: '/admin', icon: LayoutDashboard, label: 'Dashboard', end: true },
    { to: '/admin/polls', icon: ClipboardList, label: 'Poll Management' },
    { to: '/admin/parties', icon: Megaphone, label: 'Party Management' },
    { to: '/admin/system', icon: Settings2, label: 'System Controls' },
];

// ─── Admin Sidebar ────────────────────────────────────────────────────────────

const AdminSidebar = () => {
    const navigate = useNavigate();

    return (
        <aside className="h-screen w-60 bg-gray-950 flex flex-col fixed left-0 top-0 z-50 select-none">
            {/* Brand */}
            <div className="px-5 py-5 border-b border-gray-800">
                <div className="flex items-center gap-2.5 mb-1">
                    <div className="w-7 h-7 rounded-md bg-blue-600 flex items-center justify-center flex-shrink-0">
                        <ShieldCheck className="w-4 h-4 text-white" />
                    </div>
                    <span className="text-white font-bold text-sm tracking-wide">Admin Panel</span>
                </div>
                <p className="text-gray-500 text-[10px] pl-9 uppercase tracking-widest">Control Centre</p>
            </div>

            {/* Nav */}
            <nav className="flex-1 px-3 py-4 overflow-y-auto space-y-1">
                {NAV_ITEMS.map(({ to, icon: Icon, label, end }) => (
                    <NavLink
                        key={to}
                        to={to}
                        end={end}
                        className={({ isActive }) =>
                            `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150
                            ${isActive
                                ? 'bg-blue-600 text-white shadow-sm shadow-blue-900'
                                : 'text-gray-400 hover:text-white hover:bg-gray-800'
                            }`
                        }
                    >
                        <Icon className="w-4 h-4 flex-shrink-0" />
                        {label}
                    </NavLink>
                ))}
            </nav>

            {/* Back to site */}
            <div className="px-3 py-4 border-t border-gray-800">
                <button
                    onClick={() => navigate('/')}
                    className="flex items-center gap-2 px-3 py-2.5 w-full rounded-lg text-sm font-medium text-gray-500 hover:text-white hover:bg-gray-800 transition-all"
                >
                    <ChevronLeft className="w-4 h-4" />
                    Back to Site
                </button>
            </div>
        </aside>
    );
};

// ─── Layout ───────────────────────────────────────────────────────────────────

const AdminLayout = () => (
    <AdminRoute>
        <div className="min-h-screen bg-gray-50 flex">
            <AdminSidebar />
            {/* Main content offset by sidebar width */}
            <main className="flex-1 ml-60 p-8 overflow-y-auto min-h-screen">
                <Outlet />
            </main>
        </div>
    </AdminRoute>
);

export default AdminLayout;
