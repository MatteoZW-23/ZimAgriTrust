import React from "react";
import { Link } from "react-router-dom";

function TermsConditions() {
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
          <h1>Terms of Service</h1>
          <p>Last updated: May 2026</p>
        </section>

        <section className="content-section">
          <h2>Agreement to Terms</h2>
          <p>
            By accessing or using ZimAgritrust services, you agree to be bound by these Terms of Service. If you do not agree to these terms, please do not use our platform. We reserve the right to modify these terms at any time, and continued use of the platform constitutes acceptance of any changes.
          </p>
        </section>

        <section className="content-section">
          <h2>1. Account Registration and Verification</h2>
          <h3>1.1 Eligibility</h3>
          <p>
            You must be at least 18 years old to create an account on ZimAgritrust. By registering, you represent that you are legally capable of entering into binding contracts.
          </p>
          <h3>1.2 Account Information</h3>
          <p>
            You agree to provide accurate, current, and complete information during registration. You are responsible for maintaining the confidentiality of your account credentials and for all activities that occur under your account.
          </p>
          <h3>1.3 Verification</h3>
          <p>
            All users must complete verification before conducting transactions. This may include providing identification documents, business registration, and other relevant information. False or misleading information will result in account termination.
          </p>
          <h3>1.4 Single Account</h3>
          <p>
            Each individual or entity may maintain only one account. Multiple accounts for the same entity are prohibited and may result in suspension of all associated accounts.
          </p>
        </section>

        <section className="content-section">
          <h2>2. User Responsibilities</h2>
          <h3>2.1 Accurate Listings</h3>
          <p>
            Farmers must provide accurate descriptions of products, including quality, quantity, and condition. Misrepresentation of products is strictly prohibited and may result in account termination.
          </p>
          <h3>2.2 Fulfillment of Orders</h3>
          <p>
            Once an order is confirmed, sellers are obligated to fulfill the transaction according to the agreed terms. Failure to deliver without valid reason may result in penalties and account suspension.
          </p>
          <h3>2.3 Payment Obligations</h3>
          <p>
            Buyers must pay for orders in accordance with agreed payment terms. Non-payment without valid reason may result in account restrictions and legal action.
          </p>
          <h3>2.4 Professional Conduct</h3>
          <p>
            All users must conduct themselves professionally and respectfully. Harassment, abuse, or inappropriate behavior toward other users or staff will not be tolerated.
          </p>
        </section>

        <section className="content-section">
          <h2>3. Transaction Rules</h2>
          <h3>3.1 Escrow System</h3>
          <p>
            All transactions are processed through our secure escrow system. Payments are held until delivery is confirmed and both parties are satisfied. This protects both buyers and sellers.
          </p>
          <h3>3.2 Delivery Standards</h3>
          <p>
            Sellers must ensure products are delivered in the agreed condition within the specified timeframe. Delivery must be confirmed by the buyer through the platform.
          </p>
          <h3>3.3 Quality Standards</h3>
          <p>
            Products must meet the quality standards described in the listing. Any significant deviation from described quality may be grounds for dispute resolution and refund.
          </p>
          <h3>3.4 Cancellation Policy</h3>
          <p>
            Orders may be cancelled before shipment without penalty. After shipment, cancellations require mutual agreement or determination through dispute resolution.
          </p>
        </section>

        <section className="content-section">
          <h2>4. Fees and Payments</h2>
          <h3>4.1 Platform Fees</h3>
          <p>
            ZimAgritrust charges a transaction fee of 3% on the total transaction value. This fee is deducted from the payment before release to the seller.
          </p>
          <h3>4.2 Payment Processing</h3>
          <p>
            Payment processing fees may apply depending on the payment method used. These fees are disclosed at the time of payment.
          </p>
          <h3>4.3 Withdrawal Fees</h3>
          <p>
            Standard withdrawals to bank accounts are free. Expedited withdrawals may incur additional fees.
          </p>
          <h3>4.4 Fee Changes</h3>
          <p>
            ZimAgritrust reserves the right to modify fees with 30 days notice. Changes will not apply to existing transactions at the time of notice.
          </p>
        </section>

        <section className="content-section">
          <h2>5. Prohibited Activities</h2>
          <h3>5.1 Illegal Activities</h3>
          <p>
            Use of the platform for any illegal activities, including but not limited to fraud, money laundering, or sale of illegal goods, is strictly prohibited.
          </p>
          <h3>5.2 False Information</h3>
          <p>
            Providing false, misleading, or deceptive information is prohibited. This includes product descriptions, user information, and transaction details.
          </p>
          <h3>5.3 System Manipulation</h3>
          <p>
            Any attempt to manipulate the platform, including creating fake accounts, fake transactions, or exploiting vulnerabilities, is prohibited.
          </p>
          <h3>5.4 Outside Transactions</h3>
          <p>
            Conducting transactions outside the platform to avoid fees is prohibited. This undermines our ability to provide protection and support.
          </p>
          <h3>5.5 Spam and Abuse</h3>
          <p>
            Sending unsolicited messages, spam, or engaging in abusive behavior toward other users is prohibited.
          </p>
        </section>

        <section className="content-section">
          <h2>6. Intellectual Property</h2>
          <h3>6.1 Platform Content</h3>
          <p>
            All content on the ZimAgritrust platform, including text, graphics, logos, and software, is our intellectual property or licensed to us. Unauthorized use is prohibited.
          </p>
          <h3>6.2 User Content</h3>
          <p>
            By posting content to the platform, you grant us a non-exclusive, royalty-free license to use, display, and distribute that content for platform purposes.
          </p>
          <h3>6.3 Trademarks</h3>
          <p>
            ZimAgritrust and related logos are trademarks of ZimAgritrust. Use of our trademarks without permission is prohibited.
          </p>
        </section>

        <section className="content-section">
          <h2>7. Privacy and Data Protection</h2>
          <p>
            Your privacy is important to us. Please refer to our Privacy Policy for detailed information about how we collect, use, and protect your personal data. By using our platform, you consent to our data practices as described in the Privacy Policy.
          </p>
        </section>

        <section className="content-section">
          <h2>8. Dispute Resolution</h2>
          <h3>8.1 Platform Disputes</h3>
          <p>
            All disputes related to platform transactions should first be resolved through our internal dispute resolution process. Details are available in our Dispute Resolution policy.
          </p>
          <h3>8.2 Binding Decisions</h3>
          <p>
            Decisions made through our dispute resolution process are binding on both parties, subject to the appeal process outlined in the Dispute Resolution policy.
          </p>
          <h3>8.3 Legal Action</h3>
          <p>
            Users waive the right to pursue class action lawsuits and agree to resolve disputes through individual arbitration or small claims court where appropriate.
          </p>
        </section>

        <section className="content-section">
          <h2>9. Limitation of Liability</h2>
          <p>
            ZimAgritrust is not liable for any indirect, incidental, special, or consequential damages arising from use of the platform. Our total liability is limited to the amount of fees paid by the affected user in the preceding 12 months.
          </p>
          <p>
            We do not guarantee uninterrupted or error-free operation of the platform. We are not responsible for losses resulting from platform downtime or technical issues.
          </p>
        </section>

        <section className="content-section">
          <h2>10. Account Suspension and Termination</h2>
          <h3>10.1 Suspension</h3>
          <p>
            We reserve the right to suspend accounts suspected of violating these terms. Suspended accounts may be reinstated after investigation and remediation.
          </p>
          <h3>10.2 Termination</h3>
          <p>
            We may terminate accounts for repeated or serious violations of these terms. Terminated users forfeit any remaining balances and may be prohibited from creating new accounts.
          </p>
          <h3>10.3 User Termination</h3>
          <p>
            Users may terminate their accounts at any time. Upon termination, pending transactions will be completed, and remaining balances will be withdrawn according to our withdrawal policy.
          </p>
        </section>

        <section className="content-section">
          <h2>11. Indemnification</h2>
          <p>
            You agree to indemnify and hold harmless ZimAgritrust, its officers, directors, employees, and agents from any claims, damages, or expenses arising from your use of the platform or violation of these terms.
          </p>
        </section>

        <section className="content-section">
          <h2>12. Governing Law</h2>
          <p>
            These terms are governed by the laws of Zimbabwe. Any legal proceedings related to these terms shall be conducted in the courts of Harare, Zimbabwe.
          </p>
        </section>

        <section className="content-section">
          <h2>13. Modifications to Terms</h2>
          <p>
            We reserve the right to modify these terms at any time. Material changes will be communicated to users via email and platform notifications. Continued use of the platform after changes constitutes acceptance.
          </p>
        </section>

        <section className="content-section">
          <h2>14. Contact Information</h2>
          <p>
            For questions about these Terms of Service, please contact us:
          </p>
          <p>legal@zagritrust.com</p>
          <p>+263788272020</p>
          <p>Harare, Zimbabwe</p>
        </section>

        <section className="content-section cta-section">
          <h2>Questions About Our Terms?</h2>
          <p>
            If you have questions about these Terms of Service, please contact our legal team for clarification.
          </p>
          <Link to="/about" className="btn btn-primary btn-lg">Contact Us</Link>
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

export default TermsConditions;
