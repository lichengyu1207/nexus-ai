import React, { useState, useCallback, useEffect, lazy, Suspense } from 'react';
import AgentSelector from './components/AgentSelector';
import MessageList from './components/MessageList';
import ChatInput from './components/ChatInput';
import ReportPanel from './components/ReportPanel';
import ErrorBoundary from './components/ErrorBoundary';
import ThemeToggle from './components/ThemeToggle';
import UserGuide from './components/UserGuide';
import { ThemeProvider } from './contexts/ThemeContext';
import { useChat } from './hooks/useChat';
import { useMemory } from './hooks/useMemory';
import { soundManager, SOUNDS } from './utils/soundManager';
import './styles/chat.css';
const TrilogyController = lazy(() => import('./components/TrilogyController'));
const LoadingFallback = () => (<div className="loading-container">
    <div className="loading-spinner"></div>
    <p>加载动画组件...</p>
  </div>);
const AppContent = () => {
    const [currentAgent, setCurrentAgent] = useState('zhouyu');
    const [demoMode, setDemoMode] = useState(false);
    const [showTrilogy, setShowTrilogy] = useState(false);
    const [lastUserInput, setLastUserInput] = useState('');
    const [showGuide, setShowGuide] = useState(false);
    const { messages, isLoading, currentReportId, sendMessage } = useChat();
    const { report, isLoading: reportLoading, fetchReport } = useMemory();
    useEffect(() => {
        const hasSeenGuide = localStorage.getItem('worry_eraser_guide_completed');
        if (!hasSeenGuide) {
            setShowGuide(true);
        }
        soundManager.resume();
    }, []);
    const handleAgentChange = useCallback((agent) => {
        setCurrentAgent(agent);
        soundManager.play(SOUNDS.CLICK, 0.3);
    }, []);
    const handleSend = useCallback(async (message) => {
        setLastUserInput(message);
        soundManager.play(SOUNDS.SEND, 0.5);
        if (demoMode) {
            setTimeout(() => {
                console.log('Demo mode: simulated response');
                soundManager.play(SOUNDS.RECEIVE, 0.5);
            }, 1000);
            return;
        }
        try {
            await sendMessage(message, currentAgent);
            soundManager.play(SOUNDS.RECEIVE, 0.5);
        }
        catch (error) {
            console.error('Failed to send message:', error);
        }
    }, [sendMessage, currentAgent, demoMode]);
    const handleGenerateReport = useCallback(async () => {
        if (!currentReportId)
            return;
        try {
            await fetchReport(currentReportId);
            soundManager.play(SOUNDS.REPORT, 0.5);
        }
        catch (error) {
            console.error('Failed to generate report:', error);
        }
    }, [currentReportId, fetchReport]);
    const handleTrilogyComplete = useCallback(() => {
        setShowTrilogy(false);
        soundManager.play(SOUNDS.SUCCESS, 0.5);
    }, []);
    const startTrilogy = useCallback(() => {
        if (messages.length > 0 && report) {
            setShowTrilogy(true);
        }
    }, [messages, report]);
    const handleGuideComplete = useCallback(() => {
        setShowGuide(false);
    }, []);
    useEffect(() => {
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.has('demo')) {
            setDemoMode(true);
        }
    }, []);
    return (<div className="container">
      {demoMode && (<div className="demo-mode">演示模式</div>)}
      
      <div className="header">
        <h1>烦恼橡皮擦</h1>
        <AgentSelector currentAgent={currentAgent} onAgentChange={handleAgentChange}/>
      </div>
      
      <div className="main-content">
        <div className="chat-section">
          <MessageList messages={messages}/>
          <ChatInput onSend={handleSend} isLoading={isLoading}/>
        </div>
        
        <ReportPanel report={report} onGenerate={handleGenerateReport} isLoading={reportLoading}/>
      </div>
      
      {showTrilogy && (<Suspense fallback={<LoadingFallback />}>
          <TrilogyController userInput={lastUserInput} reportData={report} memoryContent={messages.length > 1 ? messages[messages.length - 2].content : undefined} onComplete={handleTrilogyComplete}/>
        </Suspense>)}
      
      <ThemeToggle />
      
      {showGuide && <UserGuide onComplete={handleGuideComplete}/>}
    </div>);
};
const App = () => {
    return (<ErrorBoundary>
      <ThemeProvider>
        <AppContent />
      </ThemeProvider>
    </ErrorBoundary>);
};
export default App;
