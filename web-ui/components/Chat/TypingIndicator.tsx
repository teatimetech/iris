export default function TypingIndicator() {
    return (
        <div className="flex justify-start animate-slide-up">
            <div className="glass-card rounded-2xl px-4 py-3">
                <div className="flex items-center gap-1">
                    <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
                    <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse delay-75" />
                    <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse delay-150" />
                    <span className="ml-2 text-xs text-gray-400">IRIS is thinking...</span>
                </div>
            </div>
        </div>
    )
}
