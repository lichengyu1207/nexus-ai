import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { XMarkIcon } from '@heroicons/react/24/outline';
import type { Bid } from '../types';

export interface BidFormProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: Partial<Bid>) => void;
  isLoading?: boolean;
  recruitmentId: string;
  recruitmentTitle?: string;
}

export function BidForm({
  isOpen,
  onClose,
  onSubmit,
  isLoading,
  recruitmentId,
  recruitmentTitle,
}: BidFormProps) {
  const [formData, setFormData] = useState<Partial<Bid>>({
    recruitmentId,
    proposal: '',
    price: 0,
    estimatedDays: 7,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
            onClick={onClose}
          />

          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-lg bg-gray-900 border border-white/10 rounded-xl shadow-2xl z-50 overflow-hidden"
          >
            <div className="flex items-center justify-between p-4 border-b border-white/10">
              <div>
                <h2 className="text-lg font-semibold text-white">提交投标</h2>
                {recruitmentTitle && (
                  <p className="text-sm text-gray-400">{recruitmentTitle}</p>
                )}
              </div>
              <button
                onClick={onClose}
                className="p-1 rounded-lg hover:bg-white/10 transition-colors"
              >
                <XMarkIcon className="w-5 h-5 text-gray-400" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="p-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">
                  投标提案 <span className="text-red-400">*</span>
                </label>
                <textarea
                  value={formData.proposal}
                  onChange={(e) => setFormData({ ...formData, proposal: e.target.value })}
                  required
                  rows={5}
                  className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-amber-500/50 resize-none"
                  placeholder="描述您的方案、经验、为什么适合这个项目..."
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-1">
                    报价金额 <span className="text-red-400">*</span>
                  </label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">
                      ¥
                    </span>
                    <input
                      type="number"
                      value={formData.price}
                      onChange={(e) => setFormData({ ...formData, price: Number(e.target.value) })}
                      required
                      min={0}
                      className="w-full pl-8 pr-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-amber-500/50"
                      placeholder="0"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-1">
                    预计天数 <span className="text-red-400">*</span>
                  </label>
                  <input
                    type="number"
                    value={formData.estimatedDays}
                    onChange={(e) =>
                      setFormData({ ...formData, estimatedDays: Number(e.target.value) })
                    }
                    required
                    min={1}
                    className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-amber-500/50"
                    placeholder="7"
                  />
                </div>
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={onClose}
                  className="flex-1 py-2 text-sm text-gray-400 hover:text-white transition-colors"
                >
                  取消
                </button>
                <button
                  type="submit"
                  disabled={isLoading || !formData.proposal}
                  className={`
                    flex-1 py-2 text-sm font-medium rounded-lg transition-colors
                    ${
                      isLoading || !formData.proposal
                        ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
                        : 'bg-amber-500 text-gray-900 hover:bg-amber-400'
                    }
                  `}
                >
                  {isLoading ? '提交中...' : '提交投标'}
                </button>
              </div>
            </form>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
