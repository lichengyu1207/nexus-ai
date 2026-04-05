from typing import Dict, Any, List, Callable, Optional
import asyncio
import uuid
from datetime import datetime


class AgentEvent:
    """Base class for all agent events"""
    
    def __init__(self, event_type: str, agent_id: str, agent_name: str):
        self.event_id = str(uuid.uuid4())
        self.event_type = event_type
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.timestamp = datetime.utcnow().isoformat()
        self.payload = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "timestamp": self.timestamp,
            "payload": self.payload
        }


class AgentStartEvent(AgentEvent):
    """Event fired when an agent starts execution"""
    
    def __init__(self, agent_id: str, agent_name: str, task: Dict[str, Any]):
        super().__init__("agent_start", agent_id, agent_name)
        self.payload = {
            "task": task,
            "message": f"Agent {agent_name} started execution"
        }


class AgentProgressEvent(AgentEvent):
    """Event fired when an agent makes progress"""
    
    def __init__(self, agent_id: str, agent_name: str, progress: float, message: str):
        super().__init__("agent_progress", agent_id, agent_name)
        self.payload = {
            "progress": progress,
            "message": message
        }


class AgentCompleteEvent(AgentEvent):
    """Event fired when an agent completes execution successfully"""
    
    def __init__(self, agent_id: str, agent_name: str, result: Dict[str, Any]):
        super().__init__("agent_complete", agent_id, agent_name)
        self.payload = {
            "result": result,
            "message": f"Agent {agent_name} completed execution successfully"
        }


class AgentErrorEvent(AgentEvent):
    """Event fired when an agent encounters an error"""
    
    def __init__(self, agent_id: str, agent_name: str, error: str):
        super().__init__("agent_error", agent_id, agent_name)
        self.payload = {
            "error": error,
            "message": f"Agent {agent_name} encountered an error"
        }


class WorkflowStartEvent(AgentEvent):
    """Event fired when a workflow starts execution"""
    
    def __init__(self, workflow_id: str, workflow_name: str, initial_data: Dict[str, Any]):
        super().__init__("workflow_start", workflow_id, workflow_name)
        self.payload = {
            "initial_data": initial_data,
            "message": f"Workflow {workflow_name} started execution"
        }


class WorkflowProgressEvent(AgentEvent):
    """Event fired when a workflow makes progress"""
    
    def __init__(self, workflow_id: str, workflow_name: str, progress: float, current_node: str):
        super().__init__("workflow_progress", workflow_id, workflow_name)
        self.payload = {
            "progress": progress,
            "current_node": current_node,
            "message": f"Workflow {workflow_name} is executing node {current_node}"
        }


class WorkflowCompleteEvent(AgentEvent):
    """Event fired when a workflow completes execution successfully"""
    
    def __init__(self, workflow_id: str, workflow_name: str, result: Dict[str, Any]):
        super().__init__("workflow_complete", workflow_id, workflow_name)
        self.payload = {
            "result": result,
            "message": f"Workflow {workflow_name} completed execution successfully"
        }


class WorkflowErrorEvent(AgentEvent):
    """Event fired when a workflow encounters an error"""
    
    def __init__(self, workflow_id: str, workflow_name: str, error: str):
        super().__init__("workflow_error", workflow_id, workflow_name)
        self.payload = {
            "error": error,
            "message": f"Workflow {workflow_name} encountered an error"
        }


class WorkflowWarningEvent(AgentEvent):
    """Event fired when a workflow encounters a warning"""
    
    def __init__(self, workflow_id: str, workflow_name: str, warning: str):
        super().__init__("workflow_warning", workflow_id, workflow_name)
        self.payload = {
            "warning": warning,
            "message": f"Workflow {workflow_name} encountered a warning"
        }


class EventManager:
    """Event manager for handling agent and workflow events"""
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._event_history: List[Dict[str, Any]] = []
        self._history_max_size = 1000
    
    def subscribe(self, event_type: str, callback: Callable[[Dict[str, Any]], None]):
        """Subscribe to an event type"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
    
    def unsubscribe(self, event_type: str, callback: Callable[[Dict[str, Any]], None]):
        """Unsubscribe from an event type"""
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(callback)
            except ValueError:
                pass
    
    def publish(self, event: AgentEvent):
        """Publish an event"""
        event_dict = event.to_dict()
        
        # Add to history
        self._event_history.append(event_dict)
        if len(self._event_history) > self._history_max_size:
            self._event_history.pop(0)
        
        # Notify subscribers
        event_type = event.event_type
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                try:
                    callback(event_dict)
                except Exception as e:
                    print(f"Error in event callback: {str(e)}")
        
        # Also notify wildcard subscribers
        if "*" in self._subscribers:
            for callback in self._subscribers["*"]:
                try:
                    callback(event_dict)
                except Exception as e:
                    print(f"Error in wildcard event callback: {str(e)}")
    
    def get_event_history(self, event_type: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get event history"""
        if event_type:
            history = [event for event in self._event_history if event["event_type"] == event_type]
        else:
            history = self._event_history
        
        return history[-limit:]
    
    def clear_event_history(self):
        """Clear event history"""
        self._event_history.clear()


# Create a global event manager instance
event_manager = EventManager()
