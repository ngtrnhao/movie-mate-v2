// import React from 'react';
import { motion } from 'framer-motion';
import { Facebook, Twitter, Instagram, Youtube } from 'lucide-react';

const HomeFooter = () => {
  return (
    <footer className="bg-gray-900 py-8">
      <div className="container mx-auto px-4">
        <div className="grid grid-cols-1 gap-8 md:grid-cols-3">
          {/* Quick Links */}
          <div>
            <h4 className="mb-4 text-lg font-semibold text-white">Quick Links</h4>
            <ul className="space-y-2">
              <li>
                <a href="#" className="text-gray-400 hover:text-red-500">
                  My Watchlist
                </a>
              </li>
              <li>
                <a href="#" className="text-gray-400 hover:text-red-500">
                  My Reviews
                </a>
              </li>
              <li>
                <a href="#" className="text-gray-400 hover:text-red-500">
                  Settings
                </a>
              </li>
              <li>
                <a href="#" className="text-gray-400 hover:text-red-500">
                  Help Center
                </a>
              </li>
            </ul>
          </div>

          {/* Social Links */}
          <div>
            <h4 className="mb-4 text-lg font-semibold text-white">Connect With Us</h4>
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

          {/* App Info */}
          <div>
            <h4 className="mb-4 text-lg font-semibold text-white">MovieMate App</h4>
            <p className="mb-4 text-gray-400">
              Get the best movie experience on your mobile device.
            </p>
            <div className="flex space-x-4">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="rounded-md bg-gray-800 px-4 py-2 text-white hover:bg-gray-700"
              >
                App Store
              </motion.button>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="rounded-md bg-gray-800 px-4 py-2 text-white hover:bg-gray-700"
              >
                Google Play
              </motion.button>
            </div>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="mt-8 border-t border-gray-800 pt-8">
          <div className="flex flex-col items-center justify-between space-y-4 text-center text-gray-400 md:flex-row md:space-y-0">
            <p>© 2024 MovieMate. All rights reserved.</p>
            <div className="flex space-x-6">
              <a href="#" className="hover:text-red-500">
                Terms
              </a>
              <a href="#" className="hover:text-red-500">
                Privacy
              </a>
              <a href="#" className="hover:text-red-500">
                Cookies
              </a>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default HomeFooter;
