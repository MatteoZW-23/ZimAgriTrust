import React from "react";
import { Link } from "react-router-dom";

function PrivacyPolicy() {
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
          <h1>Privacy Policy</h1>
          <p>Last updated: May 2026</p>
        </section>

        <section className="content-section">
          <h2>Introduction</h2>
          <p>
            ZimAgritrust ("we", "our", or "us") is committed to protecting your privacy. This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you use our agricultural marketplace platform. Please read this policy carefully.
          </p>
          <p>
            By using ZimAgritrust, you agree to the collection and use of information in accordance with this policy. If you do not agree with our policies and practices, please do not use our platform.
          </p>
        </section>

        <section className="content-section">
          <h2>1. Information We Collect</h2>
          <h3>1.1 Personal Information</h3>
          <p>
            We collect information you provide directly to us, including:
          </p>
          <ul className="policy-list">
            <li>Name, contact information (phone number, email address)</li>
            <li>Physical address and location data</li>
            <li>Identification documents for verification</li>
            <li>Bank account details for payments</li>
            <li>Business registration information (for business accounts)</li>
            <li>Profile information and photos</li>
          </ul>

          <h3>1.2 Transaction Information</h3>
          <p>
            We collect information related to your transactions, including:
          </p>
          <ul className="policy-list">
            <li>Order history and details</li>
            <li>Payment information (processed securely through third-party providers)</li>
            <li>Delivery addresses and logistics information</li>
            <li>Communication with other users</li>
            <li>Dispute resolution records</li>
          </ul>

          <h3>1.3 Technical Information</h3>
          <p>
            We automatically collect technical information when you use our platform, including:
          </p>
          <ul className="policy-list">
            <li>IP address and device information</li>
            <li>Browser type and version</li>
            <li>Operating system</li>
            <li>Pages visited and time spent on pages</li>
            <li>Referring websites</li>
            <li>Mobile device identifiers</li>
          </ul>

          <h3>1.4 Location Information</h3>
          <p>
            With your consent, we may collect location information to:
          </p>
          <ul className="policy-list">
            <li>Provide location-based services</li>
            <li>Match buyers and sellers in the same region</li>
            <li>Coordinate logistics and delivery</li>
            <li>Improve our services</li>
          </ul>
        </section>

        <section className="content-section">
          <h2>2. How We Use Your Information</h2>
          <p>
            We use the collected information for various purposes, including:
          </p>
          <ul className="policy-list">
            <li><strong>Service Provision:</strong> To provide, maintain, and improve our platform services</li>
            <li><strong>Transaction Processing:</strong> To process transactions, payments, and deliveries</li>
            <li><strong>Verification:</strong> To verify user identity and prevent fraud</li>
            <li><strong>Communication:</strong> To send you notifications, updates, and support messages</li>
            <li><strong>Security:</strong> To detect, prevent, and address technical issues and fraudulent activity</li>
            <li><strong>Personalization:</strong> To personalize your experience and provide relevant recommendations</li>
            <li><strong>Analytics:</strong> To analyze usage patterns and improve our platform</li>
            <li><strong>Legal Compliance:</strong> To comply with legal obligations and regulations</li>
          </ul>
        </section>

        <section className="content-section">
          <h2>3. Information Sharing</h2>
          <h3>3.1 With Other Users</h3>
          <p>
            We share limited information with other users as necessary for transactions, including:
          </p>
          <ul className="policy-list">
            <li>Your profile information (name, location, verification status)</li>
            <li>Contact information necessary for transaction completion</li>
            <li>Transaction-related communications</li>
          </ul>
          <p>
            We do not share sensitive information like bank details or full identification documents with other users.
          </p>

          <h3>3.2 With Service Providers</h3>
          <p>
            We share information with third-party service providers who perform services on our behalf, including:
          </p>
          <ul className="policy-list">
            <li>Payment processors for transaction processing</li>
            <li>Logistics providers for delivery services</li>
            <li>Cloud hosting providers for platform infrastructure</li>
            <li>Analytics providers for platform analysis</li>
            <li>Communication providers for messaging services</li>
          </ul>
          <p>
            These service providers are bound by confidentiality agreements and only use your information for the specific services they provide.
          </p>

          <h3>3.3 Legal Requirements</h3>
          <p>
            We may disclose your information when required by law or to protect our rights, including:
          </p>
          <ul className="policy-list">
            <li>Compliance with legal obligations</li>
            <li>Response to lawful requests from authorities</li>
            <li>Protection of our rights, property, or safety</li>
            <li>Prevention of fraud or illegal activities</li>
          </ul>

          <h3>3.4 Business Transfers</h3>
          <p>
            In the event of a merger, acquisition, or sale of assets, user information may be transferred as part of the transaction. We will notify you of any such transfer.
          </p>
        </section>

        <section className="content-section">
          <h2>4. Data Security</h2>
          <p>
            We implement appropriate security measures to protect your information, including:
          </p>
          <ul className="policy-list">
            <li><strong>Encryption:</strong> Data is encrypted in transit and at rest using industry-standard encryption</li>
            <li><strong>Access Control:</strong> Strict access controls limit who can access your information</li>
            <li><strong>Secure Storage:</strong> Data is stored in secure, SOC-compliant data centers</li>
            <li><strong>Regular Audits:</strong> We conduct regular security audits and vulnerability assessments</li>
            <li><strong>Employee Training:</strong> All employees undergo security training and sign confidentiality agreements</li>
          </ul>
          <p>
            Despite our best efforts, no method of transmission over the internet is 100% secure. We cannot guarantee absolute security of your information.
          </p>
        </section>

        <section className="content-section">
          <h2>5. Data Retention</h2>
          <p>
            We retain your information for as long as necessary to provide our services and fulfill legal obligations:
          </p>
          <ul className="policy-list">
            <li><strong>Account Information:</strong> Retained while your account is active</li>
            <li><strong>Transaction Records:</strong> Retained for 7 years for legal and tax purposes</li>
            <li><strong>Communication Logs:</strong> Retained for 2 years for dispute resolution purposes</li>
            <li><strong>Analytics Data:</strong> Retained in anonymized form for platform improvement</li>
          </ul>
          <p>
            Upon account closure, we delete or anonymize your personal information except as required by law or for legitimate business purposes.
          </p>
        </section>

        <section className="content-section">
          <h2>6. Your Rights and Choices</h2>
          <p>
            You have certain rights regarding your personal information:
          </p>
          <ul className="policy-list">
            <li><strong>Access:</strong> Request access to your personal information</li>
            <li><strong>Correction:</strong> Request correction of inaccurate information</li>
            <li><strong>Deletion:</strong> Request deletion of your personal information (subject to legal obligations)</li>
            <li><strong>Portability:</strong> Request transfer of your data to another service</li>
            <li><strong>Objection:</strong> Object to processing of your information for certain purposes</li>
            <li><strong>Consent Withdrawal:</strong> Withdraw consent for processing where consent is the legal basis</li>
          </ul>
          <p>
            To exercise these rights, contact us at privacy@zagritrust.com
          </p>
        </section>

        <section className="content-section">
          <h2>7. Cookies and Tracking</h2>
          <h3>7.1 Cookies</h3>
          <p>
            We use cookies and similar technologies to improve your experience, including:
          </p>
          <ul className="policy-list">
            <li>Essential cookies for platform functionality</li>
            <li>Authentication cookies to keep you logged in</li>
            <li>Analytics cookies to understand platform usage</li>
            <li>Preference cookies to remember your settings</li>
          </ul>

          <h3>7.2 Cookie Control</h3>
          <p>
            You can control cookies through your browser settings. However, disabling essential cookies may affect platform functionality.
          </p>
        </section>

        <section className="content-section">
          <h2>8. Third-Party Links</h2>
          <p>
            Our platform may contain links to third-party websites. We are not responsible for the privacy practices of these third parties. We encourage you to review their privacy policies.
          </p>
        </section>

        <section className="content-section">
          <h2>9. Children's Privacy</h2>
          <p>
            Our platform is not intended for children under 18. We do not knowingly collect personal information from children. If we become aware of such collection, we will take steps to delete it.
          </p>
        </section>

        <section className="content-section">
          <h2>10. International Data Transfers</h2>
          <p>
            Your information is primarily stored and processed in Zimbabwe. We may transfer data to other countries for processing purposes, ensuring appropriate safeguards are in place to protect your information.
          </p>
        </section>

        <section className="content-section">
          <h2>11. Changes to This Policy</h2>
          <p>
            We may update this Privacy Policy from time to time. We will notify you of material changes by posting the new policy on our platform and sending you an email notification. Continued use of the platform after changes constitutes acceptance.
          </p>
        </section>

        <section className="content-section">
          <h2>12. Contact Information</h2>
          <p>
            If you have questions about this Privacy Policy or our data practices, please contact us:
          </p>
          <p>privacy@zagritrust.com</p>
          <p>+263788272020</p>
          <p>Harare, Zimbabwe</p>
        </section>

        <section className="content-section cta-section">
          <h2>Questions About Your Privacy?</h2>
          <p>
            If you have questions about how we handle your data, please contact our privacy team.
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

export default PrivacyPolicy;
