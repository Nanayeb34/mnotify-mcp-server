import os
import asyncio
from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.openrouter import OpenRouter
import functions  # Imports the MNotify functions
from context_cache import EntityCache
from tool_adapter import register_flex_functions

load_dotenv()

# Initialize the agent with OpenRouter model
model = OpenRouter(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    id="openai/gpt-oss-20b" 
)

agent = Agent(model=model)
cache = EntityCache()


# Add MNotify functions as tools to the agent
registered_flex = register_flex_functions(agent, functions)


SYSTEM_PROMPT = """You are a helpful assistant for working with the MNotify SMS API. You can:

1) Messaging and scheduling
- Send SMS to phone numbers or to one/more groups
- Schedule messages (require schedule_time when schedule is true)
- Enforce message length ≤ 460 characters

2) Contacts, groups, templates
- Create, update, delete, and list contacts and groups
- Create, update, delete, and list message templates
- Resolve ambiguous names by asking the user to choose

3) Reports and utilities
- Check delivery reports (by campaign or date range)
- Check SMS balance and sender ID status; register a sender ID

CRITICAL tool usage & error handling
- Always use the MNotify tools to perform real actions
- Validate inputs before calling tools (sender_id, recipients, message)
- When a tool fails: explain plainly, ask for missing info, suggest next steps
- Never invent IDs; when unknown, fetch the appropriate list first

ID handling & memory
- Use short “breadcrumbs” from recent tool results (group name → id, campaign id) maintained in a local entity cache
- If an ID is unknown, fetch list endpoints and continue

Input rules for tools (don’t mention tool names to the user)
- Strings must be quoted; lists are arrays of strings
- schedule=true requires a schedule_time in 'YYYY-MM-DD HH:MM'
- Keep user-facing text concise and professional
"""

async def chat_with_agent():
    """Interactive CLI for the MNotify Agent."""
    print("\n📨  MNotify Agent")
    print("  Manage contacts, groups, templates and SMS via MNotify.")
    print("  Type 'help' for commands. Type 'quit' to exit.\n")

    # Initialize conversation
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("Goodbye!")
                break

            if user_input.lower() in {'help', 'commands'}:
                print("\nCommands:")
                print("  help        Show commands")
                print("  history     Show recent messages")
                print("  tools       List available tools")
                print("  clear       Clear conversation context")
                print()
                continue
            
            if user_input.lower() == 'history':
                print("\n📜 Conversation History:")
                for i, msg in enumerate(messages[1:], 1):  # Skip system message
                    role = msg["role"]
                    content = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
                    print(f"{i}. {role.upper()}: {content}")
                print()
                continue

            if user_input.lower() == 'tools':
                print("\n🔧 Available tools:")
                for name in sorted(registered_flex):
                    print(f"  - {name}")
                print()
                continue
                

            if user_input.lower() == 'clear':
                messages = [{"role": "system", "content": SYSTEM_PROMPT}]
                print("Context cleared.\n")
                continue
            
            if not user_input:
                continue

            # Add user message
            messages.append({"role": "user", "content": user_input})

            # Get agent response with streaming
            print("Agent: ", end="", flush=True)
            
      
            full_response_content = ""
            tool_calls_made = []
            tool_results = []
            reasoning_steps = []
            tool_errors = []
            
            try:
                response_stream = agent.run(messages, stream=True, stream_intermediate_steps=False)
                
                for event in response_stream:
                    if event.event == "RunResponseContent":
                        print(event.content, end="", flush=True)
                        full_response_content += event.content
                    elif event.event == "ToolCallStarted":
                        tool_calls_made.append(event.tool)
                    elif event.event == "ReasoningStep":
                        reasoning_steps.append(event.content)
                    elif event.event == "ToolCallCompleted":
                        tool_name = getattr(event, 'tool_call', {}).get('name', 'unknown')
                        if hasattr(event, 'tool_call_result') and event.tool_call_result is not None:
                            tool_results.append({"tool": tool_name, "result": event.tool_call_result})
                        else:
                            tool_errors.append(tool_name)
                    elif event.event == "ToolCallError":
                        tool_name = getattr(event, 'tool_call', {}).get('name', 'unknown')
                        tool_errors.append(tool_name)
                        error_msg = getattr(event, 'error', 'Unknown error')
                # Index all tool results into cache
                for tr in tool_results:
                    tname = tr.get("tool", "")
                    tresult = tr.get("result")
                    try:
                        cache.index_tool_result(tname, tresult)
                    except Exception:
                        pass

                # Optionally add tiny breadcrumbs from cache for continuity
                memory_lines = cache.get_memory_lines_and_reset()
                if memory_lines:
                    messages.append({"role": "assistant", "content": "\n".join(memory_lines)})

                # Add the agent response to conversation history
                if full_response_content.strip():
                    messages.append({"role": "assistant", "content": full_response_content})
                elif tool_calls_made:
                    messages.append({"role": "assistant", "content": "I attempted to process your request but I didn't get a response. Please let me know and I can try a different approach or provide more details about what happened."})
                else:
                    messages.append({"role": "assistant", "content": "I'm not sure how to help with that request."})

                print("\n")
                
            except Exception as e:
                error_msg = f"Streaming error: {e}"
                print(f"\n❌ {error_msg}")
                messages.append({"role": "assistant", "content": f"Sorry, I encountered an error: {e}"})
                print()

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\nSorry, I encountered an error: {e}")
            print("Please try again.\n")

if __name__ == "__main__":
    if not os.getenv("OPENROUTER_API_KEY"):
        print("❌ Error: OPENROUTER_API_KEY environment variable not set")
        print("Please add your OpenRouter API key to your .env file")
        exit(1)
    
    if not os.getenv("MNOTIFY_API_KEY"):
        print("❌ Error: MNOTIFY_API_KEY environment variable not set")
        print("Please add your MNotify API key to your .env file")
        exit(1)

    print("🚀 Starting MNotify Agent...")
    asyncio.run(chat_with_agent()) 