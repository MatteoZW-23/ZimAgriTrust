import React, { useState, useEffect, useRef } from 'react';

export default function SupportConcierge({ profile, onViewChange }) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    { id: 1, text: `Hello! Welcome to ZimAgritrust, ${profile?.full_name || 'Partner'}. I am your Platform Concierge at the Desk. How can I help your operations today?`, sender: 'bot', time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }
  ]);
  const [inputValue, setInputValue] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const scrollRef = useRef(null);

  const OPENROUTER_KEY = import.meta.env.VITE_OPENROUTER_KEY;

  useEffect(() => {
    if (scrollRef.current) {
        scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isOpen, isTyping]);

  const quickActions = [
    { label: "Check Escrow Status", view: "transactions-admin" },
    { label: "Market Trends", view: "overview" },
    { label: "Account Verification", view: "settings" },
    { label: "Regional Help", view: "network" }
  ];

  const handleSend = async (text) => {
    const userMsg = text || inputValue;
    if (!userMsg.trim() || isTyping) return;

    const userMessageObj = { 
        id: Date.now(), 
        text: userMsg, 
        sender: 'user', 
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) 
    };
    
    setMessages(prev => [...prev, userMessageObj]);
    setInputValue("");
    setIsTyping(true);

    try {
        const response = await fetch("https://openrouter.ai/api/v1/chat/completions", {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${OPENROUTER_KEY}`,
                "Content-Type": "application/json",
                "HTTP-Referer": window.location.origin,
                "X-Title": "ZimAgritrust Desk Support"
            },
            body: JSON.stringify({
                model: "google/gemini-2.0-flash-lite-001",
                messages: [
                    { role: "system", content: "You are the ZimAgritrust Desk support team, a human operations officer based in Harare. You are professional and extremely helpful for our national agricultural marketplace. You help Farmers, Buyers, Agents, and Admins. Use professional Zimbabwean English (e.g., 'Kindly note', 'Please assist'). NEVER mention you are an AI or an assistant. Act like a real person managing the desk. Keep responses concise and focused on escrow, trust scores, and field verification." },
                    { role: "user", content: userMsg }
                ]
            })
        });

        const data = await response.json();
        const botResponse = data.choices?.[0]?.message?.content || "Eish, I am currently facing some network issues. Kindly check back in a moment or contact our main office.";
        
        setMessages(prev => [...prev, { 
            id: Date.now() + 1, 
            text: botResponse, 
            sender: 'bot', 
            time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) 
        }]);
    } catch (err) {
        console.error("AI Node Error:", err);
        setMessages(prev => [...prev, { 
            id: Date.now() + 1, 
            text: "The Desk is currently very busy. Kindly verify your credentials or check your connection and try again.", 
            sender: 'bot', 
            time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) 
        }]);
    } finally {
        setIsTyping(false);
    }
  };

  return (
    <>
      <div className={`concierge-bubble ${isOpen ? 'active' : ''}`} onClick={() => !isOpen && setIsOpen(true)}>
        <div className="bubble-aura"></div>
        <i className={`fas ${isOpen ? 'fa-times' : 'fa-headset'}`}></i>
      </div>

      <div className={`concierge-window ${isOpen ? 'open' : ''}`}>
        <div className="concierge-header">
           <div className="c-avatar">
               <i className="fas fa-user-tie"></i>
               <div className="online-status"></div>
           </div>
           <div className="c-meta">
               <strong>ZimAgritrust Concierge</strong>
               <span>Platform Support Agent</span>
           </div>
           <button className="c-close" onClick={() => setIsOpen(false)}><i className="fas fa-chevron-down"></i></button>
        </div>

        <div className="concierge-body" ref={scrollRef}>
            {messages.map(m => (
                <div key={m.id} className={`msg-row ${m.sender}`}>
                    <div className="msg-bubble">
                        {m.text}
                        <span className="msg-time">{m.time}</span>
                    </div>
                </div>
            ))}
            {isTyping && (
                <div className="msg-row bot">
                    <div className="msg-bubble shimmer" style={{ opacity: 0.7, padding: '14px 20px' }}>
                        <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
                            <div className="type-dot"></div>
                            <div className="type-dot"></div>
                            <div className="type-dot"></div>
                            <span style={{ fontSize: '9px', fontWeight: 900, marginLeft: '8px', opacity: 0.5 }}>SYNCHRONIZING DATA...</span>
                        </div>
                    </div>
                </div>
            )}
        </div>

        <div className="concierge-footer">
            <div className="quick-actions">
                {quickActions.map((qa, i) => (
                    <button key={i} className="qa-chip" onClick={() => {
                        handleSend(qa.label);
                        onViewChange(qa.view);
                    }}>{qa.label}</button>
                ))}
            </div>
            <div className="input-area">
                <input 
                    type="text" 
                    placeholder="Type support details..." 
                    value={inputValue} 
                    onChange={(e) => setInputValue(e.target.value)} 
                    onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                />
                <button className="send-btn" onClick={() => handleSend()}>
                    <i className="fas fa-paper-plane"></i>
                </button>
            </div>
        </div>
      </div>

      <style>{`
        .concierge-bubble {
            position: fixed;
            bottom: 30px;
            right: 30px;
            width: 60px;
            height: 60px;
            background: #000E2B;
            color: #fff;
            border-radius: 50%;
            display: grid;
            place-items: center;
            font-size: 24px;
            cursor: pointer;
            z-index: 9999;
            box-shadow: 0 10px 30px rgba(6, 78, 59, 0.4);
            transition: 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }
        .concierge-bubble:hover { transform: scale(1.1) rotate(5deg); }
        .concierge-bubble.active { transform: scale(0); opacity: 0; }
        .bubble-aura { position: absolute; inset: -4px; border-radius: 50%; border: 2px solid #20963D; animation: pulse-aura 2s infinite; }
        @keyframes pulse-aura { 0% { opacity: 0.5; transform: scale(1); } 100% { opacity: 0; transform: scale(1.4); } }

        .concierge-window {
            position: fixed;
            bottom: 30px;
            right: 30px;
            width: 380px;
            height: 550px;
            background: #fff;
            border-radius: 28px;
            display: flex;
            flex-direction: column;
            z-index: 10000;
            box-shadow: 0 40px 100px rgba(0,0,0,0.2);
            transform: translateY(100px) scale(0.9);
            opacity: 0;
            pointer-events: none;
            transition: 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            overflow: hidden;
            border: 1px solid rgba(0,0,0,0.05);
        }
        .concierge-window.open { transform: translateY(0) scale(1); opacity: 1; pointer-events: auto; }

        .concierge-header { background: #000E2B; padding: 24px; display: flex; align-items: center; gap: 16px; color: #fff; }
        .c-avatar { position: relative; width: 44px; height: 44px; background: rgba(255,255,255,0.1); border-radius: 12px; display: grid; place-items: center; font-size: 20px; }
        .online-status { position: absolute; bottom: -2px; right: -2px; width: 12px; height: 12px; background: #20963D; border: 2px solid #000E2B; border-radius: 50%; }
        .c-meta { flex: 1; }
        .c-meta strong { display: block; font-size: 15px; font-weight: 800; letter-spacing: -0.02em; }
        .c-meta span { font-size: 11px; opacity: 0.6; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; }
        .c-close { background: none; border: none; color: #fff; font-size: 18px; cursor: pointer; opacity: 0.5; transition: 0.2s; }
        .c-close:hover { opacity: 1; }

        .concierge-body { flex: 1; padding: 24px; overflow-y: auto; background: #f8fafc; display: flex; flex-direction: column; gap: 16px; }
        .msg-row { display: flex; width: 100%; }
        .msg-row.bot { justify-content: flex-start; }
        .msg-row.user { justify-content: flex-end; }
        .msg-bubble { max-width: 80%; padding: 12px 16px; border-radius: 18px; font-size: 13px; font-weight: 600; line-height: 1.5; position: relative; }
        .bot .msg-bubble { background: #fff; color: #000E2B; border-bottom-left-radius: 4px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
        .user .msg-bubble { background: #000E2B; color: #fff; border-bottom-right-radius: 4px; box-shadow: 0 4px 12px rgba(6, 78, 59, 0.2); }
        .msg-time { display: block; font-size: 9px; margin-top: 4px; opacity: 0.5; text-align: right; }

        .type-dot {
            width: 4px;
            height: 4px;
            background: #000E2B;
            border-radius: 50%;
            animation: dot-jump 1.4s infinite ease-in-out;
        }
        .type-dot:nth-child(2) { animation-delay: 0.2s; }
        .type-dot:nth-child(3) { animation-delay: 0.4s; }
        @keyframes dot-jump {
            0%, 80%, 100% { transform: scale(0); opacity: 0.3; }
            40% { transform: scale(1.5); opacity: 1; }
        }

        .concierge-footer { background: #fff; padding: 20px; border-top: 1px solid #f1f5f9; }
        .quick-actions { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 16px; }
        .qa-chip { background: #f1f5f9; border: none; padding: 6px 12px; border-radius: 100px; font-size: 11px; font-weight: 800; color: #475569; cursor: pointer; transition: 0.2s; }
        .qa-chip:hover { background: #e2e8f0; color: #000E2B; }
        
        .input-area { display: flex; background: #f8fafc; border-radius: 14px; padding: 4px; border: 1.5px solid #e2e8f0; }
        .input-area input { flex: 1; background: none; border: none; padding: 10px 14px; outline: none; font-size: 13px; font-weight: 600; color: #000E2B; }
        .send-btn { background: #000E2B; color: #fff; border: none; width: 40px; height: 40px; border-radius: 10px; cursor: pointer; transition: 0.2s; }
        .send-btn:hover { background: #065f46; transform: scale(1.05); }

        @media (max-width: 500px) {
            .concierge-window { width: 100%; height: 100%; bottom: 0; right: 0; border-radius: 0; }
        }
      `}</style>
    </>
  );
}
