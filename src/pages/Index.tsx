import { useEffect } from 'react';
import { Header } from '@/components/Header.tsx';
import Hero from '@/components/Hero';
import FeaturesSection from '@/components/FeaturesSection';
import AnimatedBackground from '@/components/AnimatedBackground';

const Index = () => {
  useEffect(() => {
    document.title = "Edumate - AI-Powered Language Learning";
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-b from-white to-slate-50">
      <AnimatedBackground />
      <Header />
      <main>
        <Hero />
        <FeaturesSection />
        
        <section className="py-20 px-6" id="how-it-works">
          <div className="max-w-7xl mx-auto text-center">
            <span className="text-sm font-medium text-edumate-500 uppercase tracking-wider">How It Works</span>
            <h2 className="mt-2 mb-10 text-balance">Seamless Learning Experience</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-12 max-w-5xl mx-auto">
              {[
                {
                  step: "01",
                  title: "Speak or Write",
                  description: "Use your voice or upload written content to begin the learning process."
                },
                {
                  step: "02",
                  title: "AI Analysis",
                  description: "Our advanced AI instantly analyzes your pronunciation, grammar, and comprehension."
                },
                {
                  step: "03",
                  title: "Detailed Feedback",
                  description: "Receive personalized suggestions and improvements to enhance your skills."
                }
              ].map((step, index) => (
                <div key={index} className="flex flex-col items-center">
                  <div className="w-14 h-14 rounded-full bg-edumate-50 flex items-center justify-center border border-edumate-100 mb-6">
                    <span className="text-edumate-500 font-medium">{step.step}</span>
                  </div>
                  <h3 className="text-xl font-medium mb-3 text-edumate-900">{step.title}</h3>
                  <p className="text-slate-600 text-balance">{step.description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>
        
        <section className="py-20 px-6 bg-edumate-50" id="contact">
          <div className="max-w-7xl mx-auto">
            <div className="glass-panel p-8 sm:p-12">
              <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
                <div className="lg:col-span-3 space-y-6">
                  <div>
                    <span className="text-sm font-medium text-edumate-500 uppercase tracking-wider">Ready to Start?</span>
                    <h2 className="mt-2 text-balance">Begin Your Learning Journey Today</h2>
                  </div>
                  <p className="text-xl text-slate-600 text-balance">
                    Join thousands of learners who have already transformed their language skills with Edumate.
                  </p>
                  <div className="flex flex-wrap gap-4">
                    <button className="px-8 py-3 bg-edumate-500 text-white rounded-lg font-medium hover:bg-edumate-600 transition-all shadow-lg hover:shadow-xl hover:shadow-edumate-200/20 focus:outline-none focus:ring-2 focus:ring-edumate-500 focus:ring-offset-2">
                      Get Started
                    </button>
                    <button className="px-8 py-3 bg-white text-edumate-700 rounded-lg font-medium border border-edumate-100 hover:border-edumate-300 transition-all">
                      Contact Sales
                    </button>
                  </div>
                </div>
                <div className="lg:col-span-2">
                  <form className="space-y-4">
                    <div>
                      <label htmlFor="email" className="block text-sm font-medium text-edumate-700 mb-1">Email</label>
                      <input
                        type="email"
                        id="email"
                        className="w-full px-4 py-3 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-edumate-500"
                        placeholder="you@example.com"
                      />
                    </div>
                    <div>
                      <label htmlFor="message" className="block text-sm font-medium text-edumate-700 mb-1">Message</label>
                      <textarea
                        id="message"
                        rows={4}
                        className="w-full px-4 py-3 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-edumate-500"
                        placeholder="How can we help you?"
                      ></textarea>
                    </div>
                    <button type="submit" className="w-full py-3 bg-edumate-500 text-white rounded-lg font-medium hover:bg-edumate-600 transition-all">
                      Send Message
                    </button>
                  </form>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>
      
      <footer className="bg-white py-12 px-6 border-t border-slate-100">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div className="md:col-span-2">
              <div className="flex items-center space-x-2 mb-4">
                <div className="w-8 h-8 bg-edumate-500 rounded-lg flex items-center justify-center">
                  <span className="text-white font-semibold text-lg">E</span>
                </div>
                <span className="text-xl font-medium text-edumate-900">Edumate</span>
              </div>
              <p className="text-slate-600 max-w-md text-balance">
                Revolutionizing language learning with AI-powered speech and text analysis for enhanced educational outcomes.
              </p>
            </div>
            
            {[
              {
                title: "Product",
                links: ["Features", "Pricing", "Testimonials", "FAQ"]
              },
              {
                title: "Company",
                links: ["About", "Blog", "Careers", "Contact"]
              }
            ].map((column, index) => (
              <div key={index}>
                <h4 className="font-medium text-edumate-900 mb-4">{column.title}</h4>
                <ul className="space-y-3">
                  {column.links.map((link, i) => (
                    <li key={i}>
                      <a href="#" className="text-slate-600 hover:text-edumate-500 transition-colors">
                        {link}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
          
          <div className="mt-12 pt-8 border-t border-slate-100 flex flex-col md:flex-row justify-between items-center">
            <p className="text-slate-500 text-sm">
              © {new Date().getFullYear()} Edumate. All rights reserved.
            </p>
            <div className="flex space-x-6 mt-4 md:mt-0">
              {["Privacy Policy", "Terms of Service", "Cookie Policy"].map((item, index) => (
                <a key={index} href="#" className="text-sm text-slate-500 hover:text-edumate-500 transition-colors">
                  {item}
                </a>
              ))}
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Index;
