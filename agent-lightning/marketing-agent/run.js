/**
 * Marketing Agent CLI
 * Run autonomous marketing campaigns from the command line.
 * 
 * Usage:
 *   node run.js --brand wirebet.com --campaign domain-sale
 *   node run.js --brand wirebet.com --generate-dna
 *   node run.js --brand wirebet.com --discover "crypto prediction markets"
 *   node run.js --brand wirebet.com --content twitter 5
 *   node run.js --brand wirebet.com --outreach targets.json
 */

import { MarketingAgent } from './marketing-agent.js';
import { readFile } from 'fs/promises';

const args = process.argv.slice(2);
const flags = {};

for (let i = 0; i < args.length; i++) {
  if (args[i].startsWith('--')) {
    const key = args[i].slice(2);
    const val = args[i + 1] && !args[i + 1].startsWith('--') ? args[i + 1] : true;
    flags[key] = val;
    if (val !== true) i++;
  }
}

async function main() {
  const brand = flags.brand || 'wirebet.com';
  const agent = new MarketingAgent({ brand });
  await agent.init();

  console.log(`\n⚡ Marketing Agent — ${brand}\n`);

  // Generate Brand DNA
  if (flags['generate-dna'] || flags.dna) {
    const dna = await agent.generateBrandDNA();
    console.log('\n📋 Brand DNA:');
    console.log(JSON.stringify(dna, null, 2));
    return;
  }

  // Discover influencers
  if (flags.discover) {
    const influencers = await agent.discoverInfluencers({
      niche: flags.discover,
      limit: parseInt(flags.limit) || 20,
    });
    console.log(`\n👥 Found ${influencers.length} influencers:`);
    for (const inf of influencers.slice(0, 10)) {
      console.log(`  ${inf.handle} — ${inf.followers?.toLocaleString()} followers (${inf.engagement} engagement)`);
    }
    return;
  }

  // Generate content
  if (flags.content) {
    const platform = flags.content;
    const count = parseInt(args[args.indexOf(flags.content) + 1]) || 5;
    const posts = await agent.generateContent({ platform, count });
    console.log(`\n📱 Generated ${posts.length} ${platform} posts:`);
    for (const post of posts) {
      console.log(`\n---\n${post.content}`);
      if (post.hashtags?.length) console.log(`#${post.hashtags.join(' #')}`);
    }
    return;
  }

  // Generate outreach
  if (flags.outreach) {
    let targets;
    try {
      const data = await readFile(flags.outreach, 'utf-8');
      targets = JSON.parse(data);
    } catch {
      // Default targets for domain sale
      targets = [
        { name: 'Shayne Coplan', company: 'Polymarket', role: 'CEO' },
        { name: 'Tarek Mansour', company: 'Kalshi', role: 'CEO' },
        { name: 'James', company: 'Manifold Markets', role: 'Co-founder' },
        { name: 'Robin Hanson', company: 'Metaculus', role: 'Founder' },
      ];
    }
    const outreach = await agent.generateOutreach({ targets, offer: `Premium ${brand} domain` });
    console.log(`\n📧 Generated outreach for ${outreach.length} targets`);
    for (const o of outreach) {
      console.log(`\n→ ${o.target.name} (${o.target.company}):`);
      for (const step of o.sequence) {
        console.log(`  Step: ${step.subject || step.body?.substring(0, 60)}...`);
      }
    }
    return;
  }

  // Affiliate program
  if (flags.affiliate) {
    const program = await agent.createAffiliateProgram({
      commission: parseInt(flags.commission) || 10,
    });
    console.log('\n💰 Affiliate Program:');
    console.log(JSON.stringify(program, null, 2));
    return;
  }

  // Run full campaign
  if (flags.campaign) {
    const results = await agent.runCampaign(flags.campaign);
    console.log('\n✅ Campaign complete!');
    console.log(`  Brand DNA: ${results.brandDNA ? 'Generated' : 'Existing'}`);
    console.log(`  Content: ${results.content?.length || 0} posts`);
    console.log(`  Outreach: ${results.outreach?.length || 0} targets`);
    console.log(`  Affiliate: ${results.affiliate ? 'Created' : 'Failed'}`);
    return;
  }

  // Stats
  if (flags.stats) {
    const stats = await agent.getCampaignStats();
    console.log('\n📊 Stats:', JSON.stringify(stats, null, 2));
    return;
  }

  // Default: show help
  console.log(`
Usage:
  node run.js --brand wirebet.com --campaign domain-sale
  node run.js --brand wirebet.com --generate-dna
  node run.js --brand wirebet.com --discover "crypto prediction markets"
  node run.js --brand wirebet.com --content twitter 5
  node run.js --brand wirebet.com --outreach [targets.json]
  node run.js --brand wirebet.com --affiliate
  node run.js --brand wirebet.com --stats
  `);
}

main().catch(console.error);
