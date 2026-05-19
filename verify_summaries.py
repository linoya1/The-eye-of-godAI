#!/usr/bin/env python
"""Verify summaries are different from titles."""

from backend.db.supabase import get_supabase

db = get_supabase()

# Get last 2 inserted events
events = db.table('events').select('title, summary, created_at').order('created_at', desc=True).limit(2).execute()

print("\n" + "="*70)
print("📊 SUMMARY VERIFICATION")
print("="*70 + "\n")

for i, event in enumerate(events.data, 1):
    title = event['title']
    summary = event['summary']
    
    print(f"Article {i}:")
    print(f"  Title:   {title[:80]}...")
    print(f"  Summary: {summary[:80]}...")
    
    # Check if they're the same
    if title.lower() in summary.lower()[:100]:
        print("  ⚠️  WARNING: Summary contains title")
    else:
        print("  ✅ Summary is distinct from title")
    
    print()

print("="*70)
