import { Footer } from '../components/marketing/Footer'
import { IntroReveal } from '../components/marketing/IntroReveal'
import { ScrollProgress } from '../components/marketing/ScrollProgress'
import { SiteNav } from '../components/marketing/SiteNav'
import { AgentsSection } from '../components/marketing/sections/AgentsSection'
import { FinalCTA } from '../components/marketing/sections/FinalCTA'
import { GuardrailsSection } from '../components/marketing/sections/GuardrailsSection'
import { Hero } from '../components/marketing/sections/Hero'
import { HowItWorks } from '../components/marketing/sections/HowItWorks'
import { HumanInLoop } from '../components/marketing/sections/HumanInLoop'
import { Problem } from '../components/marketing/sections/Problem'
import { TrustSection } from '../components/marketing/sections/TrustSection'
import { UnderTheHood } from '../components/marketing/sections/UnderTheHood'
import { WhatIsNiriksh } from '../components/marketing/sections/WhatIsNiriksh'

export function LandingPage() {
  return (
    <div className="relative">
      <IntroReveal />
      <ScrollProgress />
      <SiteNav />
      <Hero />
      <Problem />
      <WhatIsNiriksh />
      <HowItWorks />
      <AgentsSection />
      <UnderTheHood />
      <HumanInLoop />
      <GuardrailsSection />
      <TrustSection />
      <FinalCTA />
      <Footer />
    </div>
  )
}
