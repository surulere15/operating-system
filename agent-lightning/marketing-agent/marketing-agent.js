/**
 * OpenClaw Marketing Agent
 * Autonomous marketing system inspired by Head AI.
 * 
 * Features:
 *   - Brand DNA generation from URL
 *   - Influencer/creator discovery & outreach
 *   - Cold email campaigns
 *   - Campaign tracking & analytics
 *   - Affiliate/referral management
 *   - Social media content generation
 * 
 * Usage:
 *   import { MarketingAgent } from './marketing-agent.js';
 *   const agent = new MarketingAgent({ brand: 'wirebet.com' });
 *   await agent.init();
 *   await agent.runCampaign('domain-sale');
 */

import { readFile, writeFile, mkdir } from 'fs/promises';
import { join, dirname } from 'path';
import { homedir } from 'os';
import { fileURLToPath } from 'url';
import { SessionStore } from '../modules/session-store.js';
import { OpenClawAgent } from '../modules/integration.js';

const __dirname = dirname(fileURLToPath(import.meta.url));

export class MarketingAgent {
  constructor(config = {}) {
    this.config = {
      brand: config.brand || 'wirebet.com',
      brandUrl: config.brandUrl || `https://${config.brand || 'wirebet.com'}`,
      workspace: config.workspace || join(homedir(), '.openclaw', 'workspace'),
      dataPath: config.dataPath || join(__dirname, 'data'),
      campaignsPath: config.campaignsPath || join(__dirname, 'campaigns'),
      templatesPath: config.templatesPath || join(__dirname, 'templates'),
      ...config,
    };

    this.agent = new OpenClawAgent();
    this.store = new SessionStore(this.config.dataPath);
    this.brandDNA = null;
    this.campaigns = new Map();
  }

  /**
   * Initialize the marketing agent
   */
  async init() {
    await this.agent.init();
    await this.store.init();
    await mkdir(this.config.dataPath, { recursive: true });
    await mkdir(this.config.campaignsPath, { recursive: true });
    
    // Load existing brand DNA
    try {
      const data = await readFile(join(this.config.dataPath, 'brand-dna.json'), 'utf-8');
      this.brandDNA = JSON.parse(data);
    } catch {
      // No brand DNA yet
    }

    console.log('[MarketingAgent] Initialized for:', this.config.brand);
  }

  // ═══════════════════════════════════════════════
  // BRAND DNA
  // ═══════════════════════════════════════════════

  /**
   * Generate brand DNA from URL
   * Scrapes the site and extracts brand voice, positioning, target audience
   */
  async generateBrandDNA(url = null) {
    const targetUrl = url || this.config.brandUrl;
    console.log('[MarketingAgent] Generating brand DNA from:', targetUrl);

    // Use the AI agent to analyze the site
    const result = await this.agent.run(
      `Analyze the website at ${targetUrl} and extract a Brand DNA profile. 
      
      Return a JSON object with these fields:
      {
        "name": "brand name",
        "tagline": "one-line description",
        "voice": ["adjective1", "adjective2", "adjective3"],
        "targetAudience": ["segment1", "segment2"],
        "valueProps": ["prop1", "prop2", "prop3"],
        "competitors": ["comp1", "comp2"],
        "keywords": ["kw1", "kw2", "kw3"],
        "tone": "formal|casual|technical|premium",
        "category": "industry category",
        "uniqueSellingPoint": "what makes it different"
      }
      
      Return ONLY valid JSON, no explanation.`,
      { model: 'openai/gpt-4o-mini' }
    );

    try {
      // Extract JSON from response
      const jsonMatch = result.content.match(/\{[\s\S]*\}/);
      this.brandDNA = JSON.parse(jsonMatch[0]);
      
      // Save to disk
      await writeFile(
        join(this.config.dataPath, 'brand-dna.json'),
        JSON.stringify(this.brandDNA, null, 2)
      );

      console.log('[MarketingAgent] Brand DNA generated:', this.brandDNA.name);
      return this.brandDNA;
    } catch (err) {
      console.error('[MarketingAgent] Failed to parse brand DNA:', err.message);
      return null;
    }
  }

  // ═══════════════════════════════════════════════
  // INFLUENCER DISCOVERY
  // ═══════════════════════════════════════════════

