
import React, { useState, useEffect } from 'react';
import { fetchScraperStatus, runScraper, runCleaningPipeline, clearScraperCaches, fetchDataSnapshots } from '../api';

// -- Scraper definitions --------------------------------------------------------
const SCRAPERS = [
  {
    id: 'prices',
    name: 'Commodity Price Scraper',
    description: 'Scrapes live crop prices from GMB, AMA, ZimPriceCheck, FarmnPort and Ministry of Agriculture.',
    icon: 'fa-tags',
    color: '#f59e0b',
    sources: ['gmbdura.co.zw', 'ama.co.zw', 'zimpricecheck.com', 'farmnport.com', 'agric.gov.zw'],
    schedule: 'Every 60 min',
    dataKey: 'prices',
  },
  {
    id: 'news',
    name: 'Agriculture News Scraper',
    description: 'Scrapes RSS feeds from The Herald, NewsDay, Chronicle, ZBC News, Sunday Mail and FinGazette. Falls back to HTML scraping.',
    icon: 'fa-newspaper',
    color: '#3b82f6',
    sources: ['herald.co.zw', 'newsday.co.zw', 'chronicle.co.zw', 'zbcnews.co.zw', 'sundaymail.co.zw', 'financialgazette.co.zw'],
    schedule: 'Every 60 min',
    dataKey: 'news',
  },
  {
    id: 'weather',
    name: 'Weather Data Fetcher',
    description: 'Fetches current weather for 5 major Zimbabwe farming regions via OpenWeatherMap API.',
    icon: 'fa-cloud-sun',
    color: '#06b6d4',
    sources: ['OpenWeatherMap API'],
    schedule: 'Every 6 hours',
    dataKey: 'weather',
  },
];

