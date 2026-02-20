import AnimatedSection from "./AnimatedSection";

const reasons = [
  {
    title: "Never Sleeps, Never Misses",
    description:
      "Human traders miss setups during sleep, meals, or busy days. Our AI monitors every session for every active pair — no setup goes unnoticed.",
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7z" />
        <circle cx="12" cy="12" r="3" />
      </svg>
    ),
  },
  {
    title: "Zero Emotional Bias",
    description:
      "Fear, greed, revenge trading — humans are wired to make emotional decisions. Our AI evaluates every setup against the same rigorous 12-point checklist, every single time.",
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 2a4 4 0 014 4v2a4 4 0 01-8 0V6a4 4 0 014-4z" />
        <path d="M16 14v4a4 4 0 01-8 0v-4" />
        <path d="M12 18v4M8 22h8" />
      </svg>
    ),
  },
  {
    title: "Institutional Methodology",
    description:
      "ICT concepts decoded by AI — order blocks, fair value gaps, market structure shifts, OTE zones. The same framework used by institutional traders, now automated.",
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <rect x="2" y="7" width="20" height="14" rx="2" ry="2" />
        <path d="M16 3h-8l-2 4h12z" />
        <path d="M12 11v4M10 13h4" />
      </svg>
    ),
  },
  {
    title: "Learns From Every Trade",
    description:
      "After each closed position, the AI reviews what worked and what didn't. These insights feed into the next analysis — a continuous learning loop that improves over time.",
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.66 0 3-4.03 3-9s-1.34-9-3-9m0 18c-1.66 0-3-4.03-3-9s1.34-9 3-9" />
      </svg>
    ),
  },
];

export default function WhyAIICT() {
  return (
    <section className="py-20 px-4 bg-bg-secondary">
      <div className="max-w-5xl mx-auto">
        {/* Section header */}
        <AnimatedSection className="text-center mb-14">
          <p className="text-accent text-xs font-semibold uppercase tracking-widest mb-3">
            Why AI + ICT?
          </p>
          <h2 className="text-2xl sm:text-3xl font-bold mb-3">
            The Edge You&apos;ve Been Looking For
          </h2>
          <p className="text-text-secondary text-sm sm:text-base max-w-lg mx-auto">
            Combining the most powerful AI model with proven institutional trading methodology.
          </p>
        </AnimatedSection>

        {/* Reasons grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          {reasons.map((reason, i) => (
            <AnimatedSection key={i} delay={i * 0.1}>
              <div className="bg-bg-card border border-border rounded-xl p-7 h-full card-hover">
                <div className="w-11 h-11 rounded-lg bg-accent-glow flex items-center justify-center text-accent-light mb-5">
                  {reason.icon}
                </div>
                <h3 className="text-base font-semibold mb-2 text-text-primary">
                  {reason.title}
                </h3>
                <p className="text-text-secondary text-sm leading-relaxed">
                  {reason.description}
                </p>
              </div>
            </AnimatedSection>
          ))}
        </div>
      </div>
    </section>
  );
}
