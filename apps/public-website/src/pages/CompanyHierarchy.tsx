import React from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Users, Briefcase, Building2, MapPin, CircleDot } from "lucide-react";

function CompanyHierarchy() {
 const executives = [
 { role: "Chief Executive Officer", code: "CEO", desc: "Oversees overall company strategy, vision, and execution. Responsible for stakeholder relations and company growth." },
 { role: "Chief Technology Officer", code: "CTO", desc: "Leads technology strategy, platform development, and technical innovation. Ensures robust and scalable infrastructure." },
 { role: "Chief Financial Officer", code: "CFO", desc: "Manages financial operations, planning, and reporting. Oversees financial compliance and investor relations." },
 { role: "Chief Operating Officer", code: "COO", desc: "Manages day-to-day operations, logistics coordination, and operational efficiency across all departments." },
 { role: "Chief Commercial Officer", code: "CCO", desc: "Leads business development, sales, marketing, and customer acquisition strategies." },
 { role: "Chief People Officer", code: "CPO", desc: "Oversees human resources, talent acquisition, employee development, and organizational culture." },
 ];

 const departments = [
 {
 name: "Technology",
 subs: ["Software Engineering", "Infrastructure & DevOps", "Data & Analytics", "Quality Assurance"]
 },
 {
 name: "Operations",
 subs: ["Logistics Coordination", "Field Operations", "Quality Assurance", "Customer Support"]
 },
 {
 name: "Finance",
 subs: ["Financial Planning", "Accounting", "Treasury", "Risk Management"]
 },
 {
 name: "Commercial",
 subs: ["Business Development", "Marketing", "Sales", "Market Research"]
 },
 {
 name: "People & Culture",
 subs: ["Human Resources", "Learning & Development", "Organizational Development", "Performance Management"]
 },
 {
 name: "Legal & Compliance",
 subs: ["Legal Affairs", "Compliance", "Corporate Governance"]
 },
 ];

 const regions = [
 { name: "Harare Headquarters", desc: "Main office housing executive leadership and central operations." },
 { name: "Mashonaland Regional", desc: "Covers Mashonaland East, Central, and West provinces." },
 { name: "Manicaland Regional", desc: "Services Manicaland province with dedicated operations." },
 { name: "Midlands Regional", desc: "Covers Midlands province with regional coordination." },
 { name: "Matabeleland Regional", desc: "Services Matabeleland North and South provinces." },
 { name: "Masvingo Regional", desc: "Covers Masvingo province with field operations." },
 { name: "Bulawayo Regional", desc: "Major regional hub supporting surrounding areas." },
 ];

 return (
 <div className="min-h-screen bg-earth-50">{/* Hero */}
 <section className="bg-gradient-to-br from-primary-700 to-primary-900 text-white py-16 lg:py-24"><div className="container-custom"><motion.div
 initial={{ opacity: 0, y: 20 }}
 animate={{ opacity: 1, y: 0 }}
 className="text-center max-w-3xl mx-auto"
 ><div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/10 backdrop-blur-sm mb-6"><Users className="w-4 h-4" /><span className="text-sm font-medium">Our Structure</span></div><h1 className="text-4xl md:text-5xl font-bold mb-4">Organizational Structure</h1><p className="text-xl text-primary-100">Our leadership and organizational hierarchy</p></motion.div></div></section>
{/* Executive Leadership */}
 <section className="py-16"><div className="container-custom"><div className="text-center mb-12"><h2 className="text-3xl font-bold text-earth-900 mb-4">Executive Leadership</h2><p className="text-earth-600 max-w-2xl mx-auto">Meet our C-Suite executives leading the company</p></div>
<div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">{executives.map((exec, index) => (
 <motion.div
 key={exec.code}
 initial={{ opacity: 0, y: 20 }}
 whileInView={{ opacity: 1, y: 0 }}
 viewport={{ once: true }}
 transition={{ delay: index * 0.1 }}
 className="bg-white rounded-xl p-6 shadow-sm border border-earth-100"
 ><div className="flex items-start gap-4"><div className="w-12 h-12 rounded-xl bg-primary-100 flex items-center justify-center flex-shrink-0"><span className="text-sm font-bold text-primary-700">{exec.code}</span></div><div><h3 className="font-semibold text-earth-900 mb-1">{exec.role}</h3><p className="text-sm text-earth-500 leading-relaxed">{exec.desc}</p></div></div></motion.div>))}
 </div></div></section>
{/* Board of Directors */}
 <section className="py-16 bg-white"><div className="container-custom"><div className="text-center mb-12"><h2 className="text-3xl font-bold text-earth-900 mb-4">Board of Directors</h2><p className="text-earth-600 max-w-2xl mx-auto">Independent oversight and strategic guidance</p></div>
<div className="grid md:grid-cols-2 lg:grid-cols-5 gap-4">{["Board Chairman", "Independent Director 1", "Independent Director 2", "Independent Director 3", "Independent Director 4"].map((title, index) => (
 <motion.div
 key={title}
 initial={{ opacity: 0, y: 20 }}
 whileInView={{ opacity: 1, y: 0 }}
 viewport={{ once: true }}
 transition={{ delay: index * 0.1 }}
 className="bg-earth-50 rounded-xl p-5 text-center"
 ><div className="w-10 h-10 rounded-full bg-primary-100 flex items-center justify-center mx-auto mb-3"><CircleDot className="w-5 h-5 text-primary-600" /></div><h3 className="font-medium text-earth-900 text-sm mb-2">{title}</h3><p className="text-xs text-earth-500">{index === 0 ? "Provides strategic guidance" : index === 1 ? "Agri industry expert" : index === 2 ? "Fintech background" : index === 3 ? "Legal & governance expert" : "Supply chain expert"}</p></motion.div>))}
 </div></div></section>
{/* Departments */}
 <section className="py-16"><div className="container-custom"><div className="text-center mb-12"><h2 className="text-3xl font-bold text-earth-900 mb-4">Departmental Structure</h2><p className="text-earth-600 max-w-2xl mx-auto">Our functional departments and sub-teams</p></div>
