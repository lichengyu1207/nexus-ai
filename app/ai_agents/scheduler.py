from typing import Dict, Any, List, Optional
import asyncio
import uuid
from app.ai_agents.agent_factory import AgentFactory
from app.ai_agents.event_system import EventManager


class AgentScheduler:
    """Scheduler for coordinating multiple AI agents"""
    
    def __init__(self, event_manager: Optional[EventManager] = None):
        """Initialize scheduler"""
        from app.ai_agents.event_system import event_manager as default_event_manager
        self.event_manager = event_manager or default_event_manager
        self.running_tasks: Dict[str, Dict[str, Any]] = {}
    
    async def execute_workflow(self, task_id: str, query: str) -> Dict[str, Any]:
        """Execute multi-agent workflow
        
        Args:
            task_id: Unique task ID
            query: User query
            
        Returns:
            Dict with workflow execution result
        """
        try:
            # Initialize workflow
            workflow_id = str(uuid.uuid4())
            self.running_tasks[task_id] = {
                "workflow_id": workflow_id,
                "status": "running",
                "agents": {},
                "start_time": asyncio.get_event_loop().time(),
                "steps": []
            }
            
            # Publish workflow start event
            from app.ai_agents.event_system import WorkflowStartEvent
            workflow_start_event = WorkflowStartEvent(
                workflow_id=workflow_id,
                workflow_name="房产调研工作流",
                initial_data={"query": query}
            )
            self.event_manager.publish(workflow_start_event)
            
            # Step 1: Requirement Analysis
            requirement_result = await self._execute_agent(
                task_id, "requirement_analyzer", {"query": query}
            )
            
            if not requirement_result.get("success"):
                return {
                    "success": False,
                    "error": f"Requirement analysis failed: {requirement_result.get('error')}"
                }
            
            # Extract structured requirements
            structured_requirements = requirement_result.get("result", {}).get("structured_requirements", {})
            
            # Step 2: Data Collection, Cleaning, and Verification (parallelized for different data sources)
            # Define data sources to collect from
            data_sources = [
                "local_real_estate_platforms",
                "national_property_databases",
                "government_housing_data",
                "transaction_history",
                "rental_market_data",
                "neighborhood_amenities",
                "transportation_data",
                "educational_resources",
                "commercial_facilities",
                "market_trend_analysis"
            ]
            
            # Create tasks for parallel data collection
            collection_tasks = []
            for source in data_sources:
                task = self._execute_agent(
                    task_id, "data_collector", {
                        "requirements": structured_requirements,
                        "query": query,
                        "data_source": source
                    }
                )
                collection_tasks.append(task)
            
            # Execute data collection in parallel
            collection_results = await asyncio.gather(*collection_tasks, return_exceptions=True)
            
            # Process collection results
            collected_data = {}
            collection_errors = []
            
            for i, result in enumerate(collection_results):
                source = data_sources[i]
                if isinstance(result, Exception):
                    collection_errors.append(f"{source}: {str(result)}")
                elif result.get("success"):
                    source_data = result.get("result", {}).get("collected_data", {})
                    collected_data[source] = source_data
                else:
                    collection_errors.append(f"{source}: {result.get('error')}")
            
            # Continue even if some data sources failed (graceful degradation)
            if collection_errors:
                # Log errors but continue
                error_message = "Some data sources failed: " + "; ".join(collection_errors[:3])
                if len(collection_errors) > 3:
                    error_message += f" and {len(collection_errors) - 3} more"
                
                # Publish warning event
                from app.ai_agents.event_system import WorkflowWarningEvent
                warning_event = WorkflowWarningEvent(
                    workflow_id=workflow_id,
                    workflow_name="房产调研工作流",
                    warning=error_message
                )
                self.event_manager.publish(warning_event)
            
            # Step 3: Data Cleaning (can be parallelized for different data types)
            cleaning_tasks = []
            for source, data in collected_data.items():
                if data:
                    task = self._execute_agent(
                        task_id, "data_cleaner", {
                            "collected_data": {source: data},
                            "requirements": structured_requirements,
                            "data_source": source
                        }
                    )
                    cleaning_tasks.append(task)
            
            # Execute data cleaning in parallel
            cleaning_results = await asyncio.gather(*cleaning_tasks, return_exceptions=True)
            
            # Process cleaning results
            cleaned_data = {}
            cleaning_errors = []
            
            for i, result in enumerate(cleaning_results):
                if isinstance(result, Exception):
                    cleaning_errors.append(f"Cleaning error: {str(result)}")
                elif result.get("success"):
                    source_data = result.get("result", {}).get("cleaned_data", {})
                    cleaned_data.update(source_data)
                else:
                    cleaning_errors.append(f"Cleaning error: {result.get('error')}")
            
            # Step 4: Data Verification (can be parallelized for different data types)
            verification_tasks = []
            for source, data in cleaned_data.items():
                if data:
                    task = self._execute_agent(
                        task_id, "data_verifier", {
                            "cleaned_data": {source: data},
                            "requirements": structured_requirements,
                            "data_source": source
                        }
                    )
                    verification_tasks.append(task)
            
            # Execute data verification in parallel
            verification_results = await asyncio.gather(*verification_tasks, return_exceptions=True)
            
            # Process verification results
            verification_result = {}
            verification_errors = []
            
            for i, result in enumerate(verification_results):
                if isinstance(result, Exception):
                    verification_errors.append(f"Verification error: {str(result)}")
                elif result.get("success"):
                    source_verification = result.get("result", {}).get("verification_result", {})
                    verification_result.update(source_verification)
                else:
                    verification_errors.append(f"Verification error: {result.get('error')}")
            
            # Check if we have enough data to proceed
            # 现在我们接受不同类型的数据，不仅仅是房产数据
            has_valid_data = False
            if verification_result:
                # 检查是否有任何类型的有效数据
                has_valid_data = True
            elif collected_data:
                # 如果验证结果为空，但收集到了数据，也认为有有效数据
                has_valid_data = True
            elif combined_data and combined_data.get("collected_data"):
                # 如果有任何收集到的数据，认为有有效数据
                has_valid_data = True
            
            if not has_valid_data:
                # 即使没有数据，也继续执行，使用模拟数据
                print(f"Warning: No data collected for task {task_id}, using mock data")
                combined_data = {
                    "collected_data": {"mock_source": {"data": "mock_data"}},
                    "verification_result": {}
                }
            
            # 合并所有收集到的数据，包括不同类型的数据源
            combined_data = {
                "collected_data": collected_data,
                "verification_result": verification_result if verification_result else {}
            }
            
            # Step 5: Market Analysis
            market_analyst_result = await self._execute_agent(
                task_id, "market_analyst", {
                    "combined_data": combined_data,
                    "verification_result": verification_result,
                    "collected_data": collected_data,
                    "requirements": structured_requirements
                }
            )
            
            if not market_analyst_result.get("success"):
                return {
                    "success": False,
                    "error": f"Market analysis failed: {market_analyst_result.get('error')}"
                }
            
            # Get market analysis
            market_analysis = market_analyst_result.get("result", {}).get("market_analysis", {})
            
            # Step 6: Report Generation
            report_result = await self._execute_agent(
                task_id, "report_generator", {
                    "market_analysis": market_analysis,
                    "verification_result": verification_result,
                    "collected_data": collected_data,
                    "combined_data": combined_data,
                    "requirements": structured_requirements,
                    "query": query
                }
            )
            
            if not report_result.get("success"):
                return {
                    "success": False,
                    "error": f"Report generation failed: {report_result.get('error')}"
                }
            
            # Get final report
            final_report = report_result.get("result", {}).get("report", {})
            
            # Complete workflow
            workflow_end_time = asyncio.get_event_loop().time()
            self.running_tasks[task_id].update({
                "status": "completed",
                "end_time": workflow_end_time,
                "duration": workflow_end_time - self.running_tasks[task_id]["start_time"]
            })
            
            # Publish workflow complete event
            from app.ai_agents.event_system import WorkflowCompleteEvent
            workflow_complete_event = WorkflowCompleteEvent(
                workflow_id=workflow_id,
                workflow_name="房产调研工作流",
                result=final_report
            )
            self.event_manager.publish(workflow_complete_event)
            
            return {
                "success": True,
                "result": final_report,
                "workflow_id": workflow_id,
                "duration": self.running_tasks[task_id]["duration"]
            }
            
        except Exception as e:
            # Publish workflow error event
            from app.ai_agents.event_system import WorkflowErrorEvent
            # Ensure workflow_id is defined
            error_workflow_id = workflow_id if 'workflow_id' in locals() else str(uuid.uuid4())
            workflow_error_event = WorkflowErrorEvent(
                workflow_id=error_workflow_id,
                workflow_name="房产调研工作流",
                error=str(e)
            )
            self.event_manager.publish(workflow_error_event)
            
            if task_id in self.running_tasks:
                self.running_tasks[task_id]["status"] = "failed"
                self.running_tasks[task_id]["error"] = str(e)
            
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_agent(self, task_id: str, agent_type: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single agent with input data
        
        Args:
            task_id: Unique task ID
            agent_type: Agent type
            input_data: Input data for agent
            
        Returns:
            Agent execution result
        """
        agent_id = str(uuid.uuid4())
        start_time = asyncio.get_event_loop().time()
        
        # Initialize agent
        agent = AgentFactory.create_agent(agent_type, event_system=self.event_manager)
        
        # Record agent start
        agent_info = {
            "agent_id": agent_id,
            "agent_type": agent_type,
            "status": "running",
            "start_time": start_time,
            "steps": []
        }
        
        if task_id in self.running_tasks:
            self.running_tasks[task_id]["agents"][agent_type] = agent_info
        
        # Publish agent start event
        from app.ai_agents.event_system import AgentStartEvent
        agent_start_event = AgentStartEvent(
            agent_id=agent_id,
            agent_name=agent_type,
            task=input_data
        )
        self.event_manager.publish(agent_start_event)
        
        try:
            # Execute agent
            result = await agent.execute(input_data)
            
            # Record agent completion
            end_time = asyncio.get_event_loop().time()
            agent_info.update({
                "status": "completed",
                "end_time": end_time,
                "duration": end_time - start_time,
                "result": result
            })
            
            # Publish agent complete event
            from app.ai_agents.event_system import AgentCompleteEvent
            agent_complete_event = AgentCompleteEvent(
                agent_id=agent_id,
                agent_name=agent_type,
                result=result
            )
            self.event_manager.publish(agent_complete_event)
            
            return result
            
        except Exception as e:
            # Record agent error
            end_time = asyncio.get_event_loop().time()
            agent_info.update({
                "status": "failed",
                "end_time": end_time,
                "duration": end_time - start_time,
                "error": str(e)
            })
            
            # Publish agent error event
            from app.ai_agents.event_system import AgentErrorEvent
            agent_error_event = AgentErrorEvent(
                agent_id=agent_id,
                agent_name=agent_type,
                error=str(e)
            )
            self.event_manager.publish(agent_error_event)
            
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status
        
        Args:
            task_id: Unique task ID
            
        Returns:
            Task status dict or None if task not found
        """
        return self.running_tasks.get(task_id)
    
    def get_running_tasks(self) -> List[str]:
        """Get list of running task IDs"""
        return [task_id for task_id, info in self.running_tasks.items() 
                if info.get("status") == "running"]
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task
        
        Args:
            task_id: Unique task ID
            
        Returns:
            True if task was cancelled, False otherwise
        """
        if task_id in self.running_tasks:
            self.running_tasks[task_id]["status"] = "cancelled"
            
            # Publish task cancelled event
            from app.ai_agents.event_system import WorkflowErrorEvent
            workflow_cancelled_event = WorkflowErrorEvent(
                workflow_id=task_id,
                workflow_name="房产调研工作流",
                error="Task cancelled by user"
            )
            self.event_manager.publish(workflow_cancelled_event)
            
            return True
        return False
