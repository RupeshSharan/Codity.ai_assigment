import { useState } from "react";
import { api } from "../services/api";
import { KeyRound, Mail, User, Building, AlertCircle } from "lucide-react";

export function Auth({ onAuthSuccess }: { onAuthSuccess: (token: string) => void }) {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [orgName, setOrgName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (isLogin) {
        const res = await api.login({ email, password });
        localStorage.setItem("pulsequeue_token", res.access_token);
        onAuthSuccess(res.access_token);
      } else {
        const res = await api.register({
          email,
          password,
          full_name: fullName,
          organization_name: orgName
        });
        localStorage.setItem("pulsequeue_token", res.access_token);
        onAuthSuccess(res.access_token);
      }
    } catch (err: any) {
      setError(err.message || "Authentication failed. Please check your credentials.");
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = async () => {
    setError(null);
    setLoading(true);
    try {
      const res = await api.login({ email: "demo@pulsequeue.local", password: "password123" });
      localStorage.setItem("pulsequeue_token", res.access_token);
      onAuthSuccess(res.access_token);
    } catch (err: any) {
      setError("Demo credentials failed. Please make sure the database is seeded.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-mist px-4 py-12 sm:px-6 lg:px-8">
      <div className="w-full max-w-md space-y-8 rounded-lg border border-zinc-200 bg-white p-8 shadow-panel">
        <div>
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-md bg-pulse text-xl font-bold text-white shadow-sm">
            PQ
          </div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-ink">
            {isLogin ? "Sign in to PulseQueue" : "Create your account"}
          </h2>
          <p className="mt-2 text-center text-sm text-zinc-500">
            Or{" "}
            <button
              onClick={() => {
                setIsLogin(!isLogin);
                setError(null);
              }}
              className="font-medium text-pulse hover:underline"
            >
              {isLogin ? "start a free organization" : "sign in to your organization"}
            </button>
          </p>
        </div>

        {error && (
          <div className="flex items-center gap-3 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            <AlertCircle className="h-5 w-5 shrink-0 text-red-500" />
            <span>{error}</span>
          </div>
        )}

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="space-y-4">
            {!isLogin && (
              <>
                <div>
                  <label htmlFor="full-name" className="sr-only">
                    Full Name
                  </label>
                  <div className="relative">
                    <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                      <User className="h-5 w-5 text-zinc-400" />
                    </div>
                    <input
                      id="full-name"
                      name="name"
                      type="text"
                      required
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      className="block w-full rounded-md border border-zinc-300 py-3 pl-10 pr-3 text-sm text-ink placeholder-zinc-400 focus:border-pulse focus:outline-none focus:ring-1 focus:ring-pulse"
                      placeholder="Full Name"
                    />
                  </div>
                </div>

                <div>
                  <label htmlFor="org-name" className="sr-only">
                    Organization Name
                  </label>
                  <div className="relative">
                    <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                      <Building className="h-5 w-5 text-zinc-400" />
                    </div>
                    <input
                      id="org-name"
                      name="org"
                      type="text"
                      required
                      value={orgName}
                      onChange={(e) => setOrgName(e.target.value)}
                      className="block w-full rounded-md border border-zinc-300 py-3 pl-10 pr-3 text-sm text-ink placeholder-zinc-400 focus:border-pulse focus:outline-none focus:ring-1 focus:ring-pulse"
                      placeholder="Organization Name (e.g. Acme)"
                    />
                  </div>
                </div>
              </>
            )}

            <div>
              <label htmlFor="email-address" className="sr-only">
                Email address
              </label>
              <div className="relative">
                <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                  <Mail className="h-5 w-5 text-zinc-400" />
                </div>
                <input
                  id="email-address"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="block w-full rounded-md border border-zinc-300 py-3 pl-10 pr-3 text-sm text-ink placeholder-zinc-400 focus:border-pulse focus:outline-none focus:ring-1 focus:ring-pulse"
                  placeholder="Email address"
                />
              </div>
            </div>

            <div>
              <label htmlFor="password" className="sr-only">
                Password
              </label>
              <div className="relative">
                <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                  <KeyRound className="h-5 w-5 text-zinc-400" />
                </div>
                <input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="block w-full rounded-md border border-zinc-300 py-3 pl-10 pr-3 text-sm text-ink placeholder-zinc-400 focus:border-pulse focus:outline-none focus:ring-1 focus:ring-pulse"
                  placeholder="Password"
                />
              </div>
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={loading}
              className="flex w-full justify-center rounded-md bg-pulse py-3 text-sm font-semibold text-white shadow-sm hover:bg-pulse/90 focus:outline-none focus:ring-2 focus:ring-pulse focus:ring-offset-2 disabled:opacity-55"
            >
              {loading ? "Authenticating..." : isLogin ? "Sign In" : "Register"}
            </button>
          </div>
        </form>

        <div className="relative flex py-2 items-center">
          <div className="flex-grow border-t border-zinc-200"></div>
          <span className="flex-shrink mx-4 text-xs text-zinc-400 uppercase">Demo Access</span>
          <div className="flex-grow border-t border-zinc-200"></div>
        </div>

        <div>
          <button
            onClick={handleDemoLogin}
            disabled={loading}
            className="flex w-full justify-center rounded-md border border-zinc-200 bg-zinc-50 py-3 text-sm font-semibold text-zinc-700 shadow-sm hover:bg-zinc-100 focus:outline-none"
          >
            Quick Sandbox Login (demo@pulsequeue.local)
          </button>
        </div>
      </div>
    </div>
  );
}
