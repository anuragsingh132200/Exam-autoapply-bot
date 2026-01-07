"""
WebSocket API
Handles real-time communication for workflow execution.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Optional
from datetime import datetime
import json
import asyncio

from app.models.session import WorkflowSession


router = APIRouter()


class ConnectionManager:
    """
    WebSocket connection manager.
    Handles multiple clients and message broadcasting.
    """
    
    def __init__(self):
        # Map session_id -> WebSocket connections
        self.active_connections: dict[str, list[WebSocket]] = {}
        # Map WebSocket -> session_id (reverse lookup)
        self.connection_sessions: dict[WebSocket, str] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str = None):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        
        if session_id:
            if session_id not in self.active_connections:
                self.active_connections[session_id] = []
            self.active_connections[session_id].append(websocket)
            self.connection_sessions[websocket] = session_id
        
        print(f"🔌 WebSocket connected: {session_id or 'no session'}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        session_id = self.connection_sessions.get(websocket)
        
        if session_id and session_id in self.active_connections:
            self.active_connections[session_id].remove(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
        
        if websocket in self.connection_sessions:
            del self.connection_sessions[websocket]
        
        print(f"❌ WebSocket disconnected: {session_id or 'unknown'}")
    
    async def send_personal(self, websocket: WebSocket, message: dict):
        """Send a message to a specific connection."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            print(f"Error sending message: {e}")
    
    async def send_to_session(self, session_id: str, message: dict):
        """Send a message to all connections watching a session."""
        if session_id in self.active_connections:
            for connection in self.active_connections[session_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    print(f"Error sending to session {session_id}: {e}")
    
    async def broadcast(self, message: dict):
        """Send a message to all connected clients."""
        for session_id in self.active_connections:
            await self.send_to_session(session_id, message)


# Global connection manager
manager = ConnectionManager()


# ============= Message Types =============

class MessageTypes:
    # Client -> Server
    START_WORKFLOW = "START_WORKFLOW"
    START_BATCH = "START_BATCH"
    OTP_SUBMIT = "OTP_SUBMIT"
    CAPTCHA_SUBMIT = "CAPTCHA_SUBMIT"
    CUSTOM_SUBMIT = "CUSTOM_INPUT_SUBMIT"
    PAUSE_WORKFLOW = "PAUSE_WORKFLOW"
    RESUME_WORKFLOW = "RESUME_WORKFLOW"
    
    # Server -> Client
    LOG = "LOG"
    SCREENSHOT = "SCREENSHOT"
    REQUEST_OTP = "REQUEST_OTP"
    REQUEST_CAPTCHA = "REQUEST_CAPTCHA"
    REQUEST_CUSTOM = "REQUEST_CUSTOM_INPUT"
    STATUS = "STATUS"
    BATCH_PROGRESS = "BATCH_PROGRESS"
    RESULT = "RESULT"


# ============= WebSocket Endpoints =============

@router.websocket("/workflow/{session_id}")
async def workflow_websocket(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for workflow monitoring.
    Clients connect here to receive real-time updates.
    """
    await manager.connect(websocket, session_id)
    
    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            await handle_client_message(websocket, session_id, message)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)


@router.websocket("/workflow")
async def workflow_websocket_new(websocket: WebSocket):
    """
    WebSocket endpoint for starting new workflows.
    Session ID is determined after START_WORKFLOW message.
    """
    await manager.connect(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle START_WORKFLOW to get session ID
            if message.get("type") == MessageTypes.START_WORKFLOW:
                session_id = await handle_start_workflow(websocket, message)
                if session_id:
                    # Register connection with session
                    if session_id not in manager.active_connections:
                        manager.active_connections[session_id] = []
                    manager.active_connections[session_id].append(websocket)
                    manager.connection_sessions[websocket] = session_id
            else:
                session_id = manager.connection_sessions.get(websocket)
                if session_id:
                    await handle_client_message(websocket, session_id, message)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)


# ============= Message Handlers =============

async def handle_client_message(websocket: WebSocket, session_id: str, message: dict):
    """Handle incoming client messages."""
    msg_type = message.get("type")
    payload = message.get("payload", {})
    
    if msg_type == MessageTypes.OTP_SUBMIT:
        await handle_otp_submit(session_id, payload)
    
    elif msg_type == MessageTypes.CAPTCHA_SUBMIT:
        await handle_captcha_submit(session_id, payload)
    
    elif msg_type == MessageTypes.CUSTOM_SUBMIT:
        await handle_custom_submit(session_id, payload)
    
    elif msg_type == MessageTypes.PAUSE_WORKFLOW:
        await handle_pause_workflow(session_id)
    
    elif msg_type == MessageTypes.RESUME_WORKFLOW:
        await handle_resume_workflow(session_id)
    
    else:
        await manager.send_personal(websocket, {
            "type": "ERROR",
            "payload": {"message": f"Unknown message type: {msg_type}"}
        })


async def handle_start_workflow(websocket: WebSocket, message: dict) -> Optional[str]:
    """
    Handle START_WORKFLOW message.
    Creates a new workflow session and starts LangGraph execution.
    """
    payload = message.get("payload", {})
    exam_id = payload.get("examId")
    user_id = payload.get("userId")
    
    if not exam_id or not user_id:
        await manager.send_personal(websocket, {
            "type": "ERROR",
            "payload": {"message": "Missing examId or userId"}
        })
        return None
    
    # Import required modules
    from beanie import PydanticObjectId
    from app.models.exam import Exam
    from app.models.user import User
    from app.graph.builder import run_workflow
    
    # Get exam and user data
    exam = await Exam.get(PydanticObjectId(exam_id))
    user = await User.get(PydanticObjectId(user_id))
    
    if not exam:
        await manager.send_personal(websocket, {
            "type": "ERROR",
            "payload": {"message": f"Exam not found: {exam_id}"}
        })
        return None
    
    if not user:
        await manager.send_personal(websocket, {
            "type": "ERROR",
            "payload": {"message": f"User not found: {user_id}"}
        })
        return None
    
    # Create workflow session
    session = WorkflowSession(
        exam_id=PydanticObjectId(exam_id),
        user_id=PydanticObjectId(user_id),
        status="running",
        started_at=datetime.utcnow(),
    )
    await session.insert()
    
    session_id = str(session.id)
    
    # Send confirmation
    await manager.send_personal(websocket, {
        "type": "SESSION_CREATED",
        "payload": {"sessionId": session_id}
    })
    
    # Log
    session.add_log("Workflow session created", level="info")
    await session.save()
    
    await manager.send_personal(websocket, {
        "type": MessageTypes.LOG,
        "payload": {"message": f"Starting automation for {exam.name}...", "level": "info"}
    })
    
    # Start LangGraph workflow in background task
    asyncio.create_task(
        execute_workflow(
            session_id=session_id,
            exam_id=exam_id,
            user_id=user_id,
            exam_url=exam.url,
            exam_name=exam.name,
            field_mappings={k: v.model_dump() for k, v in exam.field_mappings.items()},
            user_data=user.get_flat_data(),
        )
    )
    
    return session_id


async def execute_workflow(
    session_id: str,
    exam_id: str,
    user_id: str,
    exam_url: str,
    exam_name: str,
    field_mappings: dict,
    user_data: dict,
):
    """
    Execute the LangGraph workflow.
    Runs in a background task.
    """
    from app.graph.builder import run_workflow
    from beanie import PydanticObjectId
    
    try:
        result = await run_workflow(
            session_id=session_id,
            exam_id=exam_id,
            user_id=user_id,
            exam_url=exam_url,
            exam_name=exam_name,
            field_mappings=field_mappings,
            user_data=user_data,
        )
        
        # Update session with final result
        session = await WorkflowSession.get(PydanticObjectId(session_id))
        if session:
            session.status = result.get("status", "completed")
            session.result_message = result.get("result_message")
            session.completed_at = datetime.utcnow()
            await session.save()
            
    except Exception as e:
        # Handle errors
        await send_log(session_id, f"Workflow error: {str(e)}", "error")
        await send_result(session_id, False, f"Workflow failed: {str(e)}")
        
        session = await WorkflowSession.get(PydanticObjectId(session_id))
        if session:
            session.status = "failed"
            session.result_message = str(e)
            session.completed_at = datetime.utcnow()
            await session.save()


async def handle_otp_submit(session_id: str, payload: dict):
    """Handle OTP submission from user. Resumes LangGraph workflow."""
    otp = payload.get("otp")
    
    from beanie import PydanticObjectId
    from app.graph.builder import resume_workflow
    
    session = await WorkflowSession.get(PydanticObjectId(session_id))
    
    if session:
        session.add_log("OTP received from user", level="info")
        session.pending_input = None
        await session.save()
        
        # Notify client
        await manager.send_to_session(session_id, {
            "type": MessageTypes.LOG,
            "payload": {"message": "OTP received, continuing...", "level": "success"}
        })
        
        # Resume LangGraph workflow with the OTP value
        asyncio.create_task(resume_workflow_task(session_id, otp))


async def handle_captcha_submit(session_id: str, payload: dict):
    """Handle captcha solution submission from user. Resumes LangGraph workflow."""
    solution = payload.get("solution")
    
    from beanie import PydanticObjectId
    session = await WorkflowSession.get(PydanticObjectId(session_id))
    
    if session:
        session.add_log("Captcha solution received from user", level="info")
        session.pending_input = None
        await session.save()
        
        await manager.send_to_session(session_id, {
            "type": MessageTypes.LOG,
            "payload": {"message": "Captcha solution received, continuing...", "level": "success"}
        })
        
        # Resume LangGraph workflow with the captcha solution
        asyncio.create_task(resume_workflow_task(session_id, solution))


async def handle_custom_submit(session_id: str, payload: dict):
    """Handle custom field submission from user. Resumes LangGraph workflow."""
    field_id = payload.get("fieldId")
    value = payload.get("value")
    
    from beanie import PydanticObjectId
    session = await WorkflowSession.get(PydanticObjectId(session_id))
    
    if session:
        session.add_log(f"Custom input received for field: {field_id}", level="info")
        session.pending_input = None
        await session.save()
        
        await manager.send_to_session(session_id, {
            "type": MessageTypes.LOG,
            "payload": {"message": f"Input received for {field_id}, continuing...", "level": "success"}
        })
        
        # Resume LangGraph workflow with the custom input value
        asyncio.create_task(resume_workflow_task(session_id, value))


async def resume_workflow_task(session_id: str, user_input: any):
    """
    Resume a paused LangGraph workflow with user input.
    This is called after user provides OTP, captcha, or custom input.
    """
    from app.graph.builder import resume_workflow
    from beanie import PydanticObjectId
    
    try:
        result = await resume_workflow(session_id, user_input)
        
        # Update session with result if workflow completed
        if result.get("status") in ["success", "failed"]:
            session = await WorkflowSession.get(PydanticObjectId(session_id))
            if session:
                session.status = result.get("status", "completed")
                session.result_message = result.get("result_message")
                session.completed_at = datetime.utcnow()
                await session.save()
                
    except Exception as e:
        await send_log(session_id, f"Resume error: {str(e)}", "error")
        await send_result(session_id, False, f"Resume failed: {str(e)}")


async def handle_pause_workflow(session_id: str):
    """Handle workflow pause request."""
    from beanie import PydanticObjectId
    session = await WorkflowSession.get(PydanticObjectId(session_id))
    
    if session and session.status == "running":
        session.status = "paused"
        session.add_log("Workflow paused by user", level="warning")
        await session.save()
        
        await manager.send_to_session(session_id, {
            "type": MessageTypes.STATUS,
            "payload": {"step": session.current_step, "status": "paused", "message": "Workflow paused"}
        })


async def handle_resume_workflow(session_id: str):
    """Handle workflow resume request."""
    from beanie import PydanticObjectId
    session = await WorkflowSession.get(PydanticObjectId(session_id))
    
    if session and session.status == "paused":
        session.status = "running"
        session.add_log("Workflow resumed by user", level="info")
        await session.save()
        
        await manager.send_to_session(session_id, {
            "type": MessageTypes.STATUS,
            "payload": {"step": session.current_step, "status": "running", "message": "Workflow resumed"}
        })
        
        # TODO: Resume LangGraph execution from checkpoint


# ============= Helper Functions for Graph Nodes =============

async def send_screenshot(session_id: str, image_base64: str, step: str):
    """Send screenshot update to connected clients."""
    await manager.send_to_session(session_id, {
        "type": MessageTypes.SCREENSHOT,
        "payload": {
            "imageBase64": image_base64,
            "step": step,
            "timestamp": datetime.utcnow().isoformat()
        }
    })


async def send_log(session_id: str, message: str, level: str = "info"):
    """Send log message to connected clients."""
    await manager.send_to_session(session_id, {
        "type": MessageTypes.LOG,
        "payload": {"message": message, "level": level}
    })


async def send_status(session_id: str, step: str, progress: int, message: str):
    """Send status update to connected clients."""
    await manager.send_to_session(session_id, {
        "type": MessageTypes.STATUS,
        "payload": {
            "step": step,
            "progress": progress,
            "message": message,
            "status": "running"
        }
    })


async def request_otp(session_id: str):
    """Request OTP from user."""
    await manager.send_to_session(session_id, {
        "type": MessageTypes.REQUEST_OTP,
        "payload": {}
    })


async def request_captcha(session_id: str, image_base64: str, auto_solving: bool = False):
    """Request captcha solution from user."""
    await manager.send_to_session(session_id, {
        "type": MessageTypes.REQUEST_CAPTCHA,
        "payload": {
            "imageBase64": image_base64,
            "autoSolving": auto_solving
        }
    })


async def request_custom_input(
    session_id: str,
    field_id: str,
    label: str,
    field_type: str,
    suggestions: list[str] = None
):
    """Request custom input from user."""
    await manager.send_to_session(session_id, {
        "type": MessageTypes.REQUEST_CUSTOM,
        "payload": {
            "fieldId": field_id,
            "label": label,
            "type": field_type,
            "suggestions": suggestions or []
        }
    })


async def send_result(session_id: str, success: bool, message: str):
    """Send workflow result to connected clients."""
    await manager.send_to_session(session_id, {
        "type": MessageTypes.RESULT,
        "payload": {"success": success, "message": message}
    })
