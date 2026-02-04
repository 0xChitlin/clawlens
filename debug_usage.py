#!/usr/bin/env python3
import json
import os
from datetime import datetime

# Test the usage parsing logic
sessions_dir = '/home/vivek/.moltbot/agents/main/sessions'
test_file = 'c024f2f0-cfd6-42ed-943f-f8e11235f875.jsonl'

daily_tokens = {}
daily_cost = {}
model_usage = {}

fpath = os.path.join(sessions_dir, test_file)
print(f"Testing file: {fpath}")

with open(fpath, 'r') as f:
    for line_num, line in enumerate(f):
        try:
            obj = json.loads(line.strip())
            
            # Only process message entries with usage data
            if obj.get('type') != 'message':
                continue
                
            message = obj.get('message', {})
            usage = message.get('usage')
            if not usage or not isinstance(usage, dict):
                continue
                
            print(f"Line {line_num}: Found usage data")
            print(f"  Total tokens: {usage.get('totalTokens', 0)}")
            print(f"  Cost: {usage.get('cost', {})}")
            
            # Extract the exact usage format from the brief
            tokens_data = {
                'input': usage.get('input', 0),
                'output': usage.get('output', 0),
                'cacheRead': usage.get('cacheRead', 0),
                'cacheWrite': usage.get('cacheWrite', 0),
                'totalTokens': usage.get('totalTokens', 0),
                'cost': usage.get('cost', {})
            }
            
            cost_data = tokens_data['cost']
            if isinstance(cost_data, dict) and 'total' in cost_data:
                total_cost = float(cost_data['total'])
            else:
                total_cost = 0.0
            
            # Extract model name
            model = message.get('model', 'unknown') or 'unknown'
            
            # Get timestamp and convert to date
            ts = obj.get('timestamp')
            if ts:
                # Handle ISO timestamp strings
                if isinstance(ts, str):
                    try:
                        dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                    except:
                        continue
                else:
                    # Handle numeric timestamps
                    dt = datetime.fromtimestamp(ts / 1000 if ts > 1e12 else ts)
                
                day = dt.strftime('%Y-%m-%d')
                
                print(f"  Date: {day}, Model: {model}, Cost: {total_cost}")
                
                # Aggregate daily tokens and costs
                daily_tokens[day] = daily_tokens.get(day, 0) + tokens_data['totalTokens']
                daily_cost[day] = daily_cost.get(day, 0) + total_cost
                
                # Track model usage
                model_usage[model] = model_usage.get(model, 0) + tokens_data['totalTokens']
                
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            if line_num < 10:  # Only show first 10 errors
                print(f"Line {line_num}: Error - {e}")
            continue

print(f"\nSummary:")
print(f"Daily tokens: {daily_tokens}")
print(f"Daily cost: {daily_cost}")
print(f"Model usage: {model_usage}")