  /**
   * Discover influencers/creators in a niche
   * @param {Object} params
   * @param {string} params.niche - Target niche (e.g., "crypto prediction markets")
   * @param {string[]} params.platforms - Platforms to search (twitter, youtube, tiktok)
   * @param {number} params.minFollowers - Minimum follower count
   * @param {number} params.limit - Max creators to find
   */
  async discoverInfluencers(params = {}) {
    const {
      niche = this.brandDNA?.category || 'crypto',
      platforms = ['twitter'],
      minFollowers = 1000,
      limit = 20,
    } = params;

    console.log('[MarketingAgent] Discovering influencers in:', niche);

    const result = await this.agent.run(
      `Find ${limit} influencers/creators in the "${niche}" space on ${platforms.join(', ')}.
      
      For each creator, provide:
      {
        "name": "display name",
        "handle": "@username",
        "platform": "twitter|youtube|tiktok",
        "followers": estimated_count,
        "engagement": "high|medium|low",
        "content_type": "what they post about",
        "relevance": 0-10 score for ${niche}
      }
      
      Return a JSON array. Only include creators with ${minFollowers}+ followers.
      Focus on creators who cover prediction markets, crypto trading, or DeFi.`,
      { model: 'openai/gpt-4o' }
    );

    try {
      const jsonMatch = result.content.match(/\[[\s\S]*\]/);
      const influencers = JSON.parse(jsonMatch[0]);
      
      // Save to disk
      await writeFile(
        join(this.config.dataPath, 'influencers.json'),
        JSON.stringify(influencers, null, 2)
      );

      console.log(`[MarketingAgent] Found ${influencers.length} influencers`);
      return influencers;
    } catch (err) {
      console.error('[MarketingAgent] Failed to parse influencers:', err.message);
      return [];
    }
  }

  // ═══════════════════════════════════════════════
  // COLD OUTREACH
  // ═══════════════════════════════════════════════

  /**
   * Generate personalized outreach messages
   * @param {Object} params
   * @param {Object[]} params.targets - List of targets with name, company, role
   * @param {string} params.offer - What you're offering
   * @param {string} params.channel - 'email' | 'dm' | 'linkedin'
   * @param {number} params.sequences - Number of follow-up sequences
   */
  async generateOutreach(params = {}) {
    const {
      targets = [],
      offer = 'premium domain for sale',
      channel = 'dm',
      sequences = 3,
    } = params;

    if (!this.brandDNA) {
      await this.generateBrandDNA();
    }

    console.log(`[MarketingAgent] Generating ${sequences}-step ${channel} sequence for ${targets.length} targets`);

    const messages = [];

    for (const target of targets) {
      const result = await this.agent.run(
        `Generate a ${sequences}-step ${channel} outreach sequence for:
        
        Target: ${target.name || 'Unknown'} at ${target.company || 'Unknown'}
        Role: ${target.role || 'Decision maker'}
        Offer: ${offer}
        Brand: ${this.brandDNA?.name || this.config.brand}
        Tagline: ${this.brandDNA?.tagline || ''}
        Value Props: ${this.brandDNA?.valueProps?.join(', ') || ''}
        
        Rules:
        - Step 1: Initial outreach (2-3 sentences, personalized)
        - Step 2: Follow-up after 3 days (add value, no pressure)
        - Step 3: Final follow-up after 7 days (urgency, scarcity)
        - Each step should have: subject (if email), body, cta
        - Tone: ${this.brandDNA?.tone || 'professional'}
        - No generic templates — personalize to the target
        
        Return JSON array of ${sequences} steps.`,
        { model: 'openai/gpt-4o-mini' }
      );

      try {
        const jsonMatch = result.content.match(/\[[\s\S]*\]/);
        const sequence = JSON.parse(jsonMatch[0]);
        messages.push({ target, sequence });
      } catch {
        messages.push({ target, sequence: [{ body: result.content }] });
      }
    }

    // Save campaign
    const campaignId = `outreach_${Date.now()}`;
    await writeFile(
      join(this.config.campaignsPath, `${campaignId}.json`),
      JSON.stringify({ id: campaignId, channel, offer, targets: messages, createdAt: new Date().toISOString() }, null, 2)
    );

    console.log(`[MarketingAgent] Generated outreach for ${messages.length} targets`);
    return messages;
  }

  // ═══════════════════════════════════════════════
  // SOCIAL CONTENT
  // ═══════════════════════════════════════════════

  /**
   * Generate social media content
   * @param {Object} params
   * @param {string} params.platform - 'twitter' | 'linkedin' | 'instagram'
   * @param {string} params.topic - Content topic
   * @param {number} params.count - Number of posts to generate
   * @param {string} params.style - 'thread' | 'single' | 'carousel'
   */
  async generateContent(params = {}) {
    const {
      platform = 'twitter',
      topic = this.brandDNA?.tagline || this.config.brand,
      count = 5,
      style = 'single',
    } = params;

    if (!this.brandDNA) {
      await this.generateBrandDNA();
    }

    console.log(`[MarketingAgent] Generating ${count} ${platform} posts about: ${topic}`);

    const result = await this.agent.run(
      `Generate ${count} ${platform} posts about: ${topic}
      
      Brand context:
      - Name: ${this.brandDNA?.name || this.config.brand}
      - Tagline: ${this.brandDNA?.tagline || ''}
      - Voice: ${this.brandDNA?.voice?.join(', ') || 'professional'}
      - Keywords: ${this.brandDNA?.keywords?.join(', ') || ''}
      
      Style: ${style}
      Platform: ${platform}
      
      Rules:
      - Each post should be unique
      - Include relevant hashtags
      - ${platform === 'twitter' ? 'Max 280 chars per post' : 'Can be longer'}
      - ${style === 'thread' ? 'Number them 1/N, 2/N, etc.' : 'Each post standalone'}
      - Include a call-to-action in at least 2 posts
      
      Return JSON array: [{"content": "...", "hashtags": ["..."], "cta": "..."}]`,
      { model: 'openai/gpt-4o-mini' }
    );

    try {
      const jsonMatch = result.content.match(/\[[\s\S]*\]/);
      const posts = JSON.parse(jsonMatch[0]);
      
      await writeFile(
        join(this.config.campaignsPath, `content_${platform}_${Date.now()}.json`),
        JSON.stringify({ platform, topic, style, posts, createdAt: new Date().toISOString() }, null, 2)
      );

      console.log(`[MarketingAgent] Generated ${posts.length} posts`);
      return posts;
    } catch (err) {
      console.error('[MarketingAgent] Failed to parse content:', err.message);
      return [];
    }
  }

