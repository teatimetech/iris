export default function Header() {
    return (
        <header className="glass-card border-b border-white/10 px-6 py-4">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                        <span className="text-xl font-bold">I</span>
                    </div>
                    <div>
                        <h1 className="text-xl font-bold text-gradient">IRIS</h1>
                        <p className="text-xs text-gray-400">Intelligent Risk-balanced Investment Strategist</p>
                    </div>
                </div>

                <div className="flex items-center gap-4">
                    <div className="text-right">
                        <p className="text-sm font-medium">Demo User</p>
                        <p className="text-xs text-gray-400">user@example.com</p>
                    </div>
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-pink-500 to-orange-500 flex items-center justify-center">
                        <span className="text-sm font-bold">DU</span>
                    </div>
                </div>
            </div>
        </header>
    )
}
