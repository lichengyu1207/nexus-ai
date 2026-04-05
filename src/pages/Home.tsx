import React from 'react';
import { useTranslation } from 'react-i18next';
import { BottomShowcase } from '../components/bottomShowcase';
import { InternationalShowcase } from '../components/showcase';

const Home: React.FC = () => {
  const { t } = useTranslation();

  return (
    <div className="min-h-screen">
      <InternationalShowcase autoPlay={true} />
      
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-primary-600 mb-6">{t('home.welcome')}</h1>
        <p className="text-lg text-gray-700 mb-8">
          {t('home.description')}
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
            <h2 className="text-xl font-semibold text-primary-500 mb-3">{t('home.propertyAnalysis')}</h2>
            <p className="text-gray-600">
              {t('home.propertyAnalysisDesc')}
            </p>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
            <h2 className="text-xl font-semibold text-primary-500 mb-3">{t('home.reportGeneration')}</h2>
            <p className="text-gray-600">
              {t('home.reportGenerationDesc')}
            </p>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
            <h2 className="text-xl font-semibold text-primary-500 mb-3">{t('home.assetLibrary')}</h2>
            <p className="text-gray-600">
              {t('home.assetLibraryDesc')}
            </p>
          </div>
        </div>
      </div>

      <BottomShowcase />
    </div>
  );
};

export default Home;
