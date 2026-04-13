import React, { useState, useEffect } from 'react';

export const WeatherAlert = ({ profile }) => {
    const [weather, setWeather] = useState({
        temp: 28,
        condition: 'Partly Cloudy',
        location: 'Harare, Zimbabwe',
        alert: null,
        icon: 'fa-cloud-sun'
    });

    useEffect(() => {
        // Simulated Weather Logic for Zimbabwe Rural Districts
        const districts = ['Binga', 'Mudzi', 'Mount Darwin', 'Chiredzi'];
        const randomDistrict = districts[Math.floor(Math.random() * districts.length)];
        
        // Dynamic Weather States
        const states = [
            { temp: 31, condition: 'Clear Sky', alert: 'High Evaporation Risk', icon: 'fa-sun' },
            { temp: 24, condition: 'Heavy Rain', alert: 'Flash Flood Warning (Low-lying areas)', icon: 'fa-cloud-showers-heavy' },
            { temp: 27, condition: 'Moderate Wind', alert: 'Recommended for Fertilizer Application', icon: 'fa-wind' },
            { temp: 29, condition: 'Scattered Thunderstorms', alert: 'Localized Lightning Hazards', icon: 'fa-cloud-bolt' }
        ];
        
        const selected = states[Math.floor(Math.random() * states.length)];
        setWeather({
            ...selected,
            location: `${randomDistrict}, ZW`
        });
    }, []);

    if (!profile) return null;

    return (
        <div className="v4-card weather-alert-v4 animate-rise" style={{ 
            background: 'linear-gradient(135deg, var(--v4-primary) 0%, var(--v4-primary-dark) 100%)',
            color: 'white',
            marginBottom: '24px',
            padding: '20px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            border: 'none',
            boxShadow: '0 15px 35px var(--v4-glow, rgba(0,0,0,0.1))'
        }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
                <div style={{ 
                    width: '60px', 
                    height: '60px', 
                    background: 'rgba(255,255,255,0.15)', 
                    borderRadius: '16px',
                    display: 'grid',
                    placeItems: 'center',
                    fontSize: '28px'
                }}>
                    <i className={`fas ${weather.icon} animate-pulse`}></i>
                </div>
                <div>
                    <div style={{ fontSize: '12px', fontWeight: '800', opacity: '0.8', textTransform: 'uppercase', letterSpacing: '1px' }}>
                        Local Agrometeorology: {weather.location}
                    </div>
                    <div style={{ fontSize: '24px', fontWeight: '900', display: 'flex', alignItems: 'center', gap: '10px' }}>
                        {weather.temp}°C <span style={{ fontSize: '16px', fontWeight: '600', opacity: '0.9' }}>— {weather.condition}</span>
                    </div>
                </div>
            </div>

            {weather.alert && (
                <div style={{ 
                    background: 'rgba(255,160,0,0.2)', 
                    border: '1px solid rgba(255,160,0,0.4)', 
                    padding: '10px 20px', 
                    borderRadius: '12px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px'
                }}>
                    <i className="fas fa-triangle-exclamation" style={{ color: '#fbbf24' }}></i>
                    <div>
                        <div style={{ fontSize: '10px', fontWeight: '900', color: '#fbbf24', textTransform: 'uppercase' }}>Farmer Advisory</div>
                        <div style={{ fontSize: '13px', fontWeight: '700' }}>{weather.alert}</div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default WeatherAlert;
