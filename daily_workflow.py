"""
Daily Workflow Runner - Complete morning to evening trading workflow.

Guides you through the entire daily trading process step by step.
"""

import os
import sys
from datetime import datetime

def morning_routine():
    """Morning routine - Generate signals and plan trades."""
    print("🌅 MORNING ROUTINE")
    print("=" * 40)
    
    # Step 1: Run trading system
    print("Step 1: Running Trading System...")
    print("Choose your market:")
    print("1. US Markets (NASDAQ/NYSE)")
    print("2. Indian Markets (NSE/BSE)")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == '1':
        print("\nRunning US Market System...")
        os.system("python run_us_trading.py")
        market = "US"
    elif choice == '2':
        print("\nRunning Indian Market System...")
        os.system("python run_indian_trading.py")
        market = "Indian"
    else:
        print("Invalid choice, defaulting to US markets")
        os.system("python run_us_trading.py")
        market = "US"
    
    # Step 2: Review signals
    print("\n" + "=" * 40)
    print("Step 2: Review Generated Signals")
    print("=" * 40)
    
    print("From the system output above:")
    print("✅ Note all APPROVED signals")
    print("❌ Ignore all REJECTED signals")
    print("📊 Record confidence scores")
    print("⚠️  Note position sizes and stop prices")
    
    # Step 3: Create trading plan
    print("\n" + "=" * 40)
    print("Step 3: Create Trading Plan")
    print("=" * 40)
    
    print("For each APPROVED signal, write down:")
    print("- Stock symbol")
    print("- Action (BUY/SELL)")
    print("- Number of shares")
    print("- Stop loss price")
    print("- Confidence level")
    
    input("\nPress Enter when you've noted all signals...")
    
    # Step 4: Log signals
    print("\n" + "=" * 40)
    print("Step 4: Log Signals (Optional)")
    print("=" * 40)
    
    log_choice = input("Do you want to log signals now? (y/n): ").strip().lower()
    if log_choice == 'y':
        os.system("python trade_logger.py")
    
    print("\n✅ Morning routine complete!")
    print("Next: Execute trades during market hours")
    
    return market

def market_hours_guide():
    """Market hours guidance."""
    print("\n📈 MARKET HOURS EXECUTION")
    print("=" * 40)
    
    print("CRITICAL RULES:")
    print("✅ Execute ONLY approved signals")
    print("✅ Use EXACT position sizes")
    print("✅ Set stop losses IMMEDIATELY")
    print("✅ Use MARKET orders for entries")
    print("❌ DO NOT override system decisions")
    print("❌ DO NOT change position sizes")
    print("❌ DO NOT move stop losses")
    
    print("\nFor each approved signal:")
    print("1. Place market buy order")
    print("2. Record actual fill price")
    print("3. Set stop loss order immediately")
    print("4. Confirm stop is active")
    
    input("\nPress Enter when market execution is complete...")

def evening_routine():
    """Evening routine - Log outcomes and review."""
    print("\n🌙 EVENING ROUTINE")
    print("=" * 40)
    
    # Step 1: Log outcomes
    print("Step 1: Log Trade Outcomes")
    print("For each trade today, record:")
    print("- Actual entry price (vs planned)")
    print("- Stop loss status (active/triggered)")
    print("- Any exits that occurred")
    print("- P&L for closed trades")
    
    log_choice = input("\nUpdate trade log now? (y/n): ").strip().lower()
    if log_choice == 'y':
        os.system("python trade_logger.py")
    
    # Step 2: Review performance
    print("\n" + "=" * 40)
    print("Step 2: Daily Review Questions")
    print("=" * 40)
    
    questions = [
        "Did I execute all approved signals exactly?",
        "Did I set all stop losses immediately?",
        "Did I override any system decisions? (Should be NO)",
        "Are all my positions properly managed?",
        "Did I follow the system discipline?"
    ]
    
    print("Answer these questions honestly:")
    for i, question in enumerate(questions, 1):
        answer = input(f"{i}. {question} (y/n): ").strip().lower()
        if answer == 'n' and i < 5:
            print("   Note: Review why and improve tomorrow")
    
    # Step 3: Plan tomorrow
    print("\n" + "=" * 40)
    print("Step 3: Plan Tomorrow")
    print("=" * 40)
    
    print("Quick checklist:")
    print("- Any positions to monitor tomorrow?")
    print("- Any stops that might trigger?")
    print("- System running smoothly?")
    print("- Any observations to note?")
    
    notes = input("\nAny notes for tomorrow? (optional): ")
    if notes:
        with open("daily_notes.txt", "a") as f:
            f.write(f"{datetime.now().strftime('%Y-%m-%d')}: {notes}\n")
    
    print("\n✅ Evening routine complete!")
    print("See you tomorrow for the next trading day!")

def full_workflow():
    """Complete daily workflow."""
    print("🎯 COMPLETE DAILY TRADING WORKFLOW")
    print("=" * 50)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d')}")
    print("=" * 50)
    
    # Morning
    market = morning_routine()
    
    # Market hours
    market_hours_guide()
    
    # Evening
    evening_routine()
    
    print("\n🎉 Daily workflow complete!")
    print("Remember: Consistency and discipline are key to success.")

def quick_menu():
    """Quick menu for specific workflow steps."""
    print("🎯 DAILY WORKFLOW MENU")
    print("=" * 30)
    print("1. Full Daily Workflow")
    print("2. Morning Routine Only")
    print("3. Market Hours Guide")
    print("4. Evening Routine Only")
    print("5. Trade Logger")
    print("6. Exit")
    
    while True:
        choice = input("\nChoose option (1-6): ").strip()
        
        if choice == '1':
            full_workflow()
            break
        elif choice == '2':
            morning_routine()
            break
        elif choice == '3':
            market_hours_guide()
            break
        elif choice == '4':
            evening_routine()
            break
        elif choice == '5':
            os.system("python trade_logger.py")
            break
        elif choice == '6':
            print("Happy trading!")
            break
        else:
            print("Invalid choice, please try again")

if __name__ == "__main__":
    quick_menu()