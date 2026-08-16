import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { authApi, errMsg } from "../lib/api";
import { useAuth } from "../lib/auth";

export default function Register() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const res = await authApi.register(name, email, password);
      login(res.access_token, res.user);
      navigate("/");
    } catch (e) {
      setError(errMsg(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-gradient-to-br from-ink-950 via-ink-900 to-indigo-950">
      <div className="w-full max-w-md">
        <div className="flex items-center gap-3 mb-8 justify-center">
          <div className="w-10 h-10 rounded-xl bg-indigo-500 flex items-center justify-center">
            <svg className="w-6 h-6 text-white" viewBox="0 0 32 32" fill="none">
              <path d="M7 22 L13 14 L18 19 L25 9" stroke="currentColor" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
          <div>
            <div className="text-xl font-bold text-white">InsightIQ</div>
            <div className="text-xs text-slate-400">AI Business Intelligence</div>
          </div>
        </div>
        <div className="card p-7">
          <h1 className="text-lg font-semibold text-slate-100 mb-1">Create your account</h1>
          <p className="text-sm text-slate-500 mb-5">Get started in seconds — upload data and ask questions.</p>
          <form onSubmit={submit} className="space-y-4">
            <div>
              <label className="label">Name</label>
              <input className="input" value={name} onChange={(e) => setName(e.target.value)} required />
            </div>
            <div>
              <label className="label">Email</label>
              <input className="input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
            </div>
            <div>
              <label className="label">Password</label>
              <input className="input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} minLength={6} required />
            </div>
            {error && <div className="text-sm text-rose-400">{error}</div>}
            <button className="btn-primary w-full" disabled={busy}>
              {busy ? "Creating…" : "Sign up"}
            </button>
          </form>
          <p className="text-sm text-slate-500 mt-5 text-center">
            Already have an account?{" "}
            <Link to="/login" className="text-indigo-400 hover:text-indigo-300 font-medium">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
