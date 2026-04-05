export type EndName = 'university' | 'enterprise' | 'government' | 'association' | 'public';

export type EndStatus = 'pending' | 'processing' | 'completed';

export interface End {
  id: string;
  name: EndName;
  displayName: string;
  unreadCount: number;
}

export interface EndStats {
  taskCount: number;
  activeUsers: number;
  messageCount: number;
}

export interface CollaborationEvent {
  id: string;
  timestamp: string;
  title: string;
  description: string;
  fromEnd: End['name'];
  toEnd: End['name'];
  status: 'pending' | 'processing' | 'completed';
  actionable: boolean;
  relatedTaskId?: string;
}

export interface Message {
  id: string;
  fromEnd: End['name'];
  toEnd: End['name'];
  content: string;
  attachments?: { name: string; url: string }[];
  timestamp: string;
  read: boolean;
  isOwn: boolean;
}

export interface MessageInput {
  content: string;
  attachments?: File[];
}

export interface EndInfo {
  id: EndName;
  displayName: string;
  manager: string;
  contact: string;
  apiCalls: number;
  lastActiveTime: string;
}

export interface WebSocketMessage {
  type: 'new_message' | 'newEvent' | 'messageRead';
  payload: Message | CollaborationEvent;
}

export interface NewMessagePayload {
  content: string;
  attachments?: File[];
}
