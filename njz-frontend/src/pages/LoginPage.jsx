import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Check, X as LucideX, AlertCircle } from 'lucide-react';
import axios from 'axios';

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
    const [username, setUsername] = useState('');
    const [firstName, setFirstName] = useState('');
    const [lastName, setLastName] = useState('');
    const [password, setPassword] = useState('');
    const [password2, setPassword2] = useState('');
    const [mode, setMode] = useState('login'); // 'login' or 'signup'
    const [alert, setAlert] = useState(null); // { type, title, description }

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (mode === 'signup') {
            if (!username || !email || !firstName || !lastName || !password || !password2) {
                setAlert({ type: 'error', title: 'Error', description: 'All fields are required.' });
                return;
            }
            if (password !== password2) {
                setAlert({ type: 'error', title: 'Error', description: 'Passwords do not match.' });
                return;
            }
            try {
                const response = await axios.post('http://localhost:8000/api/auth/register/', {
                    username,
                    email,
                    first_name: firstName,
                    last_name: lastName,
                    password,
                    password2
                });
                const { tokens } = response.data.data;
                localStorage.setItem('accessToken', tokens.access);
                localStorage.setItem('refreshToken', tokens.refresh);
                setAlert({
                    type: 'success',
                    title: 'Signup Successful',
                    description: 'Your account has been created.'
                });
                setTimeout(() => {
                    navigate(from, { replace: true });
                }, 1200);
            } catch (error) {
                let description = 'Registration failed.';
                if (error.response?.data?.errors) {
                    description = Object.values(error.response.data.errors).join(' ');
                } else if (error.response?.data?.message) {
                    description = error.response.data.message;
                }
                setAlert({
                    type: 'error',
                    title: 'Signup Failed',
                    description
                });
            }
            return;
        }
        // LOGIN MODE
        if (!username || !password) {
            setAlert({ type: 'error', title: 'Error', description: 'Username and password are required.' });
            return;
        }
        try {
            const response = await axios.post('http://localhost:8000/api/auth/login/', {
                username: username,
                password: password
            });
            const { tokens } = response.data.data;
            localStorage.setItem('accessToken', tokens.access);
            localStorage.setItem('refreshToken', tokens.refresh);
            setAlert({
                type: 'success',
                title: 'Login Successful',
                description: 'You have logged in successfully.'
            });
            setTimeout(() => {
                navigate(from, { replace: true });
            }, 1200);
        } catch (error) {
            setAlert({
                type: 'error',
                title: 'Login Failed',
                description: error.response?.data?.message || 'Invalid credentials or server error.'
            });
        }
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
                    {mode === 'login' && (
                        <div>
                            <label htmlFor="username" className="block text-sm font-medium text-gray-300 mb-1">
                                Username
                            </label>
                            <input
                                id="username"
                                type="text"
                                autoComplete="username"
                                required
                                value={username}
                                onChange={e => setUsername(e.target.value)}
                                className="w-full px-4 py-2 rounded-md bg-[#18181b] border border-cyan-300 text-cyan-300 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-cyan-300 focus:border-cyan-300 transition"
                                placeholder="yourusername"
                            />
                        </div>
                    )}
                    {mode === 'signup' && (
                        <>
                            <div>
                                <label htmlFor="username" className="block text-sm font-medium text-gray-300 mb-1">
                                    Username
                                </label>
                                <input
                                    id="username"
                                    type="text"
                                    autoComplete="username"
                                    required
                                    value={username}
                                    onChange={e => setUsername(e.target.value)}
                                    className="w-full px-4 py-2 rounded-md bg-[#18181b] border border-cyan-300 text-cyan-300 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-cyan-300 focus:border-cyan-300 transition"
                                    placeholder="yourusername"
                                />
                            </div>
                            <div>
                                <label htmlFor="firstName" className="block text-sm font-medium text-gray-300 mb-1">
                                    First Name
                                </label>
                                <input
                                    id="firstName"
                                    type="text"
                                    required
                                    value={firstName}
                                    onChange={e => setFirstName(e.target.value)}
                                    className="w-full px-4 py-2 rounded-md bg-[#18181b] border border-cyan-300 text-cyan-300 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-cyan-300 focus:border-cyan-300 transition"
                                    placeholder="First Name"
                                />
                            </div>
                            <div>
                                <label htmlFor="lastName" className="block text-sm font-medium text-gray-300 mb-1">
                                    Last Name
                                </label>
                                <input
                                    id="lastName"
                                    type="text"
                                    required
                                    value={lastName}
                                    onChange={e => setLastName(e.target.value)}
                                    className="w-full px-4 py-2 rounded-md bg-[#18181b] border border-cyan-300 text-cyan-300 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-cyan-300 focus:border-cyan-300 transition"
                                    placeholder="Last Name"
                                />
                            </div>
                        </>
                    )}
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
                    {mode === 'signup' ? (
                        <>
                            <div>
                                <label htmlFor="password" className="block text-sm font-medium text-gray-300 mb-1">
                                    Password
                                </label>
                                <input
                                    id="password"
                                    type="password"
                                    autoComplete="current-password"
                                    required
                                    value={password}
                                    onChange={e => setPassword(e.target.value)}
                                    className="w-full px-4 py-2 rounded-md bg-[#18181b] border border-cyan-300 text-cyan-300 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-cyan-300 focus:border-cyan-300 transition"
                                    placeholder="••••••••"
                                />
                            </div>
                            <div>
                                <label htmlFor="password2" className="block text-sm font-medium text-gray-300 mb-1">
                                    Confirm Password
                                </label>
                                <input
                                    id="password2"
                                    type="password"
                                    required
                                    value={password2}
                                    onChange={e => setPassword2(e.target.value)}
                                    className="w-full px-4 py-2 rounded-md bg-[#18181b] border border-cyan-300 text-cyan-300 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-cyan-300 focus:border-cyan-300 transition"
                                    placeholder="••••••••"
                                />
                            </div>
                        </>
                    ) : (
                        <div>
                            <label htmlFor="password" className="block text-sm font-medium text-gray-300 mb-1">
                                Password
                            </label>
                            <input
                                id="password"
                                type="password"
                                autoComplete="current-password"
                                required
                                value={password}
                                onChange={e => setPassword(e.target.value)}
                                className="w-full px-4 py-2 rounded-md bg-[#18181b] border border-cyan-300 text-cyan-300 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-cyan-300 focus:border-cyan-300 transition"
                                placeholder="••••••••"
                            />
                        </div>
                    )}
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
