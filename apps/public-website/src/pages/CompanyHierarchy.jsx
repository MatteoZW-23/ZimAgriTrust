import React from "react";
import { Link } from "react-router-dom";

function CompanyHierarchy() {
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
          <h1>Organizational Structure</h1>
          <p>Our leadership and organizational hierarchy</p>
        </section>

        <section className="content-section">
          <h2>Executive Leadership</h2>
          <div className="leadership-grid">
            <div className="leader-card">
              <div className="leader-avatar">CEO</div>
              <div className="leader-info">
                <h3>Chief Executive Officer</h3>
                <p className="leader-title">CEO</p>
                <p className="leader-bio">Oversees overall company strategy, vision, and execution. Responsible for stakeholder relations and company growth.</p>
              </div>
            </div>
            <div className="leader-card">
              <div className="leader-avatar">CTO</div>
              <div className="leader-info">
                <h3>Chief Technology Officer</h3>
                <p className="leader-title">CTO</p>
                <p className="leader-bio">Leads technology strategy, platform development, and technical innovation. Ensures robust and scalable infrastructure.</p>
              </div>
            </div>
            <div className="leader-card">
              <div className="leader-avatar">CFO</div>
              <div className="leader-info">
                <h3>Chief Financial Officer</h3>
                <p className="leader-title">CFO</p>
                <p className="leader-bio">Manages financial operations, planning, and reporting. Oversees financial compliance and investor relations.</p>
              </div>
            </div>
            <div className="leader-card">
              <div className="leader-avatar">COO</div>
              <div className="leader-info">
                <h3>Chief Operating Officer</h3>
                <p className="leader-title">COO</p>
                <p className="leader-bio">Manages day-to-day operations, logistics coordination, and operational efficiency across all departments.</p>
              </div>
            </div>
            <div className="leader-card">
              <div className="leader-avatar">CCO</div>
              <div className="leader-info">
                <h3>Chief Commercial Officer</h3>
                <p className="leader-title">CCO</p>
                <p className="leader-bio">Leads business development, sales, marketing, and customer acquisition strategies.</p>
              </div>
            </div>
            <div className="leader-card">
              <div className="leader-avatar">CPO</div>
              <div className="leader-info">
                <h3>Chief People Officer</h3>
                <p className="leader-title">CPO</p>
                <p className="leader-bio">Oversees human resources, talent acquisition, employee development, and organizational culture.</p>
              </div>
            </div>
          </div>
        </section>

        <section className="content-section">
          <h2>Board of Directors</h2>
          <div className="board-members">
            <div className="board-member">
              <h3>Board Chairman</h3>
              <p>Provides strategic guidance and governance oversight. Ensures company acts in best interests of shareholders.</p>
            </div>
            <div className="board-member">
              <h3>Independent Director 1</h3>
              <p>Agricultural industry expert with 20+ years experience in Zimbabwe's agricultural sector.</p>
            </div>
            <div className="board-member">
              <h3>Independent Director 2</h3>
              <p>Technology and finance expert with background in fintech and digital platforms.</p>
            </div>
            <div className="board-member">
              <h3>Independent Director 3</h3>
              <p>Legal and regulatory expert specializing in corporate governance and compliance.</p>
            </div>
            <div className="board-member">
              <h3>Independent Director 4</h3>
              <p>Logistics and supply chain expert with experience in agricultural transportation.</p>
            </div>
          </div>
        </section>

        <section className="content-section">
          <h2>Departmental Structure</h2>
          <div className="departments">
            <div className="department">
              <h3>Technology Department</h3>
              <div className="sub-departments">
                <div className="sub-dept">
                  <h4>Software Engineering</h4>
                  <p>Platform development, mobile apps, web applications, and API development</p>
                </div>
                <div className="sub-dept">
                  <h4>Infrastructure & DevOps</h4>
                  <p>Cloud infrastructure, server management, deployment, and system reliability</p>
                </div>
                <div className="sub-dept">
                  <h4>Data & Analytics</h4>
                  <p>Data science, business intelligence, market analytics, and reporting</p>
                </div>
                <div className="sub-dept">
                  <h4>Quality Assurance</h4>
                  <p>Testing, quality control, bug tracking, and release management</p>
                </div>
              </div>
            </div>

            <div className="department">
              <h3>Operations Department</h3>
              <div className="sub-departments">
                <div className="sub-dept">
                  <h4>Logistics Coordination</h4>
                  <p>Transporter management, delivery coordination, and route optimization</p>
                </div>
                <div className="sub-dept">
                  <h4>Field Operations</h4>
                  <p>Farmer onboarding, field agent management, and regional coordination</p>
                </div>
                <div className="sub-dept">
                  <h4>Quality Assurance</h4>
                  <p>Product quality verification, inspection protocols, and standards enforcement</p>
                </div>
                <div className="sub-dept">
                  <h4>Customer Support</h4>
                  <p>User support, dispute resolution, and help desk operations</p>
                </div>
              </div>
            </div>

            <div className="department">
              <h3>Finance Department</h3>
              <div className="sub-departments">
                <div className="sub-dept">
                  <h4>Financial Planning</h4>
                  <p>Budgeting, forecasting, financial analysis, and strategic planning</p>
                </div>
                <div className="sub-dept">
                  <h4>Accounting</h4>
                  <p>Financial reporting, tax compliance, payroll, and accounts management</p>
                </div>
                <div className="sub-dept">
                  <h4>Treasury</h4>
                  <p>Cash management, payment processing, escrow management, and banking relations</p>
                </div>
                <div className="sub-dept">
                  <h4>Risk Management</h4>
                  <p>Financial risk assessment, insurance, and compliance monitoring</p>
                </div>
              </div>
            </div>

            <div className="department">
              <h3>Commercial Department</h3>
              <div className="sub-departments">
                <div className="sub-dept">
                  <h4>Business Development</h4>
                  <p>Partnership development, enterprise sales, and market expansion</p>
                </div>
                <div className="sub-dept">
                  <h4>Marketing</h4>
                  <p>Brand management, digital marketing, content creation, and communications</p>
                </div>
                <div className="sub-dept">
                  <h4>Sales</h4>
                  <p>User acquisition, account management, and revenue growth</p>
                </div>
                <div className="sub-dept">
                  <h4>Market Research</h4>
                  <p>Market analysis, competitor research, and trend identification</p>
                </div>
              </div>
            </div>

            <div className="department">
              <h3>People & Culture Department</h3>
              <div className="sub-departments">
                <div className="sub-dept">
                  <h4>Human Resources</h4>
                  <p>Recruitment, employee relations, benefits administration, and HR operations</p>
                </div>
                <div className="sub-dept">
                  <h4>Learning & Development</h4>
                  <p>Training programs, skill development, and career progression</p>
                </div>
                <div className="sub-dept">
                  <h4>Organizational Development</h4>
                  <p>Culture building, change management, and organizational design</p>
                </div>
                <div className="sub-dept">
                  <h4>Performance Management</h4>
                  <p>Performance reviews, goal setting, and incentive programs</p>
                </div>
              </div>
            </div>

            <div className="department">
              <h3>Legal & Compliance Department</h3>
              <div className="sub-departments">
                <div className="sub-dept">
                  <h4>Legal Affairs</h4>
                  <p>Contract management, legal advisory, and regulatory compliance</p>
                </div>
                <div className="sub-dept">
                  <h4>Compliance</h4>
                  <p>Regulatory monitoring, policy enforcement, and audit coordination</p>
                </div>
                <div className="sub-dept">
                  <h4>Corporate Governance</h4>
                  <p>Board support, governance framework, and ethical standards</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="content-section">
          <h2>Regional Structure</h2>
          <div className="regions">
            <div className="region">
              <h3>Harare Headquarters</h3>
              <p>Main office housing executive leadership, technology, and central operations teams.</p>
            </div>
            <div className="region">
              <h3>Mashonaland Regional Office</h3>
              <p>Covers Mashonaland East, Central, and West provinces with field agents and coordination teams.</p>
            </div>
            <div className="region">
              <h3>Manicaland Regional Office</h3>
              <p>Services Manicaland province with dedicated field operations and support.</p>
            </div>
            <div className="region">
              <h3>Midlands Regional Office</h3>
              <p>Covers Midlands province with regional coordination and farmer support.</p>
            </div>
            <div className="region">
              <h3>Matabeleland Regional Office</h3>
              <p>Services Matabeleland North and South provinces with comprehensive regional coverage.</p>
            </div>
            <div className="region">
              <h3>Masvingo Regional Office</h3>
              <p>Covers Masvingo province with field operations and market coordination.</p>
            </div>
            <div className="region">
              <h3>Bulawayo Regional Office</h3>
              <p>Major regional hub supporting Matabeleland and surrounding areas.</p>
            </div>
          </div>
        </section>

        <section className="content-section">
          <h2>Reporting Structure</h2>
          <div className="reporting-structure">
            <div className="reporting-level">
              <h3>Level 1: Board of Directors</h3>
              <p>Governs the company, provides strategic direction, and oversees executive performance.</p>
            </div>
            <div className="reporting-level">
              <h3>Level 2: Executive Leadership (C-Suite)</h3>
              <p>Reports to Board. Executes strategy, manages company-wide operations, and drives organizational goals.</p>
            </div>
            <div className="reporting-level">
              <h3>Level 3: Department Heads</h3>
              <p>Reports to respective executives. Leads specific functional areas and manages departmental teams.</p>
            </div>
            <div className="reporting-level">
              <h3>Level 4: Team Managers</h3>
              <p>Reports to Department Heads. Manages day-to-day team operations and project execution.</p>
            </div>
            <div className="reporting-level">
              <h3>Level 5: Individual Contributors</h3>
              <p>Reports to Team Managers. Executes specific tasks and contributes to team objectives.</p>
            </div>
          </div>
        </section>

        <section className="content-section">
          <h2>Committee Structure</h2>
          <div className="committees">
            <div className="committee">
              <h3>Executive Committee</h3>
              <p>Weekly meetings of C-Suite executives to discuss strategic decisions and operational matters.</p>
            </div>
            <div className="committee">
              <h3>Audit & Risk Committee</h3>
              <p>Board-level committee overseeing financial reporting, internal controls, and risk management.</p>
            </div>
            <div className="committee">
              <h3>Strategy Committee</h3>
              <p>Board and executive committee focused on long-term strategic planning and market expansion.</p>
            </div>
            <div className="committee">
              <h3>Compensation Committee</h3>
              <p>Board committee overseeing executive compensation, benefits, and performance incentives.</p>
            </div>
            <div className="committee">
              <h3>Governance Committee</h3>
              <p>Ensures corporate governance standards, ethical practices, and regulatory compliance.</p>
            </div>
          </div>
        </section>

        <section className="content-section cta-section">
          <h2>Join Our Team</h2>
          <p>
            We're always looking for talented individuals who share our passion for transforming agriculture in Zimbabwe.
          </p>
          <Link to="/company-profile" className="btn btn-primary btn-lg">View Open Positions</Link>
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

export default CompanyHierarchy;
