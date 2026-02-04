#!/usr/bin/env python3
"""
AstroEngine 2.0 - Main Runner (Pure MongoDB & Lazy Loading)
Comprehensive Vedic Astrology reasoning engine with multi-agent architecture
"""

import argparse
import os
from dotenv import load_dotenv
from main_agent import MainAgent
from logger_config import setup_logger

load_dotenv()


def main():
    logger = setup_logger("AstroRunner")
    
    parser = argparse.ArgumentParser(
        description="AstroEngine 2.0 - Vedic Astrology Reasoning Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze by User Email
  python run.py --email user@example.com "How is my career?"
  
  # Analyze by Request ID
  python run.py --request_id <ID> "Will I get married soon?"
        """
    )
    
    parser.add_argument("query", nargs="?", help="The astrological question to analyze")
    parser.add_argument("--request_id", help="Request ID to fetch horoscope from MongoDB")
    parser.add_argument("--email", help="User email to fetch latest horoscope from MongoDB")

    args = parser.parse_args()

    # Check for API Key
    if not os.environ.get("GEMINI_API_KEY") and not os.environ.get("GOOGLE_CLOUD_API_KEY"):
        logger.critical("Neither GEMINI_API_KEY nor GOOGLE_CLOUD_API_KEY environment variable is set. Exiting.")
        print("\n❌ Error: API Key not found.")
        print("Please set GEMINI_API_KEY or GOOGLE_CLOUD_API_KEY in your .env file or environment variables.\n")
        return

    print("\n" + "="*70)
    print("🌟 ASTROENGINE 2.0 - VEDIC ASTROLOGY REASONING ENGINE 🌟")
    print("="*70 + "\n")
    
    logger.info("--- AstroEngine 2.0 Starting ---")
    
    try:
        # Initialize component
        agent = MainAgent()
        
        # Step 1: Set Identity
        print("📊 STEP 1: IDENTITY CONTEXT")
        print("-" * 70)
        
        if not args.request_id and not args.email:
            print("❌ Error: You must provide either --request_id or --email.")
            return

        agent.set_identity(request_id=args.request_id, email=args.email)
        print(f"✅ Identity set: {args.request_id or args.email}\n")
        
        # Step 2: Get Query
        print("❓ STEP 2: YOUR QUESTION")
        print("-" * 70)
        
        if args.query:
            query = args.query
            print(f"Query: {query}\n")
        else:
            query = input("Enter your astrological question: ").strip()
            if not query:
                print("❌ No query provided. Exiting.")
                return
            print()
        
        logger.info(f"Processing Query: {query}")
        
        # Step 3: Analysis
        print("🔮 STEP 3: ASTROLOGICAL ANALYSIS")
        print("-" * 70)
        print("Analyzing your question using Vedic astrology principles (Lazy Loading from DB)...")
        print("This may take a moment...\n")
        
        response, metrics = agent.run_flow(query)
        
        # Step 4: Display Results
        print("\n" + "="*70)
        print("📜 ASTROLOGICAL PREDICTION (LLM Generated)")
        print("="*70 + "\n")
        
        print(response)
        
        print("\n" + "="*70)
        print("📊 ANALYSIS METRICS")
        print("="*70)
        print(f"⏱️  Time Taken    : {metrics['duration_seconds']:.4f} seconds")
        print(f"📥 Input Tokens  : {metrics['input_tokens']:,}")
        print(f"📤 Output Tokens : {metrics['output_tokens']:,}")
        print("="*70 + "\n")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user.")
        
    except Exception as e:
        logger.critical(f"System error: {e}", exc_info=True)
        print(f"\n❌ An error occurred: {e}")
        print("Check astro_pipeline.log for details.\n")


if __name__ == "__main__":
    main()
