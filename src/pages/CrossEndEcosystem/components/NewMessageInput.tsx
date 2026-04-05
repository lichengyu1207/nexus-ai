import { useState, useRef } from 'react';
import { motion } from 'framer-motion';

interface NewMessageInputProps {
  onSend: (content: string, attachments?: File[]) => void;
  disabled?: boolean;
  placeholder?: string;
}

const quickActions = [
  { label: '请求数据', template: '您好，请提供相关数据资料。' },
  { label: '分配任务', template: '请协助处理以下任务：' },
  { label: '确认回复', template: '已收到，确认无误。' },
];

export function NewMessageInput({ 
  onSend, 
  disabled = false, 
  placeholder = '输入消息...' 
}: NewMessageInputProps) {
  const [content, setContent] = useState('');
  const [attachments, setAttachments] = useState<File[]>([]);
  const [showQuickActions, setShowQuickActions] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    if (content.trim() || attachments.length > 0) {
      onSend(content, attachments.length > 0 ? attachments : undefined);
      setContent('');
      setAttachments([]);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    setAttachments((prev) => [...prev, ...files]);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const removeAttachment = (index: number) => {
    setAttachments((prev) => prev.filter((_, i) => i !== index));
  };

  const handleQuickAction = (template: string) => {
    setContent(template);
    setShowQuickActions(false);
    textareaRef.current?.focus();
  };

  return (
    <div className="space-y-2">
      {attachments.length > 0 && (
        <div className="flex flex-wrap gap-2 p-2 rounded-lg bg-slate-800/50">
          {attachments.map((file, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="flex items-center gap-1 px-2 py-1 rounded bg-slate-700 text-gray-300 text-xs"
            >
              <span className="truncate max-w-[120px]">{file.name}</span>
              <button
                onClick={() => removeAttachment(index)}
                className="ml-1 text-gray-500 hover:text-red-400"
                aria-label="移除附件"
              >
                ×
              </button>
            </motion.div>
          ))}
        </div>
      )}

      <div className="flex items-end gap-2">
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={content}
            onChange={(e) => setContent(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled}
            rows={1}
            className="w-full px-4 py-2.5 pr-24 rounded-xl bg-slate-800 border border-slate-700
              text-white placeholder-gray-500 resize-none
              focus:outline-none focus:border-amber-500 disabled:opacity-50"
            aria-label="消息输入框"
          />
          
          <div className="absolute right-2 bottom-2 flex items-center gap-1">
            <button
              onClick={() => setShowQuickActions(!showQuickActions)}
              className="p-1.5 rounded-lg text-gray-400 hover:text-amber-400 hover:bg-slate-700
                transition-colors"
              aria-label="快捷操作"
              title="快捷操作"
            >
              ⚡
            </button>
            
            <button
              onClick={() => fileInputRef.current?.click()}
              className="p-1.5 rounded-lg text-gray-400 hover:text-amber-400 hover:bg-slate-700
                transition-colors"
              aria-label="添加附件"
              title="添加附件"
            >
              📎
            </button>
            
            <input
              ref={fileInputRef}
              type="file"
              multiple
              onChange={handleFileSelect}
              className="hidden"
              aria-label="选择文件"
            />
          </div>
        </div>

        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={handleSend}
          disabled={disabled || (!content.trim() && attachments.length === 0)}
          className="px-4 py-2.5 rounded-xl bg-amber-500 text-slate-900 font-medium
            hover:bg-amber-400 disabled:opacity-50 disabled:cursor-not-allowed
            transition-colors"
          aria-label="发送消息"
        >
          发送
        </motion.button>
      </div>

      {showQuickActions && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          className="flex gap-2 p-2 rounded-lg bg-slate-800 border border-slate-700"
        >
          {quickActions.map((action) => (
            <button
              key={action.label}
              onClick={() => handleQuickAction(action.template)}
              className="px-3 py-1.5 rounded-lg bg-slate-700 text-gray-300 text-sm
                hover:bg-slate-600 hover:text-white transition-colors"
            >
              {action.label}
            </button>
          ))}
        </motion.div>
      )}
    </div>
  );
}
