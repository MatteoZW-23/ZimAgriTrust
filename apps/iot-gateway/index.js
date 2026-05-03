const http = require('http');
const { URL } = require('url');

class NationalMarketSync {
    constructor() {
        this.apiKey = process.env.SYNC_API_KEY || "";
    }

    generatePulse() {
        return {
            system_status: "OPERATIONAL",
            sync_latency: null,
            national_gdp_impact: null,
            regional_convergence: {},
            agri_trust_vitality: {
                active_escrow: null,
                trust_avg: null,
                velocity: null
            },
            last_handshake: new Date().toISOString()
        };
    }

    generateInsights(role) {
        return {
            title: "Market Intelligence",
            kicker: "LIVE DATA",
            predictions: [],
            recommendations: []
        };
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
        // Products are served from the backend API
        res.writeHead(200);
        res.end(JSON.stringify([], null, 4));
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

const PORT = process.env.PORT || 3005;
server.listen(PORT, () => {
    console.log(`[ZimAgritrust SYNC] Node.js Gateway running on Port ${PORT}`);
});
