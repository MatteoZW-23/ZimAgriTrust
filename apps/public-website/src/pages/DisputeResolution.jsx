import React from "react";
import { Link } from "react-router-dom";

function DisputeResolution() {
  return (
    <div className="page">
      <header className="header">
        <div className="logo">
          <img src="/logo.png" alt="ZimAgritrust Logo" style={{height: '40px', width: 'auto'}} />
        </div>
        <h1>ZimAgritrust</h1>
        <nav className="nav-links">
          <Link to="/">Home</Link>
          <Link to="/about">About</Link>
          <Link to="/company-profile">Company</Link>
          <Link to="/dispute-resolution">Disputes</Link>
          <Link to="/terms">Terms</Link>
          <Link to="/privacy">Privacy</Link>
        </nav>
      </header>

      <main className="page-content">
        <section className="page-hero">
          <h1>Dispute Resolution Process</h1>
          <p>Fair, transparent, and efficient resolution of any conflicts</p>
        </section>

        <section className="content-section">
          <h2>Overview</h2>
          <p>
            At ZimAgritrust, we understand that disputes may occasionally arise in the course of business transactions. Our dispute resolution process is designed to be fair, transparent, and efficient, ensuring that all parties are heard and conflicts are resolved promptly.
          </p>
          <p>
            We have established a comprehensive dispute resolution framework that includes multiple stages of escalation, clear timelines, and impartial mediation to ensure satisfactory outcomes for all parties involved.
          </p>
        </section>

        <section className="content-section">
          <h2>Types of Disputes</h2>
          <div className="dispute-types">
            <div className="dispute-type">
              <h3>Quality Disputes</h3>
              <p>Disagreements regarding the quality or condition of delivered agricultural products.</p>
            </div>
            <div className="dispute-type">
              <h3>Quantity Disputes</h3>
              <p>Discrepancies between ordered and delivered quantities of products.</p>
            </div>
            <div className="dispute-type">
              <h3>Payment Disputes</h3>
              <p>Issues related to payment amounts, timing, or payment failures.</p>
            </div>
            <div className="dispute-type">
              <h3>Delivery Disputes</h3>
              <p>Problems with delivery timing, location, or transportation issues.</p>
            </div>
            <div className="dispute-type">
              <h3>Contract Disputes</h3>
              <p>Misunderstandings or disagreements about contract terms and conditions.</p>
            </div>
            <div className="dispute-type">
              <h3>Account Disputes</h3>
              <p>Issues related to account access, verification, or account status.</p>
            </div>
          </div>
        </section>

        <section className="content-section">
          <h2>Dispute Resolution Process</h2>
          <div className="process-steps">
            <div className="process-step">
              <div className="step-number">1</div>
              <div className="step-content">
                <h3>Direct Communication</h3>
                <p>First, attempt to resolve the dispute directly with the other party through our in-platform messaging system. Most disputes can be resolved through open communication.</p>
                <p className="step-timeline">Timeline: Up to 48 hours</p>
              </div>
            </div>
            <div className="process-step">
              <div className="step-number">2</div>
              <div className="step-content">
                <h3>File a Dispute</h3>
                <p>If direct communication doesn't resolve the issue, file a formal dispute through our platform. Provide detailed information, evidence, and your desired resolution.</p>
                <p className="step-timeline">Timeline: Immediate filing required</p>
              </div>
            </div>
            <div className="process-step">
              <div className="step-number">3</div>
              <div className="step-content">
                <h3>Platform Mediation</h3>
                <p>Our dispute resolution team will review the case and mediate between parties. We may request additional information or evidence from both sides.</p>
                <p className="step-timeline">Timeline: 3-5 business days</p>
              </div>
            </div>
            <div className="process-step">
              <div className="step-number">4</div>
              <div className="step-content">
                <h3>Evidence Review</h3>
                <p>Both parties submit evidence including photos, documents, delivery receipts, and communication logs. Our team objectively reviews all materials.</p>
                <p className="step-timeline">Timeline: 2-3 business days</p>
              </div>
            </div>
            <div className="process-step">
              <div className="step-number">5</div>
              <div className="step-content">
                <h3>Decision & Resolution</h3>
                <p>Based on evidence and platform policies, we issue a binding decision. This may include refunds, partial payments, or other remedies.</p>
                <p className="step-timeline">Timeline: 1-2 business days</p>
              </div>
            </div>
            <div className="process-step">
              <div className="step-number">6</div>
              <div className="step-content">
                <h3>Appeal Process</h3>
                <p>If either party disagrees with the decision, they may appeal within 7 days with new evidence. Appeals are reviewed by a senior dispute resolution officer.</p>
                <p className="step-timeline">Timeline: 5-7 business days</p>
              </div>
            </div>
          </div>
        </section>

        <section className="content-section">
          <h2>Filing a Dispute</h2>
          <div className="filing-guide">
            <h3>Required Information</h3>
            <ul className="requirements-list">
              <li>Transaction ID and date</li>
              <li>Detailed description of the dispute</li>
              <li>Evidence (photos, documents, screenshots)</li>
              <li>Communication history with the other party</li>
              <li>Desired resolution or outcome</li>
              <li>Contact information for follow-up</li>
            </ul>

            <h3>How to File</h3>
            <ol className="steps-list">
              <li>Log into your ZimAgritrust account</li>
              <li>Navigate to the transaction in question</li>
              <li>Click "Report Issue" or "File Dispute"</li>
              <li>Complete the dispute form with all required information</li>
              <li>Upload supporting evidence</li>
              <li>Submit and await confirmation</li>
            </ol>
          </div>
        </section>

        <section className="content-section">
          <h2>Escrow Protection</h2>
          <p>
            All payments on ZimAgritrust are held in secure escrow until the transaction is successfully completed. This provides protection for both parties:
          </p>
          <div className="escrow-info">
            <div className="escrow-point">
              <h4>For Buyers</h4>
              <p>Payment is only released to the farmer after you confirm delivery and quality of products.</p>
            </div>
            <div className="escrow-point">
              <h4>For Farmers</h4>
              <p>Payment is guaranteed once delivery is confirmed, protecting against non-payment.</p>
            </div>
            <div className="escrow-point">
              <h4>During Disputes</h4>
              <p>Escrow funds are held until the dispute is resolved, ensuring fair outcomes.</p>
            </div>
          </div>
        </section>

        <section className="content-section">
          <h2>Resolution Outcomes</h2>
          <div className="outcomes">
            <div className="outcome">
              <h3>Full Refund</h3>
              <p>Buyer receives full refund if product quality or delivery doesn't meet agreed terms.</p>
            </div>
            <div className="outcome">
              <h3>Partial Refund</h3>
              <p>Partial refund when there are minor issues but the transaction is mostly satisfactory.</p>
            </div>
            <div className="outcome">
              <h3>Replacement</h3>
              <p>Farmer may be required to replace the product at their expense.</p>
            </div>
            <div className="outcome">
              <h3>Compensation</h3>
              <p>Additional compensation may be awarded for damages or inconvenience caused.</p>
            </div>
            <div className="outcome">
              <h3>Account Action</h3>
              <p>Repeated violations may result in account suspension or termination.</p>
            </div>
          </div>
        </section>

        <section className="content-section">
          <h2>Timeline Guarantees</h2>
          <div className="timeline-table">
            <div className="timeline-row">
              <span className="timeline-stage">Direct Communication</span>
              <span className="timeline-time">48 hours</span>
            </div>
            <div className="timeline-row">
              <span className="timeline-stage">Initial Dispute Review</span>
              <span className="timeline-time">24 hours</span>
            </div>
            <div className="timeline-row">
              <span className="timeline-stage">Mediation Process</span>
              <span className="timeline-time">3-5 business days</span>
            </div>
            <div className="timeline-row">
              <span className="timeline-stage">Evidence Collection</span>
              <span className="timeline-time">2-3 business days</span>
            </div>
            <div className="timeline-row">
              <span className="timeline-stage">Final Decision</span>
              <span className="timeline-time">1-2 business days</span>
            </div>
            <div className="timeline-row">
              <span className="timeline-stage">Appeal Review</span>
              <span className="timeline-time">5-7 business days</span>
            </div>
          </div>
        </section>

        <section className="content-section">
          <h2>Fees and Costs</h2>
          <p>
            ZimAgritrust does not charge fees for standard dispute resolution. However:
          </p>
          <ul className="fees-list">
            <li>Frivolous or malicious disputes may incur penalties</li>
            <li>External arbitration (if required) may have associated costs</li>
            <li>Legal fees are the responsibility of the initiating party unless otherwise determined</li>
          </ul>
        </section>

        <section className="content-section">
          <h2>Contact Dispute Resolution</h2>
          <div className="contact-info">
            <p>For urgent disputes or questions about the process:</p>
            <p>disputes@zagritrust.com</p>
            <p>+263788272020 (Dispute Hotline)</p>
            <p>Monday - Friday, 8:00 AM - 5:00 PM</p>
          </div>
        </section>

        <section className="content-section cta-section">
          <h2>Need to File a Dispute?</h2>
          <p>
            Log into your account and navigate to your transaction history to begin the dispute resolution process.
          </p>
          <Link to="/" className="btn btn-primary btn-lg">Go to Dashboard</Link>
        </section>
      </main>

      <footer className="footer">
        <div className="footer-content">
          <div className="footer-section">
            <div className="footer-logo">
              <div className="logo">
                <img src="/logo.png" alt="ZimAgritrust Logo" style={{height: '40px', width: 'auto'}} />
              </div>
              <h3>ZimAgritrust</h3>
            </div>
            <p>Zimbabwe's trusted agricultural marketplace platform.</p>
          </div>
          <div className="footer-section">
            <h4>Quick Links</h4>
            <Link to="/">Home</Link>
            <Link to="/about">About Us</Link>
            <Link to="/company-profile">Company Profile</Link>
          </div>
          <div className="footer-section">
            <h4>Company</h4>
            <Link to="/company-hierarchy">Organization</Link>
            <Link to="/dispute-resolution">Dispute Resolution</Link>
            <Link to="/terms">Terms of Service</Link>
            <Link to="/privacy">Privacy Policy</Link>
          </div>
          <div className="footer-section">
            <h4>Contact</h4>
            <p>+263788272020</p>
            <p>mathew@zagritrust.com</p>
            <p>Harare, Zimbabwe</p>
          </div>
        </div>
        <div className="footer-bottom">
          <p>&copy; 2026 ZimAgritrust. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}

export default DisputeResolution;
