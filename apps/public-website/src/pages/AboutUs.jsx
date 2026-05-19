import React from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Users, Target, Globe, Mail, Phone, MapPin, CheckCircle } from "lucide-react";
import logo from "../assets/logo.png";

function AboutUs() {
  const stats = [
    { number: "5,000+", label: "Farmers Onboarded", icon: Users },
    { number: "$2M+", label: "Transaction Volume", icon: Globe },
    { number: "95%", label: "Customer Satisfaction", icon: CheckCircle },
    { number: "200+", label: "Active Agents", icon: Target },
  ];

  const team = [
    { role: "Founder & CEO", desc: "Leading the vision and strategy" },
    { role: "CTO", desc: "Technology and platform development" },
    { role: "Head of Operations", desc: "Agent network and logistics" },
    { role: "Head of Agriculture", desc: "Crop quality and farmer relations" },
  ];

  const partners = [
    "EcoCash (Payment Partner)",
    "OneMoney (Payment Partner)",
    "ZAMACE (Market Data Partner)",
    "GMB (Regulatory Partner)",
    "Partner Bank (Escrow Services)",
  ];

  return (
    <div className="min-h-screen bg-earth-50">
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-primary-700 to-primary-900 text-white py-20 lg:py-28">
        <div className="container-custom">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center max-w-3xl mx-auto"
          >
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/10 backdrop-blur-sm mb-6">
              <img 
                src={logo} 
                alt="ZimAgritrust Logo" 
                className="w-4 h-4 object-contain"
              />
              <span className="text-sm font-medium">Our Story</span>
            </div>
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-6">
              Empowering Zimbabwe's <span className="text-accent-400">Agricultural Future</span>
            </h1>
            <p className="text-xl text-primary-100">
              We are building the digital infrastructure to transform how agriculture works in Zimbabwe.
            </p>
          </motion.div>
        </div>
      </section>

      {/* Mission & Vision */}
      <section className="py-16 lg:py-24">
        <div className="container-custom">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
            >
              <h2 className="text-3xl font-bold text-earth-900 mb-6">Our Mission</h2>
              <p className="text-lg text-earth-600 mb-8 leading-relaxed">
                To empower Zimbabwe's smallholder farmers by providing direct access to fair markets, 
                secure payments, and transparent trading through accessible technology.
              </p>
              
              <h2 className="text-3xl font-bold text-earth-900 mb-6">Our Vision</h2>
              <p className="text-lg text-earth-600 leading-relaxed">
                A Zimbabwe where every farmer can sell their crops at fair prices without exploitation, 
                regardless of whether they own a smartphone or have internet access.
              </p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              className="bg-white rounded-2xl p-8 shadow-lg"
            >
              <h3 className="text-xl font-bold text-earth-900 mb-4">Our Story</h3>
              <p className="text-earth-600 leading-relaxed">
                ZimAgriTrust was founded in 2026 by a team of Zimbabwean agri-tech entrepreneurs, 
                software engineers, and agricultural specialists who saw firsthand how middlemen 
                were exploiting farmers. We built a platform that works on ANY phone via USSD (*123#), 
                making fair trade accessible to every farmer in Zimbabwe.
              </p>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="py-16 bg-white">
        <div className="container-custom">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
            {stats.map((stat, index) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                className="text-center p-6 rounded-xl bg-earth-50"
              >
                <stat.icon className="w-8 h-8 text-primary-600 mx-auto mb-3" />
                <div className="text-3xl font-bold text-earth-900 mb-1">{stat.number}</div>
                <div className="text-sm text-earth-500">{stat.label}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Team */}
      <section className="py-16 lg:py-24">
        <div className="container-custom">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-earth-900 mb-4">Our Team</h2>
            <p className="text-earth-600 max-w-2xl mx-auto">
              Meet the passionate individuals driving our mission forward
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {team.map((member, index) => (
              <motion.div
                key={member.role}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                className="bg-white rounded-xl p-6 shadow-sm border border-earth-100 text-center"
              >
                <div className="w-16 h-16 rounded-full bg-primary-100 flex items-center justify-center mx-auto mb-4">
                  <Users className="w-8 h-8 text-primary-600" />
                </div>
                <h3 className="font-semibold text-earth-900 mb-2">{member.role}</h3>
                <p className="text-sm text-earth-500">{member.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Contact & Partners */}
      <section className="py-16 bg-white">
        <div className="container-custom">
          <div className="grid lg:grid-cols-2 gap-12">
            {/* Contact */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
            >
              <h2 className="text-2xl font-bold text-earth-900 mb-6">Contact Information</h2>
              <div className="space-y-4">
                <div className="flex items-center gap-3 text-earth-600">
                  <Mail className="w-5 h-5 text-primary-600" />
                  <span>info@zimagritrust.com</span>
                </div>
                <div className="flex items-center gap-3 text-earth-600">
                  <Phone className="w-5 h-5 text-primary-600" />
                  <span>+263 71 735 8956</span>
                </div>
                <div className="flex items-center gap-3 text-earth-600">
                  <MapPin className="w-5 h-5 text-primary-600" />
                  <span>123 Samora Machel Ave, Harare, Zimbabwe</span>
                </div>
              </div>
            </motion.div>

            {/* Partners */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
            >
              <h2 className="text-2xl font-bold text-earth-900 mb-6">Our Partners</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {partners.map((partner) => (
                  <div key={partner} className="flex items-center gap-2 text-earth-600">
                    <CheckCircle className="w-4 h-4 text-primary-500 flex-shrink-0" />
                    <span className="text-sm">{partner}</span>
                  </div>
                ))}
              </div>
            </motion.div>
          </div>
        </div>
      </section>
    </div>
  );
}

export default AboutUs;
