/**
 * AgriTrust Sovereign WhatsApp Academy Handler
 * Manages interactive learning sessions via WhatsApp for field agents.
 */

const axios = require('axios');

class TrainingHandler {
    constructor(backendUrl) {
        this.backendUrl = backendUrl;
    }

    async handle(message) {
        const text = message.body.toLowerCase();
        
        if (text.includes('start training')) {
            return this.sendModuleIntro(message.from, 1);
        }

        if (text.startsWith('ans:')) {
            return this.processQuizAnswer(message.from, text.replace('ans:', '').trim());
        }

        return null;
    }

    async sendModuleIntro(to, moduleId) {
        // Fetch content from FastAPI backend
        try {
            const response = await axios.get(`${this.backendUrl}/api/v1/training/module/${moduleId}`);
            const module = response.data;

            return {
                to: to,
                body: `📗 *Sovereign Agent Academy*\n\nWelcome to *${module.title}*.\n\nThis module covers ${module.pages} pages of critical protocol. Please reply with "READY" when you have reviewed the handbook: ${module.handbook_url}\n\n_Sovereignty through competence._`
            };
        } catch (error) {
            console.error('Failed to fetch training module:', error);
            return {
                to: to,
                body: "⚠️ *System Error*: Training portal temporarily offline. Please try again later."
            };
        }
    }

    async processQuizAnswer(to, answer) {
        // Simulated quiz logic
        return {
            to: to,
            body: `✅ *Correct!* You've passed the checkpoint for Module 1. \n\nReply with *Module 2* to continue your certification path.`
        };
    }
}

module.exports = TrainingHandler;
