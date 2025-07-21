#!/usr/bin/env python3
"""
Run housekeeper once to process pending instructions
"""

exec(open('auto-housekeeper.py').read())

if __name__ == "__main__":
    print("Running housekeeper once...")
    housekeeper = SuperAgentHousekeeper()
    
    # Check for instructions
    instructions = housekeeper.check_instructions()
    print(f"Found {len(instructions)} pending instructions")
    
    # Process them
    for instruction in instructions:
        result = housekeeper.process_instruction(instruction)
        print(f"Processed: {instruction['command']} -> {result['status']}")
    
    print("Done!")