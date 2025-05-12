// import React from 'react';
import { motion } from 'framer-motion';
import { Facebook, Twitter, Instagram, Youtube } from 'lucide-react';

const LandingFooter = () => {
  return (
    <footer className=" border-t-2 border-gray-800 bg-black py-12">
      <div className="container mx-auto px-4 ">
        <div className="grid grid-cols-1 gap-8 md:grid-cols-4">
          {/* Company Info */}
          <div className="space-y-4">
            <h3 className="text-xl font-bold text-white">MovieMate</h3>
            <p className="text-gray-400">
              Your personal cinema companion for discovering and enjoying movies.
            </p>
            <div className="flex space-x-4">
              <a href="#" className="text-gray-400 hover:text-red-500">
                <Facebook className="size-5" />
              </a>
              <a href="#" className="text-gray-400 hover:text-red-500">
                <Twitter className="size-5" />
              </a>
              <a href="#" className="text-gray-400 hover:text-red-500">
                <Instagram className="size-5" />
              </a>
              <a href="#" className="text-gray-400 hover:text-red-500">
                <Youtube className="size-5" />
              </a>
            </div>
          </div>

          {/* Quick Links */}
          <div>
            <h4 className="mb-4 text-lg font-semibold text-white">Quick Links</h4>
            <ul className="space-y-2">
              <li>
                <a href="#" className="text-gray-400 hover:text-red-500">
                  About Us
                </a>
              </li>
              <li>
                <a href="#" className="text-gray-400 hover:text-red-500">
                  Contact
                </a>
              </li>
              <li>
                <a href="#" className="text-gray-400 hover:text-red-500">
                  FAQ
                </a>
              </li>
              <li>
                <a href="#" className="text-gray-400 hover:text-red-500">
                  Privacy Policy
                </a>
              </li>
            </ul>
          </div>

          {/* Categories */}
          <div>
            <h4 className="mb-4 text-lg font-semibold text-white">Categories</h4>
            <ul className="space-y-2">
              <li>
                <a href="#" className="text-gray-400 hover:text-red-500">
                  Action
                </a>
              </li>
              <li>
                <a href="#" className="text-gray-400 hover:text-red-500">
                  Drama
                </a>
              </li>
              <li>
                <a href="#" className="text-gray-400 hover:text-red-500">
                  Comedy
                </a>
              </li>
              <li>
                <a href="#" className="text-gray-400 hover:text-red-500">
                  Horror
                </a>
              </li>
            </ul>
          </div>

          {/* Newsletter */}
          <div>
            <h4 className="mb-4 text-lg font-semibold text-white">Newsletter</h4>
            <p className="mb-4 text-gray-400">
              Subscribe to get updates on new releases and special offers.
            </p>
            <form className="space-y-2">
              <input
                type="email"
                placeholder="Enter your email"
                className="w-full rounded-md bg-gray-800 px-4 py-2 text-white placeholder:text-gray-400 focus:border-red-500 focus:outline-none focus:ring-1 focus:ring-red-500"
              />
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className="w-full rounded-md bg-red-600 px-4 py-2 text-white transition-colors hover:bg-red-700"
              >
                Subscribe
              </motion.button>
            </form>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="mt-12 border-t border-gray-800 pt-8">
          <div className="flex flex-col items-center justify-between space-y-4 text-center text-gray-400 md:flex-row md:space-y-0">
            <p>© 2024 MovieMate. All rights reserved.</p>
            <div className="flex space-x-6">
              <a href="#" className="hover:text-red-500">
                Terms of Service
              </a>
              <a href="#" className="hover:text-red-500">
                Privacy Policy
              </a>
              <a href="#" className="hover:text-red-500">
                Cookie Policy
              </a>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default LandingFooter;
