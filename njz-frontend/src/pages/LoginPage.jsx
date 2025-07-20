import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Check, X as LucideX, AlertCircle } from 'lucide-react';

const Alert = ({ type = 'success', title, description, onClose }) => {
    const color = type === 'success' ? '#2b9875' : '#e53e3e';
    const Icon = type === 'success' ? Check : AlertCircle;

    return (
        <div className="fixed top-6 right-6 z-50 w-[200px] sm:w-[600px] text-[14px] sm:text-md">
            <div className="flex items-start justify-between w-full p-3 sm:p-4 rounded-xl bg-[#18181b] border border-[#23232b] shadow-md space-x-3">
                <div className="flex gap-3">
                    <div className="p-1 rounded-md bg-[#23232b] flex items-center justify-center" style={{ color }}>
                        <Icon className="w-5 h-5 sm:w-6 sm:h-6" />
                    </div>
                    <div className="text-left">
                        <p className="text-[#e5e7eb] font-semibold">{title}</p>
                        {description && <p className="text-[#a1a1aa]">{description}</p>}
                    </div>
                </div>
                <button
                    className="text-[#a1a1aa] hover:bg-[#23232b] p-1 rounded-md transition-colors"
                    onClick={onClose}
                >
                    <LucideX className="w-4 h-4 sm:w-5 sm:h-5" />
                </button>
            </div>
        </div>
    );
};


const LoginPage = () => {
    const navigate = useNavigate();
    const location = useLocation();
    const from = location.state?.from || '/';
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [mode, setMode] = useState('login'); // 'login' or 'signup'
    const [alert, setAlert] = useState(null); // { type, title, description }

    const handleSubmit = (e) => {
        e.preventDefault();
        // Simulate login/signup
        if (!email || !password) {
            setAlert({ type: 'error', title: 'Error', description: 'Email and password are required.' });
            return;
        }
        setTimeout(() => {
            setAlert({
                type: 'success',
                title: mode === 'login' ? 'Login Successful' : 'Signup Successful',
                description: mode === 'login' ? 'You have logged in successfully.' : 'Your account has been created.'
            });
            setTimeout(() => {
                navigate(from, { replace: true });
            }, 1200);
        }, 500);
    };

    return (
        <div className="fixed inset-0 flex items-center justify-center bg-[#18181b] px-4">
            {alert && (
                <Alert
                    type={alert.type}
                    title={alert.title}
                    description={alert.description}
                    onClose={() => setAlert(null)}
                />
            )}
            <div className="w-full max-w-md p-10 space-y-8 bg-[#23232b] border border-cyan-300 rounded-2xl shadow-2xl">
                <h2 className="text-3xl font-bold text-center text-white">
                    {mode === 'login' ? 'Welcome Back' : 'Create an Account'}
                </h2>
                <p className="text-center text-gray-400 text-sm">
                    {mode === 'login' ? 'Login to access your chat' : 'Sign up to start chatting'}
                </p>
                <form className="space-y-6" onSubmit={handleSubmit}>
                    <div>
                        <label htmlFor="email" className="block text-sm font-medium text-gray-300 mb-1">
                            Email
                        </label>
                        <input
                            id="email"
                            type="email"
                            autoComplete="email"
                            required
                            value={email}
                            onChange={e => setEmail(e.target.value)}
                            className="w-full px-4 py-2 rounded-md bg-[#18181b] border border-cyan-300 text-cyan-300 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-cyan-300 focus:border-cyan-300 transition"
                            placeholder="you@example.com"
                        />
                    </div>
                    <div>
                        <label htmlFor="password" className="block text-sm font-medium text-gray-300 mb-1">
                            Password
                        </label>
                        <input
                            id="password"
                            type="password"
                            autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                            required
                            value={password}
                            onChange={e => setPassword(e.target.value)}
                            className="w-full px-4 py-2 rounded-md bg-[#18181b] border border-cyan-300 text-cyan-300 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-cyan-300 focus:border-cyan-300 transition"
                            placeholder="••••••••"
                        />
                    </div>
                    <button
                        type="submit"
                        className="w-full py-2 px-4 text-cyan-300 border-2 border-cyan-300 rounded-md font-semibold bg-transparent hover:bg-cyan-300 hover:text-cyan-600 transition-colors duration-200"
                    >
                        {mode === 'login' ? 'Sign In' : 'Sign Up'}
                    </button>
                </form>
                <div className="flex items-center my-4">
                    <div className="flex-1 h-px bg-gray-700" />
                    <span className="mx-4 text-gray-500 text-xs uppercase tracking-widest">or</span>
                    <div className="flex-1 h-px bg-gray-700" />
                </div>
                <button
                    onClick={() => setMode(mode === 'login' ? 'signup' : 'login')}
                    className="w-full py-2 px-4 border-2 border-cyan-300 rounded-md font-semibold text-cyan-300 bg-transparent hover:bg-cyan-300 hover:text-cyan-600 transition-colors duration-200"
                >
                    {mode === 'login' ? 'Create an Account' : 'Already have an account? Sign In'}
                </button>
            </div>
        </div>
    );
};

export default LoginPage;
