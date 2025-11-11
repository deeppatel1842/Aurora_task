"""
Load messages from NDJSON file into cache.
Usage: python scripts/load_data.py [path_to_ndjson_file]
"""
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.data_fetcher import DataFetcher
from src.config import settings


def load_messages_from_file(file_path: str):
    """Load all messages from NDJSON file into cache."""
    
    print("=" * 80)
    print("Loading Messages into Cache")
    print("=" * 80)
    print(f"Source file: {file_path}")
    print(f"Cache directory: {settings.cache_dir}")
    print()
    
    # Read all messages from file
    all_messages = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if line.strip():
                    try:
                        msg = json.loads(line)
                        all_messages.append(msg)
                    except json.JSONDecodeError as e:
                        print(f"⚠️  Warning: Skipping line {line_num} - Invalid JSON: {e}")
                        
    except FileNotFoundError:
        print(f"❌ Error: File not found: {file_path}")
        return
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return
    
    print(f"✅ Loaded {len(all_messages)} total messages from file\n")
    
    # Count messages per user
    user_counts = {}
    for msg in all_messages:
        user_name = msg.get('senderName', 'Unknown')
        user_counts[user_name] = user_counts.get(user_name, 0) + 1
    
    print("📊 Messages per user:")
    for user_name in sorted(user_counts.keys(), key=lambda x: user_counts[x], reverse=True):
        print(f"  {user_name}: {user_counts[user_name]} messages")
    
    # Save to cache
    print(f"\n💾 Updating cache...")
    fetcher = DataFetcher()
    
    try:
        fetcher.cache.set(fetcher.cache_key, all_messages, expire=settings.cache_ttl)
        print("✅ Cache updated successfully!")
        
        # Verify
        cached = fetcher.cache.get(fetcher.cache_key, default=[])
        print(f"\n✓ Verification: Cache now has {len(cached)} messages")
        
    except Exception as e:
        print(f"❌ Error updating cache: {e}")
        return
    
    print("\n" + "=" * 80)
    print("✅ Data loading complete!")
    print("=" * 80)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        # Default to messages_checkpoint.ndjson in project root
        file_path = Path(__file__).parent.parent / "messages_checkpoint.ndjson"
    
    if not Path(file_path).exists():
        print(f"❌ Error: File not found: {file_path}")
        print(f"\nUsage: python {sys.argv[0]} [path_to_ndjson_file]")
        print(f"Example: python {sys.argv[0]} messages_checkpoint.ndjson")
        sys.exit(1)
    
    load_messages_from_file(str(file_path))
