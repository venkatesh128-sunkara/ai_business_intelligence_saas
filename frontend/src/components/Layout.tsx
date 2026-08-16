import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../lib/auth";

const nav = [
  { to: "/", label: "Overview", icon: "M3 12l9-9 9 9M5 10v10h14V10" },
  { to: "/datasets", label: "Datasets", icon: "M4 7h16M4 12h16M4 17h16" },
  { to: "/ask", label: "Ask AI", icon: "M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" },
  { to: "/insights", label: "Insights", icon: "M13 2L3 14h9l-1 8 10-12h-9l1-8z" },
  { to: "/dashboards", label: "Dashboards", icon: "M3 3h18v18H3zM3 9h18M9 21V9" },
];

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex">
      <aside className="w-60 shrink-0 bg-ink-900 border-r border-slate-800 flex flex-col fixed inset-y-0">
        <div className="px-5 py-5 flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-lg bg-indigo-500 flex items-center justify-center">
            <svg className="w-5 h-5 text-white" viewBox="0 0 32 32" fill="none">
              <path d="M7 22 L13 14 L18 19 L25 9" stroke="currentColor" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
          <div>
            <div className="font-bold text-slate-100 leading-tight">InsightIQ</div>
            <div className="text-[11px] text-slate-500">AI Business Intelligence</div>
          </div>
        </div>
        <nav className="flex-1 px-3 py-2 space-y-1">
          {nav.map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              end={n.to === "/"}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive ? "bg-indigo-500/15 text-indigo-300" : "text-slate-400 hover:bg-slate-800 hover:text-slate-200"
                }`
              }
            >
              <svg className="w-4.5 h-4.5 w-[18px] h-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d={n.icon} />
              </svg>
              {n.label}
            </NavLink>
          ))}
          {user?.role === "admin" && (
            <NavLink
              to="/admin"
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive ? "bg-indigo-500/15 text-indigo-300" : "text-slate-400 hover:bg-slate-800 hover:text-slate-200"
                }`
              }
            >
              <svg className="w-[18px] h-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 15a3 3 0 100-6 3 3 0 000 6zm0 0v3m-9-3h3M3 9h3m6-6v3M9 3h6" />
              </svg>
              Admin
            </NavLink>
          )}
        </nav>
        <div className="p-3 border-t border-slate-800">
          <div className="flex items-center gap-3 px-2 py-2">
            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white text-sm font-bold uppercase">
              {user?.name?.[0] ?? "?"}
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium text-slate-200 truncate">{user?.name}</div>
              <div className="text-[11px] text-slate-500 truncate">{user?.email}</div>
            </div>
            <button
              onClick={() => {
                logout();
                navigate("/login");
              }}
              title="Sign out"
              className="text-slate-500 hover:text-rose-400"
            >
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9" />
              </svg>
            </button>
          </div>
        </div>
      </aside>
      <main className="flex-1 ml-60 p-8">
        <Outlet />
      </main>
    </div>
  );
}
