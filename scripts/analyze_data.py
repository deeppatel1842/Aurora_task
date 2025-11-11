"""
Data analysis script to identify anomalies and inconsistencies.
"""
import requests
from collections import Counter, defaultdict
from datetime import datetime
import re


def fetch_all_messages():
    """Fetch all messages from the API."""
    url = "https://november7-730026606190.europe-west1.run.app/messages/"
    all_messages = []
    skip = 0
    limit = 100
    
    while True:
        response = requests.get(url, params={"skip": skip, "limit": limit})
        data = response.json()
        messages = data.get("items", [])
        
        if not messages:
            break
            
        all_messages.extend(messages)
        
        if len(all_messages) >= data.get("total", 0):
            break
            
        skip += limit
    
    return all_messages


def analyze_data(messages):
    """Analyze the dataset for anomalies and inconsistencies."""
    print("=" * 80)
    print("DATA ANALYSIS REPORT")
    print("=" * 80)
    print(f"\nTotal Messages: {len(messages)}")
    
    # User analysis
    user_messages = defaultdict(list)
    user_ids = {}
    
    for msg in messages:
        user_name = msg['user_name']
        user_id = msg['user_id']
        user_messages[user_name].append(msg)
        
        # Check for user ID consistency
        if user_name in user_ids and user_ids[user_name] != user_id:
            print(f"\n⚠️  ANOMALY: User '{user_name}' has multiple user IDs!")
            print(f"   - {user_ids[user_name]}")
            print(f"   - {user_id}")
        user_ids[user_name] = user_id
    
    print(f"\nTotal Unique Users: {len(user_messages)}")
    print("\nTop 10 Most Active Users:")
    for user, msgs in sorted(user_messages.items(), key=lambda x: len(x[1]), reverse=True)[:10]:
        print(f"  - {user}: {len(msgs)} messages")
    
    # Timestamp analysis
    print("\n" + "-" * 80)
    print("TIMESTAMP ANALYSIS")
    print("-" * 80)
    
    timestamps = []
    invalid_timestamps = []
    
    for msg in messages:
        try:
            ts = datetime.fromisoformat(msg['timestamp'].replace('+00:00', ''))
            timestamps.append(ts)
        except:
            invalid_timestamps.append(msg['timestamp'])
    
    if invalid_timestamps:
        print(f"\n⚠️  ANOMALY: {len(invalid_timestamps)} invalid timestamps found")
    
    if timestamps:
        timestamps.sort()
        print(f"Earliest Message: {timestamps[0]}")
        print(f"Latest Message: {timestamps[-1]}")
        
        # Check for future dates
        now = datetime.now()
        future_messages = [ts for ts in timestamps if ts > now]
        if future_messages:
            print(f"\n⚠️  ANOMALY: {len(future_messages)} messages with future timestamps!")
    
    # Content analysis
    print("\n" + "-" * 80)
    print("CONTENT ANALYSIS")
    print("-" * 80)
    
    # Empty or very short messages
    short_messages = [msg for msg in messages if len(msg['message']) < 10]
    if short_messages:
        print(f"\n⚠️  ANOMALY: {len(short_messages)} messages are unusually short (< 10 chars)")
    
    # Very long messages
    long_messages = [msg for msg in messages if len(msg['message']) > 500]
    if long_messages:
        print(f"⚠️  ANOMALY: {len(long_messages)} messages are unusually long (> 500 chars)")
    
    # Duplicate messages
    message_texts = [msg['message'] for msg in messages]
    duplicates = [item for item, count in Counter(message_texts).items() if count > 1]
    if duplicates:
        print(f"\n⚠️  ANOMALY: {len(duplicates)} duplicate message texts found")
        print(f"Total duplicate occurrences: {sum(Counter(message_texts)[d] for d in duplicates)}")
    
    # Message patterns
    print("\n" + "-" * 80)
    print("MESSAGE PATTERNS")
    print("-" * 80)
    
    patterns = {
        "Reservations": ["reservation", "book", "reserve"],
        "Travel": ["trip", "flight", "travel", "jet"],
        "Preferences": ["prefer", "preference", "like"],
        "Complaints": ["issue", "problem", "wrong", "haven't received"],
        "Updates": ["update", "change", "new"],
        "Gratitude": ["thank", "thanks", "grateful", "appreciate"]
    }
    
    pattern_counts = defaultdict(int)
    for msg in messages:
        msg_lower = msg['message'].lower()
        for pattern_name, keywords in patterns.items():
            if any(keyword in msg_lower for keyword in keywords):
                pattern_counts[pattern_name] += 1
    
    print("\nMessage Categories:")
    for pattern, count in sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / len(messages)) * 100
        print(f"  - {pattern}: {count} ({percentage:.1f}%)")
    
    # Data quality issues
    print("\n" + "-" * 80)
    print("DATA QUALITY ISSUES")
    print("-" * 80)
    
    # Missing fields
    for field in ['id', 'user_id', 'user_name', 'timestamp', 'message']:
        missing = [msg for msg in messages if not msg.get(field)]
        if missing:
            print(f"⚠️  CRITICAL: {len(missing)} messages missing '{field}' field")
    
    # ID uniqueness
    ids = [msg['id'] for msg in messages]
    duplicate_ids = [item for item, count in Counter(ids).items() if count > 1]
    if duplicate_ids:
        print(f"\n⚠️  CRITICAL: {len(duplicate_ids)} duplicate message IDs found!")
    else:
        print(f"✓ All message IDs are unique")
    
    # User name format inconsistencies
    print("\n" + "-" * 80)
    print("USER NAME ANALYSIS")
    print("-" * 80)
    
    name_patterns = defaultdict(list)
    for user_name in user_messages.keys():
        parts = user_name.split()
        name_patterns[len(parts)].append(user_name)
    
    print("\nName structure:")
    for num_parts, names in sorted(name_patterns.items()):
        print(f"  - {num_parts} parts: {len(names)} users")
        if num_parts == 1:
            print(f"    ⚠️  Single name users: {', '.join(names[:5])}")
    
    print("\n" + "=" * 80)
    print("END OF ANALYSIS")
    print("=" * 80)


if __name__ == "__main__":
    print("Fetching data from API...")
    messages = fetch_all_messages()
    print(f"Fetched {len(messages)} messages\n")
    analyze_data(messages)
