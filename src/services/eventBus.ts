type EventHandler = (data: unknown) => void;

class EventBus {
  private events: Map<string, Set<EventHandler>> = new Map();

  subscribe(event: string, handler: EventHandler): () => void {
    if (!this.events.has(event)) {
      this.events.set(event, new Set());
    }
    this.events.get(event)!.add(handler);
    
    return () => {
      this.events.get(event)?.delete(handler);
    };
  }

  emit(event: string, data?: unknown): void {
    const handlers = this.events.get(event);
    if (handlers) {
      handlers.forEach((handler) => {
        try {
          handler(data);
        } catch (error) {
          console.error(`Error in event handler for ${event}:`, error);
        }
      });
    }
  }

  once(event: string, handler: EventHandler): () => void {
    const wrappedHandler = (data: unknown) => {
      handler(data);
      this.events.get(event)?.delete(wrappedHandler);
    };
    return this.subscribe(event, wrappedHandler);
  }

  clear(event?: string): void {
    if (event) {
      this.events.delete(event);
    } else {
      this.events.clear();
    }
  }
}

export const eventBus = new EventBus();

export const EventTypes = {
  TASK_CREATED: 'task:created',
  TASK_STATUS_CHANGED: 'task:status-changed',
  
  TEAM_SELECTED: 'team:selected',
  TEAM_MEMBER_JOINED: 'team:member-joined',
  
  RECRUITMENT_CREATED: 'recruitment:created',
  RECRUITMENT_BID_RECEIVED: 'recruitment:bid-received',
  RECRUITMENT_BID_ACCEPTED: 'recruitment:bid-accepted',
  
  MEMORY_CREATED: 'memory:created',
  
  TALENT_INVITED: 'talent:invited',
  
  WORKFLOW_STARTED: 'workflow:started',
  WORKFLOW_COMPLETED: 'workflow:completed',
  
  DISTRIBUTION_COMPLETED: 'distribution:completed',
  
  NOTIFICATION_RECEIVED: 'notification:received',
} as const;

export type EventType = typeof EventTypes[keyof typeof EventTypes];
