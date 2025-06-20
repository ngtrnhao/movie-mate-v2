// import React from 'react';
import { motion } from 'framer-motion';
import { Facebook, Twitter, Instagram, Youtube } from 'lucide-react';
import { useTranslation } from '../../i18n/hooks/useTranslation';
import AdBannerFooter from '../ads/AdBannerFooter';

const LandingFooter = () => {
  const { t } = useTranslation('landing');
  return (
    <footer className=" border-t-2 border-gray-800 bg-black py-12">
      <AdBannerFooter />
      <div className="container mx-auto px-4 ">
        <div className="grid grid-cols-1 gap-8 md:grid-cols-4">
          {/* Company Info */}
          <div className="space-y-4">
            <h3 className="text-xl font-bold text-white">{t('footer.company.title')}</h3>
            <p className="text-gray-400">{t('footer.company.description')}</p>
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
            <h4 className="mb-4 text-lg font-semibold text-white">
              {t('footer.quickLinks.title')}
            </h4>
            <ul className="space-y-2">
              <li>
                <a href="#" className="text-gray-400 hover:text-red-500">
                  {t('footer.quickLinks.about')}
                </a>
              </li>
              <li>
                <a href="#" className="text-gray-400 hover:text-red-500">
                  {t('footer.quickLinks.contact')}
                </a>
              </li>
              <li>
                <a href="#" className="text-gray-400 hover:text-red-500">
                  {t('footer.quickLinks.faq')}
                </a>
              </li>
              <li>
                <a href="#" className="text-gray-400 hover:text-red-500">
                  {t('footer.quickLinks.privacy')}
                </a>
              </li>
            </ul>
          </div>

          {/* Categories */}
          <div>
            <h4 className="mb-4 text-lg font-semibold text-white">
              {t('footer.categories.title')}
            </h4>
            <ul className="space-y-2">
              <li>
                <a href="#" className="text-gray-400 hover:text-red-500">
                  {t('footer.categories.action')}
                </a>
              </li>
              <li>
                <a href="#" className="text-gray-400 hover:text-red-500">
                  {t('footer.categories.drama')}
                </a>
              </li>
              <li>
                <a href="#" className="text-gray-400 hover:text-red-500">
                  {t('footer.categories.comedy')}
                </a>
              </li>
              <li>
                <a href="#" className="text-gray-400 hover:text-red-500">
                  {t('footer.categories.horror')}
                </a>
              </li>
            </ul>
          </div>

          {/* Newsletter */}
          <div>
            <h4 className="mb-4 text-lg font-semibold text-white">
              {t('footer.newsletter.title')}
            </h4>
            <p className="mb-4 text-gray-400">{t('footer.newsletter.description')}</p>
            <form className="space-y-2">
              <input
                type="email"
                placeholder={t('footer.newsletter.placeholder')}
                className="w-full rounded-md bg-gray-800 px-4 py-2 text-white placeholder:text-gray-400 focus:border-red-500 focus:outline-none focus:ring-1 focus:ring-red-500"
              />
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className="w-full rounded-md bg-red-600 px-4 py-2 text-white transition-colors hover:bg-red-700"
              >
                {t('footer.newsletter.button')}
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
