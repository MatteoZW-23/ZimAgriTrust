const http = require('http');
const { URL } = require('url');

const ZIMBABWE_AGRI_CATALOG = [
  { id: 'staple-maize', name: 'Maize', category: 'Field Crops', unit: 'Metric Tonne' },
  { id: 'staple-sorghum', name: 'Sorghum', category: 'Field Crops', unit: 'Metric Tonne' },
  { id: 'staple-wheat', name: 'Wheat', category: 'Field Crops', unit: 'Metric Tonne' },
  { id: 'cash-tobacco', name: 'Tobacco (Gold Leaf)', category: 'Cash Crops', unit: 'Kilogram' },
  { id: 'cash-cotton', name: 'Cotton', category: 'Cash Crops', unit: 'Kilogram' },
  { id: 'cash-soyabeans', name: 'Soya Beans', category: 'Cash Crops', unit: 'Metric Tonne' },
  { id: 'legume-sugarbeans', name: 'Sugar Beans', category: 'Legumes', unit: 'Kilogram' },
  { id: 'hort-tomatoes', name: 'Tomatoes', category: 'Horticulture', unit: 'Crate' },
  { id: 'hort-potatoes', name: 'Potatoes', category: 'Horticulture', unit: '15kg Bag' },
  { id: 'fruit-blueberries', name: 'Blueberries', category: 'Fruits', unit: 'Punnet' },
  { id: 'fruit-macadamia', name: 'Macadamia Nuts', category: 'Fruits', unit: 'Kilogram' },
  { id: 'live-cattle-beef', name: 'Cattle (Beef)', category: 'Livestock', unit: 'Head' },
  { id: 'live-eggs', name: 'Table Eggs', category: 'Poultry', unit: 'Crate (30)' }
];

class NationalMarketSync {
    constructor() {
        this.apiKey = "AGRI-TRUST-SECURE-SYNC-2026";
        this.catalog = ZIMBABWE_AGRI_CATALOG;
    }

    getRandomProduct() {
        return this.catalog[Math.floor(Math.random() * this.catalog.length)];
    }

    generatePulse() {
        return {
            system_status: "OPERATIONAL",
            sync_latency: `${Math.floor(Math.random() * 40) + 5}ms`,
            national_gdp_impact: `$${(Math.random() * 10 + 1).toFixed(1)}B (Projected)`,
            regional_convergence: {
                "Mashonaland_West": { price_index: 1.12, status: "STABLE" },
                "Midlands": { price_index: 1.05, status: "HIGH_LIQUIDITY" },
                "Manicaland": { price_index: 1.25, status: "CRITICAL_DEMAND" }
            },
            agri_trust_vitality: {
                active_escrow: "$1,450,000",
                trust_avg: "94%",
                velocity: "45 tx/hr"
            },
            last_handshake: new Date().toISOString()
        };
    }
    generateInsights(role) {
        const uRole = (role || 'FARMER').toUpperCase();
        const p1 = this.getRandomProduct();
        const p2 = this.getRandomProduct();

        if (uRole === 'FARMER') {
            return {
                title: "Farmer Strategic Intelligence",
                kicker: "YIELD MAXIMIZATION",
                predictions: [
                    { id: 1, type: 'PRICE', label: p1.name, change: '+18.4%', confidence: 92, action: 'Hold Inventory' },
                    { id: 2, type: 'DEMAND', label: p2.name, change: 'SPIKE_DETECTED', confidence: 88, action: 'Regional Shortage' },
                    { id: 3, type: 'WEATHER', label: 'Mash West Rain', change: '-12%', confidence: 75, action: 'Irrigation Required' }
                ],
                recommendations: [
                    `List your ${p1.name} in Gweru markets rather than Harare for better parity.`,
                    `Diversify acreage to ${p2.name} for export futures.`,
                    "Switch fertilizer supplier for 15% cost savings."
                ]
            };
        } else if (uRole === 'BUYER') {
            return {
                title: "Buyer Settlement Ledger",
                kicker: "ACQUISITION PIPELINE",
                predictions: [
                    { id: 1, type: 'SUPPLY', label: `${p1.name} Liquidity`, change: '-24%', confidence: 94, action: 'Pre-order Q3 requirements' },
                    { id: 2, type: 'QUALITY', label: `${p2.name} (Grade A)`, change: '+5.2%', confidence: 82, action: 'Superior Grade in Mash East' },
                    { id: 3, type: 'MACRO', label: p1.name + ' Parity', change: 'VOLATILE', confidence: 65, action: 'Enable Escrow Hedges' }
                ],
                recommendations: [
                    `Prioritize Mashonaland East for current ${p1.name} tenders.`,
                    `Lock bulk purchase terms for ${p2.name} via Escrow revenue.`,
                    "Onboard 5 more verified tier-3 farmers for supply stability."
                ]
            };
        } else {
            return {
                title: "Macro Network Governance",
                kicker: "REGIONAL CONTROL HUB",
                predictions: [
                    { id: 1, type: 'VELOCITY', label: 'Trade Volume', change: '+340%', confidence: 96, action: 'Scale Midlands node' },
                    { id: 2, type: 'RISK', label: 'Identity Integrity', change: 'ANOMALY', confidence: 91, action: 'Manual KYC audits for new hubs' },
                    { id: 3, type: 'TRUST', label: 'System Health', change: '9.2/10', confidence: 98, action: 'Performance bonus for Mat South' }
                ],
                recommendations: [
                    "Redirect Field Agents to Mash Central for congestion relief.",
                    "Optimize Dispute Resolution pipeline.",
                    "Launch regional incentives for local producers."
                ]
              };
        }
    }
    generateUnifiedPayload(role) {
        const pulse = this.generatePulse();
        const insights = this.generateInsights(role);
        return {
            telemetry: pulse,
            intelligence: insights,
            timestamp: new Date().toISOString(),
            node_integrity: "VERIFIED"
        };
    }
}

const syncManager = new NationalMarketSync();

const server = http.createServer((req, res) => {
    res.setHeader('Content-Type', 'application/json');
    res.setHeader('Access-Control-Allow-Origin', '*');
    
    if (req.url === '/' || req.url === '/sync') {
        res.writeHead(200);
        res.end(JSON.stringify(syncManager.generatePulse(), null, 4));
    } else if (req.url === '/products') {
        res.writeHead(200);
        res.end(JSON.stringify(ZIMBABWE_AGRI_CATALOG, null, 4));
    } else if (req.url.startsWith('/national-insights')) {
        const urlParams = new URL(req.url, `http://${req.headers.host}`);
        const role = urlParams.searchParams.get('role');
        res.writeHead(200);
        res.end(JSON.stringify(syncManager.generateUnifiedPayload(role), null, 4));
    } else if (req.url.startsWith('/premium-insights')) {
        const urlParams = new URL(req.url, `http://${req.headers.host}`);
        const role = urlParams.searchParams.get('role');
        res.writeHead(200);
        res.end(JSON.stringify(syncManager.generateInsights(role), null, 4));
    } else {
        res.writeHead(404);
        res.end(JSON.stringify({ error: "Not Found" }));
    }
});

const PORT = 3005;
server.listen(PORT, () => {
    console.log(`[AgriTrust SYNC] Node.js Gateway running on Port ${PORT}`);
});
