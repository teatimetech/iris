import React from 'react';

export default function Footer() {
    return (
        <footer className="w-full py-6 px-4 border-t border-white/10 bg-black/20 backdrop-blur-md mt-auto">
            <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4 text-xs text-gray-500">
                <div className="flex items-center gap-2">
                    <span className="font-bold text-gray-300">IRIS</span>
                    <span>© {new Date().getFullYear()} All rights reserved.</span>
                </div>
                <div className="flex gap-6">
                    <a href="/privacy" className="hover:text-white transition-colors">Privacy Policy</a>
                    <a href="/terms" className="hover:text-white transition-colors">Terms of Service</a>
                    <a href="#" className="hover:text-white transition-colors">Contact Support</a>
                </div>
            </div>
        </footer>
    );
}
