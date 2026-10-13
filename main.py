#!/usr/bin/env python3
"""
Cyber Ronin - CLI Entry Point
An AI agent for defensive cybersecurity and system administration tasks.
"""
import sys
import argparse
from agent import create_agent, CyberRoninAgent


def main():
    parser = argparse.ArgumentParser(
        description="Cyber Ronin - Natural language cybersecurity assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py "scan 192.168.1.1 for open ports"
  python main.py "check for failed logins in /var/log/auth.log"
  python main.py "show system health"
  python main.py "list processes named python"
  python main.py --interactive
        """
    )
    parser.add_argument("query", nargs="*", help="Natural language query")
    parser.add_argument("-i", "--interactive", action="store_true", 
                        help="Run in interactive mode")
    parser.add_argument("--llm", choices=["mock", "openai"], default="mock",
                        help="LLM provider to use")
    parser.add_argument("--api-key", help="API key for LLM provider")
    parser.add_argument("--model", default="gpt-4o-mini", help="Model name for OpenAI")
    
    args = parser.parse_args()
    
    # Create agent
    llm_kwargs = {}
    if args.llm == "openai":
        if not args.api_key:
            print("Error: --api-key required for OpenAI provider")
            sys.exit(1)
        llm_kwargs = {"api_key": args.api_key, "model": args.model}
    
    agent = create_agent(args.llm, **llm_kwargs)
    
    if args.interactive or not args.query:
        # Interactive mode
        print("Cyber Ronin - Interactive Mode")
        print("Type 'exit' or 'quit' to quit\n")
        
        while True:
            try:
                user_input = input("ronin> ").strip()
                if user_input.lower() in ('exit', 'quit'):
                    break
                if not user_input:
                    continue
                
                response = agent.run(user_input)
                print(f"\n{response}\n")
                
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye!")
                break
    else:
        # Single query mode
        query = " ".join(args.query)
        response = agent.run(query)
        print(response)


if __name__ == "__main__":
    main()