export default function JsonLd() {
  const structuredData = {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    name: "AI Trade Bot ICT",
    applicationCategory: "FinanceApplication",
    description:
      "AI-powered forex trading signals using ICT methodology. Multi-pair analysis with 12-point checklist scoring and full trade transparency.",
    operatingSystem: "Web",
    offers: [
      {
        "@type": "Offer",
        price: "0",
        priceCurrency: "USD",
        name: "Free",
        description: "Public trade history with 24h delay",
      },
      {
        "@type": "Offer",
        price: "29",
        priceCurrency: "USD",
        name: "Starter",
        description: "Real-time signals for one pair",
      },
      {
        "@type": "Offer",
        price: "79",
        priceCurrency: "USD",
        name: "Pro",
        description: "All pairs with full analysis access",
      },
      {
        "@type": "Offer",
        price: "199",
        priceCurrency: "USD",
        name: "Enterprise",
        description: "API access with custom configuration",
      },
    ],
  };

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData) }}
    />
  );
}
