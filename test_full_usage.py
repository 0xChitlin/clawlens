#!/usr/bin/env python3
import json
import os
from datetime import datetime, timedelta

# Test the usage parsing logic on all recent files
sessions_dir = '/home/vivek/.moltbot/agents/main/sessions'

daily_tokens = {}
daily_cost = {}
total_files = 0
files_with_usage = 0

# Get all .jsonl files
for fname in os.listdir(sessions_dir):
    if not fname.endswith('.jsonl'):
        continue
        
    fpath = os.path.join(sessions_dir, fname)
    total_files += 1
    has_usage = False
    
    try:
        with open(fpath, 'r') as f:
            for line in f:
                try:
                    obj = json.loads(line.strip())
                    
                    # Only process message entries with usage data
                    if obj.get('type') != 'message':
                        continue
                        
                    message = obj.get('message', {})
                    usage = message.get('usage')
                    if not usage or not isinstance(usage, dict):
                        continue
                    
                    has_usage = True
                    
                    # Extract cost data
                    cost_data = usage.get('cost', {})
                    if isinstance(cost_data, dict) and 'total' in cost_data:
                        total_cost = float(cost_data['total'])
                    else:
                        total_cost = 0.0
                    
                    # Get timestamp and convert to date
                    ts = obj.get('timestamp')
                    if ts and isinstance(ts, str):
                        try:
                            dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                        except:
                            continue
                        
                        day = dt.strftime('%Y-%m-%d')
                        
                        # Aggregate daily tokens and costs
                        daily_tokens[day] = daily_tokens.get(day, 0) + usage.get('totalTokens', 0)
                        daily_cost[day] = daily_cost.get(day, 0) + total_cost
                        
                except (json.JSONDecodeError, ValueError, KeyError):
                    continue
                    
        if has_usage:
            files_with_usage += 1
            
    except Exception as e:
        print(f"Error reading {fname}: {e}")
        continue

print(f"Processed {total_files} files, {files_with_usage} had usage data")

# Show recent days data
today = datetime.now()
for i in range(7, -1, -1):
    d = today - timedelta(days=i)
    ds = d.strftime('%Y-%m-%d')
    tokens = daily_tokens.get(ds, 0)
    cost = daily_cost.get(ds, 0)
    print(f"{ds}: {tokens:,} tokens, ${cost:.4f}")
    
print(f"\nTotal days with data: {len(daily_tokens)}")
print(f"Date range: {min(daily_tokens.keys()) if daily_tokens else 'None'} to {max(daily_tokens.keys()) if daily_tokens else 'None'}")