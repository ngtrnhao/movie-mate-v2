import React from 'react';
import { useTranslation } from 'react-i18next';

const ProductionCompanies = ({ companies = [], maxDisplay = 4, showDetails = true }) => {
  const { t } = useTranslation('movies');

  if (!companies || companies.length === 0) {
    return null;
  }

  const displayCompanies = companies.slice(0, maxDisplay);
  const remainingCount = companies.length - maxDisplay;

  const getCompanyDisplayName = company => {
    if (typeof company === 'string') {
      return company;
    }
    return company.name || company;
  };

  const getCompanyCountry = company => {
    if (typeof company === 'object' && company.origin_country) {
      return company.origin_country;
    }
    return null;
  };

  const getCompanyLogo = company => {
    if (typeof company === 'object' && company.logo_path) {
      // TMDB logo path format: /8rAmlU9kIQKBenqQVlz6hUyV1Z4.png
      // We need to add the base URL and size parameter
      return `https://image.tmdb.org/t/p/w200${company.logo_path}`;
    }
    return null;
  };

  return (
    <div className="space-y-3">
      <h4 className="text-sm font-semibold text-gray-300 sm:text-base">
        {t('details.production')}
      </h4>

      <div className="space-y-2">
        {displayCompanies.map((company, index) => {
          const companyName = getCompanyDisplayName(company);
          const companyCountry = getCompanyCountry(company);
          const companyLogo = getCompanyLogo(company);

          return (
            <div
              key={index}
              className="flex items-center space-x-3 rounded-lg bg-gray-800/50 p-3 backdrop-blur-sm transition-colors hover:bg-gray-700/50"
            >
              {/* Company Logo */}
              {companyLogo ? (
                <div className="flex-shrink-0">
                  <img
                    src={companyLogo}
                    alt={`${companyName} logo`}
                    className="h-8 w-8 rounded object-contain"
                    onError={e => {
                      e.target.style.display = 'none';
                    }}
                  />
                </div>
              ) : (
                <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded bg-gray-600 text-xs font-bold text-white">
                  {companyName.charAt(0).toUpperCase()}
                </div>
              )}

              {/* Company Info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center space-x-2">
                  <span className="text-sm font-medium text-white truncate">{companyName}</span>
                  {companyCountry && (
                    <span className="rounded bg-blue-600/20 px-2 py-1 text-xs font-medium text-blue-300">
                      {companyCountry}
                    </span>
                  )}
                </div>

                {showDetails && typeof company === 'object' && company.id && (
                  <p className="text-xs text-gray-400">ID: {company.id}</p>
                )}
              </div>
            </div>
          );
        })}

        {/* Show remaining count */}
        {remainingCount > 0 && (
          <div className="rounded-lg bg-gray-800/30 p-3 text-center">
            <span className="text-sm text-gray-400">
              +{remainingCount} {t('details.moreCompanies')}
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProductionCompanies;