  // ═══════════════════════════════════════════════
  // AFFILIATE / REFERRAL
  // ═══════════════════════════════════════════════

  /**
   * Generate affiliate/referral program structure
   * @param {Object} params
   * @param {number} params.commission - Commission percentage
   * @param {string} params.payoutMethod - 'crypto' | 'bank' | 'paypal'
   * @param {number} params.tierCount - Number of tiers
   */
  async createAffiliateProgram(params = {}) {
    const {
      commission = 10,
      payoutMethod = 'crypto',
      tierCount = 3,
    } = params;

    if (!this.brandDNA) {
      await this.generateBrandDNA();
    }

    console.log(`[MarketingAgent] Creating affiliate program: ${commission}% commission`);

    const result = await this.agent.run(
      `Design an affiliate/referral program for:
      
      Brand: ${this.brandDNA?.name || this.config.brand}
      Product: ${this.brandDNA?.tagline || 'Premium domain sale'}
      Base commission: ${commission}%
      Payout method: ${payoutMethod}
      Tiers: ${tierCount}
      
      Create:
      1. Tier structure (Bronze/Silver/Gold or similar)
      2. Commission rates per tier
      3. Requirements to advance tiers
      4. Referral link format
      5. Payout schedule
      6. Terms & conditions summary
      7. Outreach message for potential affiliates
      
      Return JSON with all program details.`,
      { model: 'openai/gpt-4o-mini' }
    );

    try {
      const jsonMatch = result.content.match(/\{[\s\S]*\}/);
      const program = JSON.parse(jsonMatch[0]);
      
      await writeFile(
        join(this.config.dataPath, 'affiliate-program.json'),
        JSON.stringify(program, null, 2)
      );

      console.log('[MarketingAgent] Affiliate program created');
      return program;
    } catch (err) {
      console.error('[MarketingAgent] Failed to parse program:', err.message);
      return null;
    }
  }

  // ═══════════════════════════════════════════════
  // CAMPAIGN RUNNER
  // ═══════════════════════════════════════════════

  /**
   * Run a complete marketing campaign
   * @param {string} campaignType - 'domain-sale' | 'product-launch' | 'growth'
   */
  async runCampaign(campaignType = 'domain-sale') {
    console.log(`[MarketingAgent] Running campaign: ${campaignType}`);

    const results = {};

    // Step 1: Generate brand DNA if missing
    if (!this.brandDNA) {
      results.brandDNA = await this.generateBrandDNA();
    }

    // Step 2: Generate content
    results.content = await this.generateContent({
      platform: 'twitter',
      count: 5,
      style: 'thread',
    });

    // Step 3: Generate outreach for key targets
    if (campaignType === 'domain-sale') {
      results.outreach = await this.generateOutreach({
        targets: [
          { name: 'Shayne Coplan', company: 'Polymarket', role: 'CEO' },
          { name: 'Tarek Mansour', company: 'Kalshi', role: 'CEO' },
          { name: 'James', company: 'Manifold Markets', role: 'Co-founder' },
        ],
        offer: 'Premium wirebet.com domain for prediction markets',
        channel: 'dm',
        sequences: 3,
      });
    }

    // Step 4: Create affiliate program
    results.affiliate = await this.createAffiliateProgram({
      commission: 10,
      payoutMethod: 'crypto',
    });

    // Save campaign summary
    const campaignId = `campaign_${campaignType}_${Date.now()}`;
    await writeFile(
      join(this.config.campaignsPath, `${campaignId}.json`),
      JSON.stringify({ id: campaignId, type: campaignType, results, createdAt: new Date().toISOString() }, null, 2)
    );

    console.log(`[MarketingAgent] Campaign ${campaignId} complete`);
    return results;
  }

  /**
   * Get campaign analytics
   */
  async getCampaignStats() {
    const sessions = await this.store.list();
    const campaigns = [];
    
    try {
      const { readdir } = await import('fs/promises');
      const files = await readdir(this.config.campaignsPath);
      for (const f of files) {
        if (f.endsWith('.json')) {
          const data = JSON.parse(await readFile(join(this.config.campaignsPath, f), 'utf-8'));
          campaigns.push(data);
        }
      }
    } catch {}

    return {
      totalCampaigns: campaigns.length,
      sessions: sessions.length,
      brandDNA: this.brandDNA ? 'generated' : 'not generated',
    };
  }
}

export default MarketingAgent;
