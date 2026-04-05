import React from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import clsx from 'clsx';

interface ModalProps {
  open: boolean;
  onClose: (open: boolean) => void;
  title: string;
  children: React.ReactNode;
  className?: string;
}

/**
 * 极简主义模态框组件
 * @param open 是否打开
 * @param onClose 关闭回调
 * @param title 模态框标题
 * @param children 模态框内容
 * @param className 自定义类名
 */
export const Modal: React.FC<ModalProps> = ({ open, onClose, title, children, className }) => {
  return (
    <Dialog.Root open={open} onOpenChange={onClose}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50" />
        <Dialog.Content className={clsx(
          'fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-md glass rounded-lg p-6 shadow-lg',
          className
        )}>
          <Dialog.Title className="text-lg font-medium mb-4">{title}</Dialog.Title>
          {children}
          <Dialog.Close asChild>
            <button className="absolute top-4 right-4 text-text-secondary hover:text-text-primary transition-colors">
              ✕
            </button>
          </Dialog.Close>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
};
