import React, { Suspense, lazy } from 'react';
import { motion } from 'framer-motion';
import { useInView } from 'react-intersection-observer';
import { useShowcaseStore } from './showcaseStore';
import { showcaseItems } from './showcaseData';
import ProcessCard from './ProcessCard';
import DetailModal from './DetailModal';

const DemandDetail = lazy(() => import('./details/DemandDetail'));
const SwarmSchedulingDetail = lazy(() => import('./details/SwarmSchedulingDetail'));
const CollaborationDetail = lazy(() => import('./details/CollaborationDetail'));
const MemoryDetail = lazy(() => import('./details/MemoryDetail'));
const EvolutionDetail = lazy(() => import('./details/EvolutionDetail'));
const ReportDetail = lazy(() => import('./details/ReportDetail'));

const detailComponents: Record<string, React.LazyExoticComponent<React.FC>> = {
  demand: DemandDetail,
  swarm: SwarmSchedulingDetail,
  collaboration: CollaborationDetail,
  memory: MemoryDetail,
  evolution: EvolutionDetail,
  report: ReportDetail,
};

const BottomShowcase: React.FC = () => {
  const { activeCardId, hoveredCardId, openModal, setHoveredCard, closeModal, isModalOpen } = useShowcaseStore();
  const { ref, inView } = useInView({
    threshold: 0.2,
    triggerOnce: false,
  });

  const activeItem = showcaseItems.find(item => item.id === activeCardId);
  const DetailComponent = activeCardId ? detailComponents[activeCardId] : null;

  return (
    <section ref={ref} style={styles.container}>
      <div style={styles.background}>
        <div style={styles.gradientOrb1} />
        <div style={styles.gradientOrb2} />
      </div>

      <div style={styles.header}>
        <motion.h2
          initial={{ opacity: 0, y: 20 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.5 }}
          style={styles.title}
        >
          平台核心能力
        </motion.h2>
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.5, delay: 0.1 }}
          style={styles.subtitle}
        >
          点击卡片探索智能体的工作流程
        </motion.p>
      </div>

      <div style={styles.cardsContainer}>
        {showcaseItems.map((item, index) => (
          <ProcessCard
            key={item.id}
            item={item}
            index={index}
            isActive={activeCardId === item.id}
            isHovered={hoveredCardId === item.id}
            onClick={() => openModal(item.id)}
            onHover={() => setHoveredCard(item.id)}
            onLeave={() => setHoveredCard(null)}
          />
        ))}
      </div>

      <DetailModal item={activeItem}>
        {DetailComponent && (
          <Suspense
            fallback={
              <div style={styles.loading}>
                <div style={styles.spinner} />
                <span>加载中...</span>
              </div>
            }
          >
            <DetailComponent />
          </Suspense>
        )}
      </DetailModal>
    </section>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    position: 'relative',
    width: '100%',
    minHeight: '400px',
    padding: '60px 24px',
    background: 'linear-gradient(180deg, transparent, rgba(10, 35, 66, 0.5))',
    overflow: 'hidden',
  },
  background: {
    position: 'absolute',
    inset: 0,
    pointerEvents: 'none',
  },
  gradientOrb1: {
    position: 'absolute',
    top: '20%',
    left: '10%',
    width: '300px',
    height: '300px',
    borderRadius: '50%',
    background: 'radial-gradient(circle, rgba(212, 175, 55, 0.1), transparent 70%)',
    filter: 'blur(40px)',
  },
  gradientOrb2: {
    position: 'absolute',
    bottom: '20%',
    right: '10%',
    width: '400px',
    height: '400px',
    borderRadius: '50%',
    background: 'radial-gradient(circle, rgba(59, 130, 246, 0.1), transparent 70%)',
    filter: 'blur(40px)',
  },
  header: {
    textAlign: 'center',
    marginBottom: '40px',
    position: 'relative',
    zIndex: 1,
  },
  title: {
    fontSize: '32px',
    color: '#D4AF37',
    margin: '0 0 8px 0',
    fontFamily: 'sans-serif',
  },
  subtitle: {
    fontSize: '16px',
    color: 'rgba(255, 255, 255, 0.6)',
    margin: 0,
  },
  cardsContainer: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
    gap: '20px',
    maxWidth: '1200px',
    margin: '0 auto',
    position: 'relative',
    zIndex: 1,
  },
  loading: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '16px',
    padding: '60px',
    color: 'rgba(255, 255, 255, 0.6)',
  },
  spinner: {
    width: '40px',
    height: '40px',
    border: '3px solid rgba(212, 175, 55, 0.3)',
    borderTopColor: '#D4AF37',
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
  },
};

export default BottomShowcase;
