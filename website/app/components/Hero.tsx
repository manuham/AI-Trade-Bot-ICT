export default function Hero() {
  return (
    <section className="relative min-h-screen flex items-center justify-center text-center px-4 pt-20 overflow-hidden">
      {/* Background gradient effects */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[600px] bg-accent/10 rounded-full blur-[120px]" />
        <div className="absolute bottom-0 left-1/4 w-[400px] h-[400px] bg-accent/5 rounded-full blur-[100px]" />
      </div>

      <div className="relative z-10 max-w-3xl mx-auto animate-fade-in-up">
        {/* Badge */}
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-border bg-bg-card/50 text-text-secondary text-xs font-medium tracking-wide mb-8">
          <span className="w-2 h-2 rounded-full bg-green pulse-dot" />
          Powered by Claude AI &amp; ICT Methodology
        </div>

        {/* Headline */}
        <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold leading-tight mb-6 tracking-tight">
          AI-Powered Forex Signals
          <br />
          <span className="gradient-text">With Full Transparency</span>
        </h1>

        {/* Sub-headline */}
        <p className="text-text-secondary text-base sm:text-lg leading-relaxed mb-10 max-w-xl mx-auto">
          Every trade shown — wins{" "}
          <span className="text-green font-semibold">AND</span> losses. No
          cherry-picking. Our AI analyzes D1 to M5 structure using ICT
          methodology and delivers setups straight to your Telegram.
        </p>

        {/* CTA buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
          <a
            href="#waitlist"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-8 py-3.5 bg-accent hover:bg-accent-hover text-white font-semibold rounded-xl text-base no-underline transition-all duration-200 glow-accent"
          >
            Join Waitlist
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="mt-px">
              <path d="M3 8h10m0 0L9 4m4 4L9 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </a>
          <a
            href="#track-record"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-8 py-3.5 border border-border hover:border-border-light text-text-primary font-semibold rounded-xl text-base no-underline transition-all duration-200"
          >
            View Track Record
          </a>
        </div>

        {/* Trust indicators */}
        <div className="mt-12 flex flex-wrap justify-center gap-6 sm:gap-10 text-text-muted text-xs font-medium uppercase tracking-wider">
          <span>Multi-Pair Trading</span>
          <span className="hidden sm:inline text-border">|</span>
          <span>12-Point ICT Checklist</span>
          <span className="hidden sm:inline text-border">|</span>
          <span>M1 Entry Confirmation</span>
        </div>
      </div>
    </section>
  );
}
