import type { Metadata } from 'next';
import { getPublicSiteUrl } from '@/lib/site';
import {
  HomeNav,
  HeroEmpresa,
  QuemSomos,
  ProdutoQuarry,
  BarreirasDeCopia,
  ParaQuemE,
  StatGigante,
  CaminhoDuplo,
  DemoBanner,
  FaqHome,
  FooterHome,
} from '@/components/landing/home-pt/sections';

const siteUrl = getPublicSiteUrl();

export const metadata: Metadata = {
  title: { absolute: '12Brain — Quarry, SOC de IA auditável para fintechs BR' },
  description:
    'Quarry é o SOC agêntico auditável da 12Brain: investigação, Threat Ledger, AuditChain e camada BACEN/PIX/LGPD para fintechs brasileiras.',
  alternates: { canonical: '/' },
  openGraph: {
    title: '12Brain — Casa do Quarry',
    description:
      'SOC agêntico auditável para fintechs BR. Agentic SOC Engine, Threat Ledger, AuditChain, Brazil RegSec Pack e evidência defensável.',
    url: siteUrl,
    siteName: '12Brain',
    type: 'website',
    locale: 'pt_BR',
    images: [
      {
        url: '/og-image.svg',
        width: 1200,
        height: 630,
        alt: '12Brain Solutions — casa do Quarry',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: '12Brain — Casa do Quarry',
    description:
      'SOC agêntico auditável para fintechs BR. BACEN, PIX, LGPD e evidência defensável.',
    images: ['/og-image.svg'],
  },
};

const orgJsonLd = {
  '@context': 'https://schema.org',
  '@type': 'Organization',
  name: '12Brain Solutions LLC',
  alternateName: '12Brain',
  url: siteUrl,
  logo: `${siteUrl}/favicon.svg`,
  description:
    '12Brain Solutions é a empresa por trás do Quarry, um SOC agêntico MIT-licensed focado em fintechs brasileiras em estágio Seed e Série A.',
  address: {
    '@type': 'PostalAddress',
    streetAddress: '428 Plaza Real',
    addressLocality: 'Boca Raton',
    addressRegion: 'FL',
    addressCountry: 'US',
  },
  contactPoint: {
    '@type': 'ContactPoint',
    contactType: 'sales',
    email: 'contato@12brain.org',
  },
  sameAs: ['https://github.com/beenuar/Quarry'],
};

export default function HomePage() {
  return (
    <>
      <script
        type="application/ld+json"
        // eslint-disable-next-line react/no-danger -- JSON-LD payload for crawlers
        dangerouslySetInnerHTML={{ __html: JSON.stringify(orgJsonLd) }}
      />
      <main
        data-theme="dark"
        className="relative min-h-screen overflow-x-hidden bg-surface-base text-fg-primary"
      >
        <HomeNav />
        <HeroEmpresa />
        <QuemSomos />
        <ProdutoQuarry />
        <BarreirasDeCopia />
        <ParaQuemE />
        <StatGigante />
        <CaminhoDuplo />
        <DemoBanner />
        <FaqHome />
        <FooterHome />
      </main>
    </>
  );
}
