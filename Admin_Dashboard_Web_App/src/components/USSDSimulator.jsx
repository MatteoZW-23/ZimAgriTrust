import React, { useState, useEffect, useRef } from 'react';
import { runUSSDSession } from '../api';

export default function USSDSimulator({ profile }) {
  const [displayMessage, setDisplayMessage] = useState('Dial *123# to initiate secure USSD escrow channel.');
  const [input, setInput] = useState('');
  const [history, setHistory] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [sessionId, setSessionId] = useState(Date.now().toString());
  const [isEndScreen, setIsEndScreen] = useState(true);
  const inputRef = useRef(null);

  const handleInput = async (val) => {
    if (!val && !isEndScreen) return;
    setIsProcessing(true);
    
    let currentSessionId = sessionId;
    
    if (isEndScreen) {
        // Init logic
        if (val !== '*123#') val = '*123#';
        currentSessionId = Date.now().toString();
        setSessionId(currentSessionId);
        setHistory([{ input: val, type: 'tx' }]);
    } else {
        setHistory(prev => [...prev, { input: val, type: 'tx' }]);
    }
    
    try {
        let payloadText = "";
        if (!isEndScreen) {
            const priorTx = history.filter(h => h.type === 'tx').map(h => h.input).filter(i => i !== '*123#');
            payloadText = priorTx.concat(val).join("*");
        }

        const payload = {
            session_id: currentSessionId,
            phone_number: profile?.phone_number || "+263771234567",
            text: payloadText
        };
        
        const res = await runUSSDSession(payload);
        
        setDisplayMessage(res.message);
        setHistory(prev => [...prev, { response: res.message, type: 'rx', payloadText }]);
        
        if (res.end_session || res.message.startsWith("END")) {
            setIsEndScreen(true);
        } else {
            setIsEndScreen(false);
        }
    } catch(err) {
        setDisplayMessage("END Handshake Failed. AgriTrust Core Unreachable.");
        setIsEndScreen(true);
    }
    
    setInput('');
    setIsProcessing(false);
  };

  const cancelSession = () => {
     setDisplayMessage('Dial *123# to initiate secure USSD escrow channel.');
     setIsEndScreen(true);
     setInput('');
     setHistory([]);
  };

  useEffect(() => {
    if (inputRef.current) inputRef.current.focus();
  }, [displayMessage, isEndScreen, isProcessing]);

  // Format backend response for interface mapping
  const rawClean = displayMessage.replace(/^(CON|END)\s+/, '');
  const lines = rawClean.split('\\n').flatMap(l => l.split('\n'));
  const activeMenu = {
      title: lines[0] || "",
      options: lines.length > 1 ? lines.slice(1).filter(l => l.trim() !== '') : []
  };

  return (
    <div className="ussd-master-container animate-fade">
      <div className="ussd-header-spec">
         <h2>USSD Bridge Diagnostics</h2>
         <p>Real-time emulation and SS7 network payload tracing for mobile-first agricultural transactions.</p>
      </div>

      <div className="ussd-split-view">
        <div className="phone-bezel">
            <div className="phone-screen">
                <div className="screen-status-bar">
                    <span className="carrier">ECONET 📶</span>
                    <span className="time">12:45 PM</span>
                    <span className="battery">88% 🔋</span>
                </div>
                
                <div className="ussd-body">
                    {isProcessing ? (
                        <div className="ussd-loading">
                            <div className="spinner"></div>
                            <p>Connecting to AgriTrust Escrow...</p>
                        </div>
                    ) : (
                        <>
                            <div className="ussd-title">
                                {activeMenu.title.split('\n').map((line, i) => <div key={i}>{line}</div>)}
                            </div>
                            <div className="ussd-options">
                                {activeMenu.options.map((opt, i) => (
                                    <div key={i} className="ussd-option-row">{opt}</div>
                                ))}
                            </div>
                            <div className="ussd-input-area">
                                <input 
                                    ref={inputRef}
                                    type="text" 
                                    value={input} 
                                    onChange={(e) => setInput(e.target.value)}
                                    onKeyPress={(e) => e.key === 'Enter' && handleInput(input)}
                                    placeholder="Enter choice..."
                                />
                                <div className="ussd-actions">
                                    <button onClick={() => handleInput(input)}>{isEndScreen ? 'DIAL' : 'SEND'}</button>
                                    <button onClick={cancelSession}>CANCEL</button>
                                </div>
                            </div>
                        </>
                    )}
                </div>
            </div>
            <div className="phone-buttons">
                <div className="home-btn"></div>
            </div>
        </div>

        <div className="ussd-tracer">
           <div className="tracer-header">
               <span style={{ fontWeight: 850, fontSize: '11px', letterSpacing: '0.05em' }}><i className="fas fa-network-wired"></i> LIVE SS7 PAYLOAD INTERCEPT</span>
               <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                   <span style={{ fontSize: '10px', color: '#64748b' }}>PORT: 8080</span>
                   <div className="pulse-dot active" style={{ width: '6px', height: '6px' }}></div>
               </div>
           </div>
           <div className="tracer-body">
               {history.length === 0 ? (
                   <div className="tracer-empty">Awaiting USSD dialectic connection bridge... (*123#)</div>
               ) : (
                   history.filter(h => h.type === 'tx').map((h, i) => (
                       <div key={i} className="tracer-log">
                          <div className="log-meta">
                              <span className="log-time">{new Date().toISOString().split('T')[1].slice(0,-1)}</span>
                              <span className="log-type">[POST] /v1/ussd/session</span>
                          </div>
                          <pre className="log-json">
{JSON.stringify({
   msisdn: "+263771234567",
   sessionId: sessionId,
   serviceCode: "*123#",
   text: h.input || "INIT",
   network: "ECONET_ZWE",
   timestamp: new Date().getTime()
}, null, 2)}
                          </pre>
                       </div>
                   ))
               )}
           </div>
        </div>
      </div>

      <style>{`
            .ussd-master-container { padding: 40px; background: #fff; border-radius: 32px; box-shadow: 0 4px 20px rgba(0,0,0,0.05); }
            .ussd-header-spec { margin-bottom: 40px; }
            .ussd-header-spec h2 { font-size: 28px; font-weight: 950; color: #000E2B; margin-bottom: 8px; letter-spacing: -0.02em; }
            .ussd-header-spec p { font-size: 15px; color: #64748b; font-weight: 500; }
            
            .ussd-split-view { display: flex; gap: 40px; align-items: flex-start; }
            
            .phone-bezel {
                width: 320px;
                height: 580px;
                background: #1e293b;
                border: 8px solid #000E2B;
                border-radius: 40px;
                padding: 15px;
                box-shadow: 0 40px 100px rgba(0,0,0,0.15), inset 0 2px 5px rgba(255,255,255,0.1);
                position: relative;
                display: flex;
                flex-direction: column;
                flex-shrink: 0;
            }

            .ussd-tracer {
                flex: 1;
                background: #000E2B;
                border-radius: 20px;
                height: 580px;
                display: flex;
                flex-direction: column;
                overflow: hidden;
                border: 1px solid #1e293b;
                box-shadow: 0 20px 50px rgba(0,0,0,0.1);
            }
            .tracer-header {
                background: #1e293b;
                padding: 16px 24px;
                color: #fff;
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-bottom: 1px solid #334155;
            }
            .tracer-body {
                flex: 1;
                overflow-y: auto;
                padding: 24px;
                font-family: 'Courier New', Courier, monospace;
            }
            .tracer-empty {
                color: #475569;
                text-align: center;
                margin-top: 100px;
                font-size: 13px;
                font-weight: 600;
            }
            .tracer-log {
                margin-bottom: 24px;
                animation: slideUp 0.3s ease-out;
            }
            .log-meta { margin-bottom: 8px; font-size: 11px; display: flex; gap: 12px; }
            .log-time { color: #64748b; }
            .log-type { color: #20963D; font-weight: bold; }
            .log-json {
                background: rgba(0,0,0,0.4);
                padding: 16px;
                border-radius: 8px;
                color: #e2e8f0;
                font-size: 12px;
                margin: 0;
                overflow-x: auto;
                border-left: 3px solid #3b82f6;
            }

            @keyframes slideUp { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

            .phone-screen {
                flex: 1;
                background: #fff;
                border-radius: 10px;
                overflow: hidden;
                box-shadow: inset 0 0 40px rgba(0,0,0,0.05);
                display: flex;
                flex-direction: column;
                border: 2px solid #000;
            }

            .screen-status-bar {
                background: #f1f5f9;
                height: 24px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 0 10px;
                font-size: 10px;
                font-weight: 800;
                color: #64748b;
                border-bottom: 1px solid #e2e8f0;
            }

            .ussd-body {
                padding: 24px;
                flex: 1;
                background: #000;
                color: #fff;
                font-family: 'Courier New', Courier, monospace;
                display: flex;
                flex-direction: column;
            }

            .ussd-title { 
                font-size: 14px; 
                line-height: 1.4;
                margin-bottom: 20px;
                padding-bottom: 15px;
                border-bottom: 2px solid #333;
                font-weight: bold;
            }

            .ussd-option-row {
                font-size: 14px;
                margin-bottom: 8px;
                line-height: 1.4;
            }

            .ussd-loading {
                flex: 1;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                text-align: center;
            }
            .spinner {
                width: 30px;
                height: 30px;
                border: 3px solid rgba(255,255,255,0.1);
                border-top-color: #fff;
                border-radius: 50%;
                animation: spin 1s infinite linear;
                margin-bottom: 15px;
            }
            @keyframes spin { to { transform: rotate(360deg); } }

            .ussd-input-area {
                margin-top: auto;
                padding-top: 20px;
            }

            .ussd-input-area input {
                width: 100%;
                background: transparent;
                border: none;
                border-bottom: 2px solid #fff;
                color: #fff;
                font-size: 18px;
                padding: 5px 0;
                outline: none;
                margin-bottom: 20px;
                font-family: inherit;
            }

            .ussd-actions {
                display: flex;
                gap: 15px;
            }

            .ussd-actions button {
                flex: 1;
                background: transparent;
                border: 2px solid #fff;
                color: #fff;
                padding: 10px;
                font-size: 12px;
                font-weight: 800;
                cursor: pointer;
                border-radius: 4px;
            }
            .ussd-actions button:hover { background: #fff; color: #000; }

            .home-btn {
                width: 44px;
                height: 44px;
                border: 3px solid rgba(255,255,255,0.1);
                border-radius: 50%;
                margin: 15px auto 4px;
            }
        `}</style>
    </div>
  );
}

