import React, { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useShowcaseStore } from './showcaseStore';
import { ShowcaseItem } from './showcaseData';

interface DetailModalProps {
  item: ShowcaseItem | null;
  children?: React.ReactNode;
}

const DetailModal: React.FC<DetailModalProps> = ({ item, children }) => {
  const { closeModal, isModalOpen } = useShowcaseStore();

  useEffect(() => {
    if (isModalOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isModalOpen]);

  if (!item) return null;

  return (
    <AnimatePresence>
      {isModalOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          style={styles.overlay}
          onClick={closeModal}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 50 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 50 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            style={styles.container}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ ...styles.header, borderColor: item.color }}>
              <div style={styles.headerLeft}>
                <span style={styles.icon}>{item.icon}</span>
                <div>
                  <h2 style={{ ...styles.title, color: item.color }}>{item.title}</h2>
                  <p style={styles.subtitle}>{item.description}</p>
                </div>
              </div>
              <button style={styles.closeButton} onClick={closeModal}>
                ✕
              </button>
            </div>

            <div style={styles.content}>
              {children}
            </div>

            <div style={styles.footer}>
              <motion.button
                style={styles.actionButton}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                了解更多 →
              </motion.button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

const styles: Record<string, React.CSSProperties> = {
  overlay: {
    position: 'fixed',
    inset: 0,
    background: 'rgba(0, 0, 0, 0.8)',
    backdropFilter: 'blur(8px)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 9999,
    padding: '20px',
  },
  container: {
    width: '100%',
    maxWidth: '800px',
    maxHeight: '80vh',
    background: 'linear-gradient(180deg, #0A2342, #061224)',
    borderRadius: '20px',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    overflow: 'hidden',
    display: 'flex',
    flexDirection: 'column',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '20px 24px',
    borderBottom: '2px solid',
  },
  headerLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
  },
  icon: {
    fontSize: '40px',
  },
  title: {
    fontSize: '24px',
    margin: 0,
    fontFamily: 'sans-serif',
  },
  subtitle: {
    fontSize: '14px',
    color: 'rgba(255, 255, 255, 0.6)',
    margin: '4px 0 0 0',
  },
  closeButton: {
    width: '40px',
    height: '40px',
    borderRadius: '50%',
    border: '1px solid rgba(255, 255, 255, 0.2)',
    background: 'rgba(255, 255, 255, 0.1)',
    color: '#fff',
    fontSize: '18px',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  content: {
    flex: 1,
    padding: '24px',
    overflowY: 'auto',
  },
  footer: {
    padding: '16px 24px',
    borderTop: '1px solid rgba(255, 255, 255, 0.1)',
    display: 'flex',
    justifyContent: 'flex-end',
  },
  actionButton: {
    padding: '12px 32px',
    background: 'linear-gradient(135deg, #D4AF37, #B8962E)',
    border: 'none',
    borderRadius: '8px',
    color: '#0A2342',
    fontSize: '14px',
    fontWeight: 'bold',
    cursor: 'pointer',
  },
};

export default DetailModal;
