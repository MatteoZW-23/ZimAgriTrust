const { Client, LocalAuth, MessageMedia } = require('whatsapp-web.js');
const qrcodeTerminal = require('qrcode-terminal');
const QRCode = require('qrcode');

const axios = require('axios');
const express = require('express');
const bodyParser = require('body-parser');

const app = express();
app.use(bodyParser.json());

const BACKEND_URL = process.env.BACKEND_URL || 'http://backend:8000/api/v1/whatsapp/webhook';
const PORT = process.env.PORT || 3006;

let lastQrString = null;

const client = new Client({
    authStrategy: new LocalAuth({
        dataPath: './.wwebjs_auth'
    }),
    authTimeoutMs: 0, // Disable timeout to give the user plenty of time
    qrMaxRetries: 10,
    puppeteer: {
        args: [
            '--no-sandbox', 
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--no-first-run',
            '--no-zygote',
            '--single-process', // <- this one can help memory in some docker envs
            '--disable-gpu'
        ],
        headless: true,
        executablePath: process.platform === 'linux' 
            ? '/usr/bin/chromium' 
            : 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
    }
});

client.on('qr', (qr) => {
    console.log('NEW QR RECEIVED');
    lastQrString = qr;
    qrcodeTerminal.generate(qr, { small: true });
});

app.get('/qr', async (req, res) => {
    if (!lastQrString) {
        return res.send(`
            <html>
                <head><meta http-equiv="refresh" content="5"></head>
                <body style="background: #111; color: #eee; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; font-family: sans-serif;">
                    <div style="background: #222; padding: 2rem; border-radius: 1rem; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
                        <h2>⏳ Waiting for QR Code...</h2>
                        <p>The bridge is initializing. This page will refresh automatically.</p>
                        <div style="border: 2px solid #555; width: 300px; height: 300px; display: flex; align-items: center; justify-content: center; margin-top: 1rem;">
                           <div class="loader"></div>
                        </div>
                    </div>
                    <style>
                        .loader { border: 4px solid #333; border-top: 4px solid #25D366; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; }
                        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
                    </style>
                </body>
            </html>
        `);
    }

    try {
        const qrImage = await QRCode.toDataURL(lastQrString);
        res.send(`
            <html>
                <head>
                    <title>AgriTrust WhatsApp Login</title>
                    <meta http-equiv="refresh" content="20">
                </head>
                <body style="background: #111; color: #eee; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; font-family: sans-serif; margin: 0;">
                    <div style="background: #222; padding: 2rem; border-radius: 1rem; box-shadow: 0 10px 50px rgba(0,0,0,0.8); text-align: center; border: 1px solid #333;">
                        <img src="https://upload.wikimedia.org/wikipedia/commons/6/6b/WhatsApp.svg" width="60" style="margin-bottom: 1rem;">
                        <h1 style="margin: 0 0 0.5rem 0; color: #25D366;">AgriTrust Bridge</h1>
                        <p style="color: #888; margin-bottom: 2rem;">Scan this QR code with your WhatsApp app <br/> (Settings > Linked Devices > Link a Device)</p>
                        
                        <div style="background: white; padding: 1.5rem; border-radius: 0.5rem; display: inline-block;">
                            <img src="${qrImage}" width="300" height="300" style="display: block;">
                        </div>
                        
                        <div style="margin-top: 2rem; font-size: 0.8rem; color: #555;">
                            Page refreshes every 20 seconds. <br/>
                            Session will be saved for future use.
                        </div>
                    </div>
                </body>
            </html>
        `);
    } catch (err) {
        res.status(500).send("Error generating QR code image");
    }
});

client.on('ready', () => {
    console.log('WhatsApp Bridge is READY!');
});

client.on('message', async (msg) => {
    // Completely ignore WhatsApp Status, Newsletters, and Groups
    if (msg.from === 'status@broadcast' || msg.from.endsWith('@newsletter') || msg.from.endsWith('@g.us')) {
        return;
    }

    console.log(`RECEIVED MESSAGE from ${msg.from}: ${msg.body}`);

    try {
        let mediaData = null;
        if (msg.hasMedia) {
            const media = await msg.downloadMedia();
            mediaData = {
                data: media.data,
                mimetype: media.mimetype,
                filename: media.filename
            };
        }

        const response = await axios.post(BACKEND_URL, {
            from: msg.from,
            body: msg.body,
            hasMedia: msg.hasMedia,
            media: mediaData,
            timestamp: msg.timestamp,
            pushname: msg._data.notifyName
        });

        if (response.data && response.data.reply) {
            msg.reply(response.data.reply);
        }
    } catch (error) {
        console.error('Error forwarding message to backend:', error.message);
        // msg.reply("Sorry, I'm having trouble connecting to the host system. Please try again later.");
    }
});

// Endpoint for backend to send messages back to WhatsApp users
app.post('/send', async (req, res) => {
    const { to, message, mediaUrl, mediaData } = req.body;
    
    try {
        if (mediaUrl || mediaData) {
            let media;
            if (mediaUrl) {
                media = await MessageMedia.fromUrl(mediaUrl);
            } else {
                media = new MessageMedia(mediaData.mimetype, mediaData.data, mediaData.filename);
            }
            await client.sendMessage(to, media, { caption: message });
        } else {
            await client.sendMessage(to, message);
        }
        res.status(200).json({ status: 'success' });
    } catch (error) {
        console.error('Error sending message:', error);
        res.status(500).json({ error: error.message });
    }
});

app.listen(PORT, () => {
    console.log(`WhatsApp Bridge control API listening on port ${PORT}`);
});

const startClient = async (retries = 5) => {
    try {
        console.log(`Starting WhatsApp Bridge... (Attempts remaining: ${retries})`);
        await client.initialize();
    } catch (err) {
        console.error('FAILED TO INITIALIZE WHATSAPP CLIENT:', err.message);
        if (retries > 0) {
            console.log('Retrying in 10 seconds...');
            setTimeout(() => startClient(retries - 1), 10000);
        } else {
            console.error('MAX RETRIES REACHED. EXITING.');
            process.exit(1);
        }
    }
};

startClient();
