import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import {
  ShieldCheckIcon,
  BoltIcon,
  CheckCircleIcon,
  ArrowRightIcon,
} from '@heroicons/react/24/outline';
import Mascot from '@/components/mascot/Mascot';
import { brandCopy } from '@/config/brand';

const Hero: React.FC = () => {
  const navigate = useNavigate();

  return (
    <section className="pt-20 pb-16 bg-gradient-to-b from-blue-50 via-white to-purple-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center gap-12">
        <div className="md:w-5/12 flex justify-center">
          <motion.div
            initial={{ opacity: 0, x: -50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6 }}
            className="flex justify-center"
          >
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-r from-blue-400 to-purple-400 rounded-3xl blur-2xl opacity-20"></div>
              <div className="relative bg-white rounded-3xl p-4 shadow-2xl">
                <Mascot emotion="happy" pose="standing" size="xl" />
              </div>
            </div>
          </motion.div>
        </div>
        
        <motion.div 
          className="md:w-7/12 text-center md:text-left"
          initial={{ opacity: 0, x: 50 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          <h1 className="text-5xl md:text-6xl font-extrabold tracking-tight mb-4">
            {brandCopy.hero.mainTitle.split('。')[0]}
            <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              {brandCopy.hero.mainTitle.split('。')[1] || ''}
            </span>
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-2xl">
            {brandCopy.hero.subTitle}
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center md:justify-start mb-10">
            <button
              onClick={() => navigate('/register')}
              className="px-8 py-4 bg-gradient-to-r from-blue-600 to-blue-500 text-white rounded-full font-semibold text-lg shadow-lg hover:shadow-xl hover:from-blue-700 hover:to-blue-600 transition-all flex items-center justify-center gap-2"
            >
              开始免费分析
              <ArrowRightIcon className="w-5 h-5" />
            </button>
            <button
              onClick={() => navigate('/login')}
              className="px-8 py-4 border-2 border-gray-200 text-gray-700 rounded-full font-semibold text-lg hover:bg-gray-50 hover:border-gray-300 transition-all"
            >
              查看演示
            </button>
          </div>
          
          <div className="flex flex-wrap gap-6 justify-center md:justify-start">
            <div className="flex items-center gap-2">
              <ShieldCheckIcon className="w-5 h-5 text-green-500" />
              <span className="text-sm font-medium">数据安全加密</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircleIcon className="w-5 h-5 text-blue-500" />
              <span className="text-sm font-medium">10万+用户信赖</span>
            </div>
            <div className="flex items-center gap-2">
              <BoltIcon className="w-5 h-5 text-yellow-500" />
              <span className="text-sm font-medium">秒级响应</span>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
};

export default Hero;
