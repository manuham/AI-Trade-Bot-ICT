const footerLinks = [
  { label: "Live Stats", href: "#stats" },
  { label: "How It Works", href: "#how-it-works" },
  { label: "Track Record", href: "#track-record" },
  { label: "Pricing", href: "#pricing" },
];

export default function Footer() {
  return (
    <footer className="border-t border-border py-12 px-4">
      <div className="max-w-5xl mx-auto">
        {/* Top row */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-6 mb-8">
          {/* Logo */}
          <a href="#" className="flex items-center gap-2.5 no-underline">
            <div className="w-7 h-7 rounded-md bg-accent flex items-center justify-center text-white font-bold text-xs">
              ICT
            </div>
            <span className="text-text-primary font-semibold text-sm">
              AI Trade Bot
            </span>
          </a>

          {/* Links */}
          <div className="flex items-center gap-6 flex-wrap justify-center">
            {footerLinks.map((link) => (
              <a
                key={link.href}
                href={link.href}
                className="text-text-muted text-sm no-underline hover:text-text-secondary transition-colors duration-200"
              >
                {link.label}
              </a>
            ))}
            <a
              href="https://t.me/ict_trade_ai_bot"
              target="_blank"
              rel="noopener noreferrer"
              className="text-text-muted text-sm no-underline hover:text-text-secondary transition-colors duration-200"
            >
              Telegram
            </a>
          </div>
        </div>

        {/* Divider */}
        <div className="border-t border-border/50 pt-8">
          {/* Disclaimer */}
          <p className="text-text-muted text-xs leading-relaxed max-w-2xl mx-auto text-center mb-4">
            Trading forex involves significant risk. Past performance does not guarantee
            future results. AI Trade Bot ICT provides analysis, not financial advice.
            Always do your own research and never trade with money you cannot afford to lose.
          </p>

          {/* Copyright */}
          <p className="text-center text-text-muted/50 text-xs">
            &copy; {new Date().getFullYear()} AI Trade Bot ICT. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
}
