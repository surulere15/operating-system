import { MarketingAgent } from './marketing-agent.js';

const agent = new MarketingAgent({ brand: 'wirebet.com' });
await agent.init();

// Generate crypto-native Twitter content
console.log('📱 Generating crypto-native content...');
const posts = await agent.generateContent({
  platform: 'twitter',
  topic: 'Premium wirebet.com domain for crypto prediction markets and event trading. One-word .com, instant category signal.',
  count: 7,
  style: 'thread',
});

for (const post of posts) {
  console.log('\n---');
  console.log(post.content);
  if (post.hashtags?.length) console.log('#' + post.hashtags.join(' #'));
  if (post.cta) console.log('CTA: ' + post.cta);
}

// Generate outreach for crypto-native targets
console.log('\n\n📧 Generating crypto-native outreach...');
const outreach = await agent.generateOutreach({
  targets: [
    { name: 'Shayne Coplan', company: 'Polymarket', role: 'CEO', niche: 'prediction markets' },
    { name: 'Tarek Mansour', company: 'Kalshi', role: 'CEO', niche: 'event markets' },
    { name: 'Hayden Adams', company: 'Uniswap', role: 'Founder', niche: 'DeFi' },
    { name: 'Stani Kulechov', company: 'Aave', role: 'CEO', niche: 'DeFi lending' },
    { name: 'Robert Leshner', company: 'Compound/Polymarket investor', role: 'Founder', niche: 'DeFi + prediction markets' },
  ],
  offer: 'wirebet.com — premium .com for prediction markets. Perfect for crypto-native event trading platforms.',
  channel: 'dm',
  sequences: 3,
});

for (const o of outreach) {
  console.log('\n→ ' + o.target.name + ' (' + o.target.company + '):');
  for (const step of o.sequence) {
    console.log('  Step ' + step.step + ': ' + (step.subject || step.body?.substring(0, 80)) + '...');
  }
}

// Create crypto-native affiliate program
console.log('\n\n💰 Creating crypto-native affiliate program...');
const program = await agent.createAffiliateProgram({
  commission: 15,
  payoutMethod: 'crypto (USDC/ETH)',
  tierCount: 3,
});
console.log('Affiliate tiers:', JSON.stringify(program?.tiers, null, 2));

console.log('\n✅ Crypto-native campaign complete!');
