import QuickLink from './QuickLink';

const Footer = () => {
  return (
    <footer className="border-border mt-auto border-t bg-gray-900 py-12 transition-colors duration-200">
      <div className="container mx-auto px-4">
        <div className="grid grid-cols-1 gap-8 md:grid-cols-3">
          {/* MovieMate Section */}
          <div className="space-y-4">
            <h2 className="text-2xl font-bold text-red-600 transition-colors duration-200">
              MovieMate
            </h2>
            <p className="text-muted-foreground transition-colors duration-200">
              Your personal movie recommendation platform
            </p>
          </div>

          {/* Quick Links Section */}
          <QuickLink />

          {/* Social Links Section */}
          <div>
            <h3 className="text-foreground mb-4 text-lg font-semibold transition-colors duration-200">
              Connect With Us
            </h3>
            <div className="flex gap-4">
              <a
                href="https://twitter.com"
                target="_blank"
                rel="noopener noreferrer"
                className="text-muted-foreground transition-colors duration-200 hover:text-red-600"
              >
                Twitter
              </a>
              <a
                href="https://instagram.com"
                target="_blank"
                rel="noopener noreferrer"
                className="text-muted-foreground transition-colors duration-200 hover:text-red-600"
              >
                Instagram
              </a>
              <a
                href="https://facebook.com"
                target="_blank"
                rel="noopener noreferrer"
                className="text-muted-foreground transition-colors duration-200 hover:text-red-600"
              >
                Facebook
              </a>
            </div>
          </div>
        </div>

        {/* Copyright Section */}
        <div className="border-border mt-8 border-t pt-8 text-center">
          <p className="text-muted-foreground transition-colors duration-200">
            © 2025 MovieMate. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;

export { default as LandingFooter } from './LandingFooter';
export { default as HomeFooter } from './HomeFooter';