// -- Cleaning pipeline definitions ----------------------------------------------
const PIPELINES = [
  {
    id: 'prices',
    name: 'Price Data Cleaner',
    description: 'IQR outlier removal, unit normalisation (tonnes?kg), commodity name standardisation. Exports CSV snapshot.',
    icon: 'fa-filter',
    color: '#f59e0b',
    steps: ['Standardise names', 'IQR outlier removal', 'Unit normalisation', 'Export CSV'],
  },
  {
    id: 'listings',
    name: 'Listing Data Cleaner',
    description: 'Deduplication, median imputation for missing fields, physical constraint enforcement (price>0, qty>0), feature engineering.',
    icon: 'fa-list-check',
    color: '#22c55e',
    steps: ['Deduplication', 'Median imputation', 'Constraint enforcement', 'Feature engineering', 'Export CSV'],
  },
  {
    id: 'transactions',
    name: 'Transaction Feature Builder',
    description: 'Builds fraud-detector-ready feature vectors from completed orders: log transforms, off-hour flags, velocity features.',
    icon: 'fa-shield-halved',
    color: '#8b5cf6',
    steps: ['Log transforms', 'Off-hour detection', 'Price/qty features', 'Export CSV'],
  },
];
export default function DataPipelinePanel({ token }) {
  const [status, setStatus]       = useState(null);
  const [snapshots, setSnapshots] = useState([]);
  const [jobs, setJobs]           = useState({});       // { id: { status, result, startedAt } }
  const [activeTab, setActiveTab] = useState('scrapers'); // scrapers | cleaning | snapshots
  const [preview, setPreview]     = useState(null);     // { title, items }

  useEffect(() => { loadStatus(); loadSnapshots(); }, []);

  const loadStatus = async () => {
    try { setStatus(await fetchScraperStatus(token)); } catch { /* ignore */ }
  };

  const loadSnapshots = async () => {
    try { const d = await fetchDataSnapshots(token); setSnapshots(d.snapshots || []); } catch { /* ignore */ }
  };

  const dispatch = async (type, id, fn) => {
    setJobs(p => ({ ...p, [id]: { status: 'running', startedAt: new Date() } }));
    try {
      const res = await fn();
      setJobs(p => ({ ...p, [id]: { status: 'done', result: res, startedAt: p[id].startedAt } }));
      if (res.items) setPreview({ title: id, items: res.items });
      loadStatus();
      if (type === 'clean') loadSnapshots();
    } catch (err) {
      setJobs(p => ({ ...p, [id]: { status: 'error', result: { error: err.message }, startedAt: p[id].startedAt } }));
    }
  };

  const handleClearCache = async () => {
    try {
      await clearScraperCaches(token);
      setStatus(null);
      loadStatus();
    } catch (err) { alert(err.message); }
  };

  const cacheInfo = (key) => {
    if (!status) return null;
    return status.scrapers?.[key];
  };

  const jobColor = (s) => ({ running: '#f59e0b', done: '#22c55e', error: '#ef4444' }[s] || '#94a3b8');

  const tabs = ['scrapers', 'cleaning', 'snapshots'];

  return (
    <div className="v4-dashboard-container animate-fade-in">

      {/* HERO */}
      <header style={{
        background: 'linear-gradient(135deg, #0a0a1a 0%, #0f2027 50%, #203a43 100%)',
        borderRadius: '32px', padding: '48px', color: '#fff',
        display: 'grid', gridTemplateColumns: '1fr auto', gap: '40px', alignItems: 'center',
      }}>
        <div>
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center', marginBottom: '16px' }}>
            <span style={{ background: 'rgba(6,182,212,0.2)', color: '#06b6d4', fontSize: '10px', fontWeight: 900, padding: '4px 14px', borderRadius: '6px', letterSpacing: '0.1em' }}>DATA OPERATIONS CENTER</span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '10px', fontWeight: 900, opacity: 0.6 }}>
              <div style={{ width: '6px', height: '6px', background: status ? '#22c55e' : '#f59e0b', borderRadius: '50%', boxShadow: `0 0 8px ${status ? '#22c55e' : '#f59e0b'}` }}></div>
              {status ? 'SCHEDULER ACTIVE' : 'LOADING STATUS...'}
            </div>
          </div>
          <h1 style={{ fontSize: '42px', fontWeight: 950, margin: '0 0 12px', letterSpacing: '-0.04em' }}>
            Scraping & <span style={{ color: '#06b6d4' }}>Data Pipeline</span>.
          </h1>
          <p style={{ fontSize: '15px', opacity: 0.7, maxWidth: '560px', lineHeight: 1.7, fontWeight: 600, margin: 0 }}>
            Manually trigger scrapers, run data cleaning pipelines, inspect cache state and download production snapshots.
          </p>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <button onClick={() => dispatch('scrape', 'all', () => runScraper(token, 'all'))} style={{
            padding: '16px 28px', borderRadius: '16px', border: 'none', cursor: 'pointer',
            background: '#06b6d4', color: '#fff', fontWeight: 950, fontSize: '13px',
            display: 'flex', alignItems: 'center', gap: '10px',
            boxShadow: '0 8px 24px rgba(6,182,212,0.4)',
          }}>
            {jobs['all']?.status === 'running'
              ? <><i className="fas fa-circle-notch fa-spin"></i> SCRAPING ALL...</>
              : <><i className="fas fa-bolt"></i> RUN ALL SCRAPERS</>}
          </button>
          <button onClick={handleClearCache} style={{
            padding: '12px 28px', borderRadius: '14px', border: '1.5px solid rgba(255,255,255,0.15)',
            background: 'transparent', color: 'rgba(255,255,255,0.7)', fontWeight: 900, fontSize: '12px', cursor: 'pointer',
          }}>
            <i className="fas fa-trash-can" style={{ marginRight: '8px' }}></i>CLEAR ALL CACHES
          </button>
        </div>
      </header>

      {/* SCHEDULER STATUS STRIP */}
      {status?.scheduler_jobs?.length > 0 && (
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          {status.scheduler_jobs.map(job => (
            <div key={job.id} style={{
              padding: '10px 18px', borderRadius: '12px', background: 'var(--v4-surface)',
              border: `1.5px solid ${job.running ? '#22c55e33' : 'var(--v4-border)'}`,
              display: 'flex', alignItems: 'center', gap: '10px',
            }}>
              <div style={{ width: '7px', height: '7px', borderRadius: '50%', background: job.running ? '#22c55e' : '#94a3b8', boxShadow: job.running ? '0 0 6px #22c55e' : 'none' }}></div>
              <div>
                <div style={{ fontSize: '11px', fontWeight: 900 }}>{job.name}</div>
                {job.next_run && <div style={{ fontSize: '10px', color: 'var(--v4-text-dim)', fontWeight: 700 }}>Next: {new Date(job.next_run).toLocaleTimeString()}</div>}
              </div>
            </div>
          ))}
          <button onClick={loadStatus} style={{ marginLeft: 'auto', padding: '10px 18px', borderRadius: '12px', border: '1.5px solid var(--v4-border)', background: 'transparent', cursor: 'pointer', fontSize: '11px', fontWeight: 900, color: 'var(--v4-text-dim)' }}>
            <i className="fas fa-sync" style={{ marginRight: '6px' }}></i>Refresh
          </button>
        </div>
      )}

      {/* TABS */}
      <div style={{ display: 'flex', gap: '8px' }}>
        {tabs.map(tab => (
          <button key={tab} onClick={() => setActiveTab(tab)} style={{
            padding: '10px 28px', borderRadius: '12px', border: 'none', cursor: 'pointer',
            fontWeight: 900, fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.05em',
            background: activeTab === tab ? '#06b6d4' : 'var(--v4-surface)',
            color: activeTab === tab ? '#fff' : 'var(--v4-text-dim)', transition: '0.2s',
          }}>
            <i className={`fas ${tab === 'scrapers' ? 'fa-spider' : tab === 'cleaning' ? 'fa-broom' : 'fa-database'}`} style={{ marginRight: '8px' }}></i>
            {tab === 'scrapers' ? 'Scrapers' : tab === 'cleaning' ? 'Data Cleaning' : 'Snapshots'}
          </button>
        ))}
      </div>

      {/* -- SCRAPERS TAB -- */}
      {activeTab === 'scrapers' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(380px, 1fr))', gap: '24px' }}>
          {SCRAPERS.map(sc => {
            const job   = jobs[sc.id];
            const cache = cacheInfo(sc.id);
            const isRunning = job?.status === 'running';
            return (
              <div key={sc.id} style={{
                background: 'var(--v4-surface)', borderRadius: '28px', padding: '32px',
                border: `1.5px solid ${isRunning ? sc.color + '55' : 'var(--v4-border)'}`,
                display: 'flex', flexDirection: 'column', gap: '18px', position: 'relative', overflow: 'hidden',
              }}>
                <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: '3px', background: sc.color, borderRadius: '28px 28px 0 0' }} />

                {/* Header */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                    <div style={{ width: '48px', height: '48px', borderRadius: '14px', background: sc.color + '15', display: 'grid', placeItems: 'center', border: `1.5px solid ${sc.color}33` }}>
                      <i className={`fas ${sc.icon}`} style={{ fontSize: '20px', color: sc.color }}></i>
                    </div>
                    <strong style={{ fontSize: '15px', fontWeight: 950 }}>{sc.name}</strong>
                  </div>
                  <span style={{ fontSize: '9px', fontWeight: 900, padding: '3px 10px', borderRadius: '6px', background: 'var(--v4-bg)', color: 'var(--v4-text-dim)', border: '1px solid var(--v4-border)' }}>
                    <i className="fas fa-clock" style={{ marginRight: '4px' }}></i>{sc.schedule}
                  </span>
                </div>

                <p style={{ fontSize: '13px', color: 'var(--v4-text-dim)', fontWeight: 600, margin: 0, lineHeight: 1.6 }}>{sc.description}</p>

                {/* Cache status */}
                {cache && (
                  <div style={{ padding: '14px 16px', background: 'var(--v4-bg)', borderRadius: '14px', border: '1px solid var(--v4-border)', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                    <div>
                      <div style={{ fontSize: '9px', fontWeight: 900, opacity: 0.5, letterSpacing: '0.1em', marginBottom: '3px' }}>CACHED ITEMS</div>
                      <strong style={{ fontSize: '18px', fontWeight: 950, color: cache.cached_items > 0 ? '#22c55e' : '#94a3b8' }}>{cache.cached_items}</strong>
                    </div>
                    <div>
                      <div style={{ fontSize: '9px', fontWeight: 900, opacity: 0.5, letterSpacing: '0.1em', marginBottom: '3px' }}>CACHE AGE</div>
                      <strong style={{ fontSize: '14px', fontWeight: 950, color: cache.stale ? '#ef4444' : '#22c55e' }}>
                        {cache.cache_age_sec != null ? `${Math.floor(cache.cache_age_sec / 60)}m ${cache.cache_age_sec % 60}s` : 'Empty'}
                      </strong>
                    </div>
                    {cache.last_scraped && (
                      <div style={{ gridColumn: '1/-1' }}>
                        <div style={{ fontSize: '9px', fontWeight: 900, opacity: 0.5, letterSpacing: '0.1em', marginBottom: '3px' }}>LAST SCRAPED</div>
                        <div style={{ fontSize: '11px', fontWeight: 700 }}>{new Date(cache.last_scraped).toLocaleString()}</div>
                      </div>
                    )}
                  </div>
                )}

                {/* Sources */}
                <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                  {sc.sources.map(s => (
                    <span key={s} style={{ fontSize: '10px', fontWeight: 800, padding: '3px 10px', borderRadius: '6px', background: 'var(--v4-bg)', border: '1px solid var(--v4-border)', color: 'var(--v4-text-dim)' }}>{s}</span>
                  ))}
                </div>

                {/* Job result */}
                {job && (
                  <div style={{ padding: '10px 14px', borderRadius: '10px', fontSize: '12px', fontWeight: 700, background: jobColor(job.status) + '15', border: `1px solid ${jobColor(job.status)}33`, color: jobColor(job.status), display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {job.status === 'running' && <i className="fas fa-circle-notch fa-spin"></i>}
                    {job.status === 'done' && <i className="fas fa-check-circle"></i>}
                    {job.status === 'error' && <i className="fas fa-triangle-exclamation"></i>}
                    <span style={{ flex: 1 }}>
                      {job.status === 'running' && 'Scraping in progress�'}
                      {job.status === 'done' && `Scraped ${job.result?.scraped ?? 0} items`}
                      {job.status === 'error' && job.result?.error}
                    </span>
                    {job.result?.items?.length > 0 && (
                      <button onClick={() => setPreview({ title: sc.name, items: job.result.items })} style={{ fontSize: '10px', fontWeight: 900, padding: '3px 10px', borderRadius: '6px', border: `1px solid ${jobColor(job.status)}55`, background: 'transparent', color: jobColor(job.status), cursor: 'pointer' }}>
                        PREVIEW
                      </button>
                    )}
                  </div>
                )}

                <button onClick={() => dispatch('scrape', sc.id, () => runScraper(token, sc.id))} disabled={isRunning} style={{
                  padding: '14px', borderRadius: '14px', border: 'none', cursor: isRunning ? 'not-allowed' : 'pointer',
                  background: isRunning ? 'var(--v4-border)' : sc.color, color: '#fff', fontWeight: 950, fontSize: '13px',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px',
                  opacity: isRunning ? 0.6 : 1, transition: '0.2s',
                  boxShadow: isRunning ? 'none' : `0 6px 20px ${sc.color}40`,
                }}>
                  {isRunning ? <><i className="fas fa-circle-notch fa-spin"></i> SCRAPING�</> : <><i className="fas fa-play"></i> RUN SCRAPER</>}
                </button>
              </div>
            );
          })}
        </div>
      )}

      {/* -- CLEANING TAB -- */}
      {activeTab === 'cleaning' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(380px, 1fr))', gap: '24px' }}>
          {/* Run all button */}
          <div style={{ gridColumn: '1/-1' }}>
            <button onClick={() => dispatch('clean', 'clean_all', () => runCleaningPipeline(token, 'all'))} style={{
              padding: '16px 32px', borderRadius: '16px', border: 'none', cursor: 'pointer',
              background: 'linear-gradient(135deg, #22c55e, #16a34a)', color: '#fff', fontWeight: 950, fontSize: '13px',
              display: 'flex', alignItems: 'center', gap: '10px', boxShadow: '0 8px 24px rgba(34,197,94,0.3)',
            }}>
              {jobs['clean_all']?.status === 'running'
                ? <><i className="fas fa-circle-notch fa-spin"></i> RUNNING ALL PIPELINES�</>
                : <><i className="fas fa-broom"></i> RUN ALL CLEANING PIPELINES</>}
            </button>
          </div>

          {PIPELINES.map(pl => {
            const job = jobs[`clean_${pl.id}`];
            const isRunning = job?.status === 'running';
            return (
              <div key={pl.id} style={{
                background: 'var(--v4-surface)', borderRadius: '28px', padding: '32px',
                border: `1.5px solid ${isRunning ? pl.color + '55' : 'var(--v4-border)'}`,
                display: 'flex', flexDirection: 'column', gap: '18px', position: 'relative', overflow: 'hidden',
              }}>
                <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: '3px', background: pl.color, borderRadius: '28px 28px 0 0' }} />

                <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                  <div style={{ width: '48px', height: '48px', borderRadius: '14px', background: pl.color + '15', display: 'grid', placeItems: 'center', border: `1.5px solid ${pl.color}33` }}>
                    <i className={`fas ${pl.icon}`} style={{ fontSize: '20px', color: pl.color }}></i>
                  </div>
                  <strong style={{ fontSize: '15px', fontWeight: 950 }}>{pl.name}</strong>
                </div>

                <p style={{ fontSize: '13px', color: 'var(--v4-text-dim)', fontWeight: 600, margin: 0, lineHeight: 1.6 }}>{pl.description}</p>

                {/* Pipeline steps */}
                <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                  {pl.steps.map((step, i) => (
                    <span key={i} style={{ fontSize: '10px', fontWeight: 900, padding: '4px 10px', borderRadius: '6px', background: pl.color + '15', color: pl.color, border: `1px solid ${pl.color}33` }}>
                      {i + 1}. {step}
                    </span>
                  ))}
                </div>

                {/* Result */}
                {job && (
                  <div style={{ padding: '12px 16px', borderRadius: '12px', fontSize: '12px', fontWeight: 700, background: jobColor(job.status) + '15', border: `1px solid ${jobColor(job.status)}33`, color: jobColor(job.status) }}>
                    {job.status === 'running' && <><i className="fas fa-circle-notch fa-spin" style={{ marginRight: '8px' }}></i>Pipeline running�</>}
                    {job.status === 'done' && (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                        <div><i className="fas fa-check-circle" style={{ marginRight: '8px' }}></i>
                          {job.result?.raw_count != null ? `${job.result.raw_count} raw ? ${job.result.clean_count} clean (${job.result.removed ?? job.result.outliers_removed ?? 0} removed)` : 'Complete'}
                        </div>
                        {job.result?.exported_to && <div style={{ fontSize: '10px', opacity: 0.8 }}>Exported ? {job.result.exported_to}</div>}
                        {job.result?.features_added?.length > 0 && <div style={{ fontSize: '10px', opacity: 0.8 }}>Features added: {job.result.features_added.join(', ')}</div>}
                      </div>
                    )}
                    {job.status === 'error' && <><i className="fas fa-triangle-exclamation" style={{ marginRight: '8px' }}></i>{job.result?.error}</>}
                  </div>
                )}

                <button onClick={() => dispatch('clean', `clean_${pl.id}`, () => runCleaningPipeline(token, pl.id))} disabled={isRunning} style={{
                  padding: '14px', borderRadius: '14px', border: 'none', cursor: isRunning ? 'not-allowed' : 'pointer',
                  background: isRunning ? 'var(--v4-border)' : pl.color, color: '#fff', fontWeight: 950, fontSize: '13px',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px',
                  opacity: isRunning ? 0.6 : 1, transition: '0.2s',
                  boxShadow: isRunning ? 'none' : `0 6px 20px ${pl.color}40`,
                }}>
                  {isRunning ? <><i className="fas fa-circle-notch fa-spin"></i> RUNNING�</> : <><i className="fas fa-broom"></i> RUN PIPELINE</>}
                </button>
              </div>
            );
          })}
        </div>
      )}

      {/* -- SNAPSHOTS TAB -- */}
      {activeTab === 'snapshots' && (
        <div className="v4-glass-card-premium">
          <div className="v4-card-header">
            <div>
              <h3>Production Data Snapshots</h3>
              <p style={{ fontSize: '13px', color: 'var(--v4-text-dim)', margin: '4px 0 0', fontWeight: 600 }}>
                Timestamped CSV exports from cleaning pipelines � ready for ML training.
              </p>
            </div>
            <button onClick={loadSnapshots} style={{ fontSize: '11px', fontWeight: 900, padding: '8px 16px', borderRadius: '10px', border: '1.5px solid var(--v4-border)', background: 'transparent', cursor: 'pointer', color: 'var(--v4-text-dim)' }}>
              <i className="fas fa-sync" style={{ marginRight: '6px' }}></i>Refresh
            </button>
          </div>
          {snapshots.length === 0 ? (
            <div style={{ padding: '60px', textAlign: 'center', color: 'var(--v4-text-dim)', fontWeight: 700 }}>
              <i className="fas fa-database" style={{ fontSize: '32px', marginBottom: '16px', display: 'block', opacity: 0.3 }}></i>
              No snapshots yet. Run a cleaning pipeline to generate CSV exports.
            </div>
          ) : (
            <div style={{ marginTop: '24px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {snapshots.map((snap, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '16px', padding: '16px 20px', borderRadius: '14px', background: 'var(--v4-bg)', border: '1.5px solid var(--v4-border)' }}>
                  <div style={{ width: '40px', height: '40px', borderRadius: '12px', background: '#06b6d415', display: 'grid', placeItems: 'center', border: '1.5px solid #06b6d433' }}>
                    <i className="fas fa-file-csv" style={{ color: '#06b6d4', fontSize: '18px' }}></i>
                  </div>
                  <div style={{ flex: 1 }}>
                    <strong style={{ fontSize: '13px', fontWeight: 950, display: 'block' }}>{snap.filename}</strong>
                    <div style={{ fontSize: '11px', color: 'var(--v4-text-dim)', fontWeight: 700, marginTop: '2px' }}>
                      {snap.size_kb} KB &nbsp;�&nbsp; {new Date(snap.created_at).toLocaleString()}
                    </div>
                  </div>
                  <span style={{ fontSize: '10px', fontWeight: 900, padding: '4px 12px', borderRadius: '6px', background: '#06b6d415', color: '#06b6d4', border: '1px solid #06b6d433' }}>
                    {snap.filename.split('_')[0].toUpperCase()}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* -- DATA PREVIEW MODAL -- */}
      {preview && (
        <div className="v4-modal-overlay" onClick={() => setPreview(null)}>
          <div className="v5-ultra-glass-modal animate-rise" style={{ maxWidth: '800px', maxHeight: '80vh', overflow: 'hidden', display: 'flex', flexDirection: 'column' }} onClick={e => e.stopPropagation()}>
            <div style={{ padding: '32px 32px 0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h3 style={{ margin: 0, fontSize: '20px', fontWeight: 950 }}>{preview.title}</h3>
                <p style={{ margin: '4px 0 0', fontSize: '12px', color: 'var(--v4-text-dim)', fontWeight: 700 }}>{preview.items.length} items</p>
              </div>
              <button onClick={() => setPreview(null)} style={{ background: 'var(--v4-surface)', border: '1.5px solid var(--v4-border)', borderRadius: '50%', width: '36px', height: '36px', cursor: 'pointer', fontSize: '14px' }}>?</button>
            </div>
            <div style={{ padding: '24px 32px 32px', overflowY: 'auto', flex: 1 }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {preview.items.slice(0, 30).map((item, i) => (
                  <div key={i} style={{ padding: '12px 16px', borderRadius: '12px', background: 'var(--v4-bg)', border: '1.5px solid var(--v4-border)', fontSize: '12px', fontWeight: 700 }}>
                    {Object.entries(item).slice(0, 5).map(([k, v]) => (
                      <span key={k} style={{ marginRight: '16px', color: 'var(--v4-text-dim)' }}>
                        <span style={{ color: 'var(--v4-text-main)' }}>{k}:</span> {String(v).slice(0, 40)}
                      </span>
                    ))}
                  </div>
                ))}
                {preview.items.length > 30 && (
                  <div style={{ textAlign: 'center', fontSize: '12px', color: 'var(--v4-text-dim)', fontWeight: 700, padding: '12px' }}>
                    � and {preview.items.length - 30} more items
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      <style>{`.v4-dashboard-container { display: flex; flex-direction: column; gap: 40px; padding-bottom: 80px; }`}</style>
    </div>
  );
}

