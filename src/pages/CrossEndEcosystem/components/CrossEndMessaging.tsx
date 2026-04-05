import { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FixedSizeList as List } from 'react-window';
import { useMessages, useSendMessage, useMarkMessagesAsRead } from '../hooks/useMessages';
import { NewMessageInput } from './NewMessageInput';
import type { EndName, Message } from '../types';

interface CrossEndMessagingProps {
  endId: EndName;
}

const endDisplayNames: Record<string, string> = {
  university: '院校端',
  enterprise: '企业端',
  government: '政府端',
  association: '协会端',
  public: '公众端',
};

const endIcons: Record<string, string> = {
  university: '🎓',
  enterprise: '🏢',
  government: '🏛️',
  association: '🤝',
  public: '👥',
};

function formatMessageTime(timestamp: string): string {
  const date = new Date(timestamp);
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
}

interface MessageBubbleProps {
  message: Message;
  style?: React.CSSProperties;
}

const MessageBubble = ({ message, style }: MessageBubbleProps) => {
  const isOwn = message.isOwn;
  
  return (
    <div
      style={style}
      className={`flex ${isOwn ? 'justify-end' : 'justify-start'} mb-2`}
    >
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className={`max-w-[70%] px-4 py-2 rounded-2xl ${
          isOwn
            ? 'bg-amber-500 text-slate-900 rounded-br-md'
            : 'bg-slate-700 text-white rounded-bl-md'
        }`}
      >
        <p className="text-sm whitespace-pre-wrap">{message.content}</p>
        {message.attachments && message.attachments.length > 0 && (
          <div className="mt-2 space-y-1">
            {message.attachments.map((att, idx) => (
              <a
                key={idx}
                href={att.url}
                target="_blank"
                rel="noopener noreferrer"
                className={`flex items-center gap-1 text-xs underline ${
                  isOwn ? 'text-slate-800' : 'text-amber-400'
                }`}
              >
                📎 {att.name}
              </a>
            ))}
          </div>
        )}
        <span className={`text-xs mt-1 block ${isOwn ? 'text-slate-700' : 'text-gray-400'}`}>
          {formatMessageTime(message.timestamp)}
        </span>
      </motion.div>
    </div>
  );
};

export function CrossEndMessaging({ endId }: CrossEndMessagingProps) {
  const [selectedContact, setSelectedContact] = useState<EndName | null>(null);
  const [messageDrafts, setMessageDrafts] = useState<Record<string, string>>({});
  const listRef = useRef<List>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const otherEnds: EndName[] = useMemo(() => {
    const allEnds: EndName[] = ['university', 'enterprise', 'government', 'association', 'public'];
    return allEnds.filter((e) => e !== endId);
  }, [endId]);

  useEffect(() => {
    if (!selectedContact && otherEnds.length > 0) {
      setSelectedContact(otherEnds[0]);
    }
  }, [otherEnds, selectedContact]);

  const { data: messages = [], isLoading } = useMessages({
    endId,
    otherEnd: selectedContact!,
    page: 1,
  });

  const sendMessage = useSendMessage(endId);
  const markAsRead = useMarkMessagesAsRead(endId);

  useEffect(() => {
    if (messages.length > 0 && listRef.current) {
      listRef.current.scrollToItem(messages.length - 1, 'end');
    }
  }, [messages.length]);

  useEffect(() => {
    if (selectedContact && messages.length > 0) {
      const unreadIds = messages.filter((m) => !m.read && !m.isOwn).map((m) => m.id);
      if (unreadIds.length > 0) {
        markAsRead.mutate({ messageIds: unreadIds, otherEnd: selectedContact });
      }
    }
  }, [messages, selectedContact, markAsRead]);

  const handleSendMessage = useCallback(
    async (content: string, attachments?: File[]) => {
      if (!selectedContact || !content.trim()) return;
      
      try {
        await sendMessage.mutateAsync({
          toEnd: selectedContact,
          content,
          attachments,
        });
      } catch (e) {
        console.error('Failed to send message:', e);
      }
    },
    [selectedContact, sendMessage]
  );

  const Row = useCallback(
    ({ index, style }: { index: number; style: React.CSSProperties }) => (
      <MessageBubble message={messages[index]} style={style} />
    ),
    [messages]
  );

  return (
    <div className="flex h-[500px] bg-slate-800/30 rounded-xl border border-slate-700/50 overflow-hidden">
      <div className="w-64 border-r border-slate-700/50 bg-slate-900/50">
        <div className="p-3 border-b border-slate-700/50">
          <h4 className="text-sm font-medium text-gray-400">联系人</h4>
        </div>
        <div className="overflow-y-auto">
          {otherEnds.map((end) => {
            const isSelected = end === selectedContact;
            const lastMessage = messages.find((m) => m.fromEnd === end || m.toEnd === end);
            const unreadCount = messages.filter((m) => !m.read && m.fromEnd === end).length;

            return (
              <motion.button
                key={end}
                whileHover={{ backgroundColor: 'rgba(255,255,255,0.05)' }}
                onClick={() => setSelectedContact(end)}
                className={`w-full p-3 text-left border-b border-slate-700/30 ${
                  isSelected ? 'bg-amber-500/10 border-l-2 border-l-amber-500' : ''
                }`}
              >
                <div className="flex items-center gap-2">
                  <span className="text-lg">{endIcons[end]}</span>
                  <span className="text-white text-sm font-medium">
                    {endDisplayNames[end]}
                  </span>
                  {unreadCount > 0 && (
                    <span className="ml-auto px-1.5 py-0.5 bg-red-500 text-white text-xs rounded-full">
                      {unreadCount}
                    </span>
                  )}
                </div>
                {lastMessage && (
                  <p className="text-gray-500 text-xs mt-1 truncate">
                    {lastMessage.content}
                  </p>
                )}
              </motion.button>
            );
          })}
        </div>
      </div>

      <div className="flex-1 flex flex-col">
        {selectedContact ? (
          <>
            <div className="p-3 border-b border-slate-700/50 bg-slate-900/30">
              <div className="flex items-center gap-2">
                <span className="text-lg">{endIcons[selectedContact]}</span>
                <span className="text-white font-medium">
                  {endDisplayNames[selectedContact]}
                </span>
              </div>
            </div>

            <div ref={containerRef} className="flex-1 overflow-hidden p-4">
              {isLoading ? (
                <div className="flex items-center justify-center h-full">
                  <div className="animate-spin w-6 h-6 border-2 border-amber-500 border-t-transparent rounded-full" />
                </div>
              ) : messages.length === 0 ? (
                <div className="flex items-center justify-center h-full text-gray-500">
                  暂无消息记录
                </div>
              ) : (
                <List
                  ref={listRef}
                  height={350}
                  itemCount={messages.length}
                  itemSize={80}
                  width="100%"
                  role="log"
                  aria-live="polite"
                >
                  {Row}
                </List>
              )}
            </div>

            <div className="p-3 border-t border-slate-700/50">
              <NewMessageInput
                onSend={handleSendMessage}
                disabled={sendMessage.isPending}
                placeholder={`发送消息给${endDisplayNames[selectedContact]}...`}
              />
            </div>
          </>
        ) : (
          <div className="flex items-center justify-center h-full text-gray-500">
            选择一个联系人开始对话
          </div>
        )}
      </div>
    </div>
  );
}
