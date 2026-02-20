import AnimatedSection from "./AnimatedSection";

const steps = [
  {
    number: "01",
    title: "AI Multi-Timeframe Analysis",
    description:
      "Every session, Claude AI scans D1, H4, H1 and M5 charts — screening for ICT setups with institutional-grade precision across multiple pairs.",
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        <path d="M9 12l2 2 4-4" />
      </svg>
    ),
  },
  {
    number: "02",
    title: "12-Point ICT Checklist",
    description:
      "Each setup is scored against 12 ICT criteria: bias alignment, order blocks, FVGs, market structure shifts, OTE zones, liquidity sweeps, and R:R targets.",
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2" />
        <rect x="9" y="3" width="6" height="4" rx="2" />
        <path d="M9 14l2 2 4-4" />
      </svg>
    ),
  },
  {
    number: "03",
    title: "Smart Zone Entry",
    description:
      "High-scoring setups are automatically watched. When price reaches the entry zone, a separate AI confirms on the M1 chart before executing the trade.",
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10" />
        <circle cx="12" cy="12" r="6" />
        <circle cx="12" cy="12" r="2" />
      </svg>
    ),
  },
];

export default function HowItWorks() {
  return (
    <section id="how-it-works" className="py-20 px-4 bg-bg-secondary">
      <div className="max-w-5xl mx-auto">
        {/* Section header */}
        <AnimatedSection className="text-center mb-14">
          <p className="text-accent text-xs font-semibold uppercase tracking-widest mb-3">
            How It Works
          </p>
          <h2 className="text-2xl sm:text-3xl font-bold mb-3">
            Three Layers of Intelligence
          </h2>
          <p className="text-text-secondary text-sm sm:text-base max-w-lg mx-auto">
            From multi-timeframe analysis to precision entry — every step is automated and transparent.
          </p>
        </AnimatedSection>

        {/* Step cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {steps.map((step, i) => (
            <AnimatedSection key={i} delay={i * 0.15}>
              <div className="bg-bg-card border border-border rounded-xl p-8 card-hover h-full">
                {/* Icon */}
                <div className="w-12 h-12 rounded-lg bg-accent-glow flex items-center justify-center text-accent-light mb-5">
                  {step.icon}
                </div>

                {/* Step number */}
                <div className="text-accent text-xs font-bold tracking-widest mb-2">
                  STEP {step.number}
                </div>

                {/* Title */}
                <h3 className="text-lg font-semibold mb-3 text-text-primary">
                  {step.title}
                </h3>

                {/* Description */}
                <p className="text-text-secondary text-sm leading-relaxed">
                  {step.description}
                </p>
              </div>
            </AnimatedSection>
          ))}
        </div>
      </div>
    </section>
  );
}