<div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">{departments.map((dept, index) => (
 <motion.div
 key={dept.name}
 initial={{ opacity: 0, y: 20 }}
 whileInView={{ opacity: 1, y: 0 }}
 viewport={{ once: true }}
 transition={{ delay: index * 0.1 }}
 className="bg-white rounded-xl p-6 shadow-sm border border-earth-100"
 ><div className="flex items-center gap-3 mb-4"><div className="w-10 h-10 rounded-lg bg-primary-100 flex items-center justify-center"><Briefcase className="w-5 h-5 text-primary-600" /></div><h3 className="font-semibold text-earth-900">{dept.name}</h3></div><div className="space-y-2">{dept.subs.map((sub) => (
 <div key={sub} className="flex items-center gap-2 text-sm text-earth-600"><div className="w-1.5 h-1.5 rounded-full bg-primary-400"></div>{sub}
 </div>))}
 </div></motion.div>))}
 </div></div></section>
{/* Regional Offices */}
 <section className="py-16 bg-white"><div className="container-custom"><div className="text-center mb-12"><h2 className="text-3xl font-bold text-earth-900 mb-4">Regional Structure</h2><p className="text-earth-600 max-w-2xl mx-auto">Our presence across Zimbabwe's provinces</p></div>
<div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">{regions.map((region, index) => (
 <motion.div
 key={region.name}
 initial={{ opacity: 0, y: 20 }}
 whileInView={{ opacity: 1, y: 0 }}
 viewport={{ once: true }}
 transition={{ delay: index * 0.1 }}
 className="bg-earth-50 rounded-xl p-5"
 ><div className="flex items-center gap-2 mb-2"><MapPin className="w-4 h-4 text-primary-600" /><h3 className="font-medium text-earth-900 text-sm">{region.name}</h3></div><p className="text-xs text-earth-500">{region.desc}</p></motion.div>))}
 </div></div></section>
{/* Reporting Structure */}
 <section className="py-16"><div className="container-custom"><div className="text-center mb-12"><h2 className="text-3xl font-bold text-earth-900 mb-4">Reporting Structure</h2><p className="text-earth-600 max-w-2xl mx-auto">Clear chain of command and accountability</p></div>
<div className="max-w-4xl mx-auto"><div className="space-y-4">{[
 { level: "Level 1", title: "Board of Directors", desc: "Governs the company and provides strategic direction" },
 { level: "Level 2", title: "Executive Leadership (C-Suite)", desc: "Executes strategy and manages company-wide operations" },
 { level: "Level 3", title: "Department Heads", desc: "Leads specific functional areas and manages teams" },
 { level: "Level 4", title: "Team Managers", desc: "Manages day-to-day team operations" },
 { level: "Level 5", title: "Individual Contributors", desc: "Executes specific tasks and contributes to objectives" },
 ].map((item, index) => (
 <motion.div
 key={item.level}
 initial={{ opacity: 0, x: -20 }}
 whileInView={{ opacity: 1, x: 0 }}
 viewport={{ once: true }}
 transition={{ delay: index * 0.1 }}
 className="flex items-center gap-4 bg-white rounded-xl p-5 shadow-sm border border-earth-100"
 ><div className="w-16 h-16 rounded-xl bg-primary-100 flex items-center justify-center flex-shrink-0"><span className="text-lg font-bold text-primary-700">{item.level.split(" ")[1]}</span></div><div><h3 className="font-semibold text-earth-900 mb-1">{item.title}</h3><p className="text-sm text-earth-500">{item.desc}</p></div></motion.div>))}
 </div></div></div></section>
{/* Committees */}
 <section className="py-16 bg-white"><div className="container-custom"><div className="text-center mb-12"><h2 className="text-3xl font-bold text-earth-900 mb-4">Committee Structure</h2><p className="text-earth-600 max-w-2xl mx-auto">Governance and oversight committees</p></div>
<div className="grid md:grid-cols-2 lg:grid-cols-5 gap-4">{[
 { name: "Executive Committee", desc: "Weekly C-Suite meetings" },
 { name: "Audit & Risk Committee", desc: "Financial oversight" },
 { name: "Strategy Committee", desc: "Long-term planning" },
 { name: "Compensation Committee", desc: "Executive benefits" },
 { name: "Governance Committee", desc: "Ethics & compliance" },
 ].map((committee, index) => (
 <motion.div
 key={committee.name}
 initial={{ opacity: 0, y: 20 }}
 whileInView={{ opacity: 1, y: 0 }}
 viewport={{ once: true }}
 transition={{ delay: index * 0.1 }}
 className="bg-gradient-to-br from-primary-50 to-primary-100 rounded-xl p-5 text-center"
 ><div className="w-10 h-10 rounded-full bg-white flex items-center justify-center mx-auto mb-3 shadow-sm"><Building2 className="w-5 h-5 text-primary-600" /></div><h3 className="font-medium text-earth-900 text-sm mb-1">{committee.name}</h3><p className="text-xs text-earth-500">{committee.desc}</p></motion.div>))}
 </div></div></section></div>);
}

export default CompanyHierarchy;
