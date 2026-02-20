import Navigation from "./components/Navigation";
import Hero from "./components/Hero";
import SocialProof from "./components/SocialProof";
import LiveStats from "./components/LiveStats";
import EquityCurve from "./components/EquityCurve";
import HowItWorks from "./components/HowItWorks";
import WhyAIICT from "./components/WhyAIICT";
import TradeTable from "./components/TradeTable";
import Pricing from "./components/Pricing";
import Footer from "./components/Footer";
import JsonLd from "./components/JsonLd";

export default function Home() {
  return (
    <>
      <JsonLd />
      <Navigation />
      <main>
        <Hero />
        <SocialProof />
        <LiveStats />
        <EquityCurve />
        <HowItWorks />
        <WhyAIICT />
        <TradeTable />
        <Pricing />
      </main>
      <Footer />
    </>
  );
}
