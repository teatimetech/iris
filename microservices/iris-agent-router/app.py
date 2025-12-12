import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from core.agents.agent_router import iris_agent # Import the LangGraph agent

app = FastAPI(title="IRIS Agent Router", version="v1")

class ChatRequest(BaseModel):
    user_id: str
    prompt: str

class ChatResponse(BaseModel):
    response: str

@app.get("/health")
async def health_check():
    """Health check endpoint for Kubernetes probes and monitoring."""
    return {
        "status": "healthy",
        "service": "iris-agent-router"
    }
    
@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Endpoint for routing chat prompts through the LangGraph agent."""
    try:
        # Initial State for the LangGraph agent
        initial_state = {
            "user_id": request.user_id,
            "messages": [("human", request.prompt)],
            "intent": "",
            "tool_outputs": {}
        }
        
        # Run the compiled LangGraph agent
        final_state = iris_agent.invoke(initial_state)
        
        # Extract the final AI response
        final_msg_obj = final_state['messages'][-1]
        final_message = final_msg_obj.content if hasattr(final_msg_obj, 'content') else final_msg_obj[1]
        
        return ChatResponse(response=final_message)
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Agent execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Agent Error: {e}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)