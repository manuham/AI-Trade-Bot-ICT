import WaitlistForm from "./WaitlistForm";
import AnimatedSection from "./AnimatedSection";

const tiers = [
  {
    name: "Free",
    price: "$0",
    period: "forever",
    description: "See what the AI finds — delayed by 1 day.",
    features: [
      "Public trade history (24h delay)",
      "Weekly performance reports",
      "Telegram community access",
    ],
    highlight: false,
    cta: "Current Plan",
    ctaLink: "#stats",
  },
  {
    name: "Starter",
    price: "$29",
    period: "/month",
    description: "Real-time signals for one pair.",
    features: [
      "Live trade signals via Telegram",
      "Real-time entry, SL & TP levels",
      "ICT analysis breakdown",
      "Email support",
    ],
    highlight: false,
    cta: "Join Waitlist",
    ctaLink: "#waitlist",
  },
  {
    name: "Pro",
    price: "$79",
    period: "/month",
    description: "All pairs + full analysis access.",
    features: [
      "All currency pairs (as added)",
      "Full ICT checklist with reasoning",
      "Chart screenshots & annotations",
      "Priority Telegram group",
      "Monthly PDF reports",
    ],
    highlight: true,
    cta: "Join Waitlist",
    ctaLink: "#waitlist",
  },
  {
    name: "Enterprise",
    price: "$199",
    period: "/month",
    description: "API access + custom configuration.",
    features: [
      "Everything in Pro",
      "REST API access for your systems",
      "Custom pair selection",
      "Custom risk parameters",
      "1-on-1 onboarding call",
    ],
    highlight: false,
    cta: "Join Waitlist",
    ctaLink: "#waitlist",
  },
];

export default function Pricing() {
  return (
    <section id="pricing" className="py-20 px-4 bg-bg-secondary">
      <div className="max-w-6xl mx-auto">
        {/* Section header */}
        <AnimatedSection className="text-center mb-14">
          <p className="text-accent text-xs font-semibold uppercase tracking-widest mb-3">
            Pricing
          </p>
          <h2 className="text-2xl sm:text-3xl font-bold mb-3">
            Simple, Transparent Plans
          </h2>
          <p className="text-text-secondary text-sm sm:text-base">
            Launching soon — join the waitlist to lock in early-bird pricing.
          </p>
        </AnimatedSection>

        {/* Tier cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mb-16">
          {tiers.map((tier, i) => (
            <AnimatedSection key={tier.name} delay={i * 0.1}>
              <div
                className={`relative bg-bg-card rounded-xl p-7 flex flex-col h-full card-hover ${
                  tier.highlight
                    ? "border-2 border-accent glow-accent"
                    : "border border-border"
                }`}
              >
                {/* Popular badge */}
                {tier.highlight && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-accent text-white text-[10px] font-bold px-3 py-1 rounded-full uppercase tracking-wider">
                    Most Popular
                  </div>
                )}

                {/* Tier name */}
                <h3 className="text-base font-semibold mb-1 text-text-primary">
                  {tier.name}
                </h3>

                {/* Price */}
                <div className="mb-4">
                  <span className="text-3xl font-bold text-text-primary">
                    {tier.price}
                  </span>
                  <span className="text-text-muted text-sm ml-1">
                    {tier.period}
                  </span>
                </div>

                {/* Description */}
                <p className="text-text-secondary text-sm leading-relaxed mb-5">
                  {tier.description}
                </p>

                {/* Features */}
                <ul className="flex-1 space-y-2.5 mb-6">
                  {tier.features.map((f) => (
                    <li key={f} className="flex items-start gap-2.5 text-sm text-text-secondary">
                      <svg className="w-4 h-4 text-green mt-0.5 shrink-0" viewBox="0 0 16 16" fill="none">
                        <path d="M3 8l3.5 3.5L13 5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      </svg>
                      {f}
                    </li>
                  ))}
                </ul>

                {/* CTA button */}
                <a
                  href={tier.ctaLink}
                  className={`block text-center py-2.5 rounded-lg font-semibold text-sm no-underline transition-all duration-200 ${
                    tier.highlight
                      ? "bg-accent hover:bg-accent-hover text-white"
                      : tier.cta === "Current Plan"
                        ? "border border-border text-text-muted cursor-default"
                        : "border border-border text-text-secondary hover:border-accent hover:text-accent-light"
                  }`}
                >
                  {tier.cta}
                </a>
              </div>
            </AnimatedSection>
          ))}
        </div>

        {/* Waitlist section */}
        <AnimatedSection className="text-center mb-6">
          <h3 className="text-xl font-semibold mb-2 text-text-primary">
            Get Notified When We Launch
          </h3>
          <p className="text-text-secondary text-sm mb-6">
            Be the first to know — no spam, just launch updates.
          </p>
        </AnimatedSection>
        <WaitlistForm />
      </div>
    </section>
  );
}
