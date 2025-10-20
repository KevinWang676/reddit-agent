#!/usr/bin/env python3
"""
Example usage scripts for the Reddit Categorization Pipeline
"""

from categorization_pipeline import run_pipeline

def example_1_auto_categories():
    """Example 1: Auto-generate categories from fashion subreddit"""
    print("\n" + "="*60)
    print("EXAMPLE 1: Auto-generate categories")
    print("="*60 + "\n")
    
    run_pipeline(
        subreddit="fashion",
        num_categories=8,
        max_posts=100  # Limit for quick demo
    )

def example_2_predefined_categories():
    """Example 2: Use predefined categories"""
    print("\n" + "="*60)
    print("EXAMPLE 2: Predefined categories")
    print("="*60 + "\n")
    
    categories = [
        "Street Style",
        "Formal & Business Wear",
        "Thrift Finds",
        "Outfit Questions",
        "Shopping & Deals",
        "Sustainable Fashion",
        "Accessories",
        "Inspiration"
    ]
    
    run_pipeline(
        subreddit="fashion",
        predefined_categories=categories,
        max_posts=100  # Limit for quick demo
    )

def example_3_mixed_approach():
    """Example 3: Mix of predefined and flexible categories"""
    print("\n" + "="*60)
    print("EXAMPLE 3: Mixed approach - key categories predefined")
    print("="*60 + "\n")
    
    # Define must-have categories, let LLM discover others
    key_categories = [
        "Outfit of the Day",
        "Questions & Advice",
        "Shopping Haul"
    ]
    
    run_pipeline(
        subreddit="streetwear",
        predefined_categories=key_categories,
        max_posts=150
    )

def example_4_quick_test():
    """Example 4: Quick test with minimal posts"""
    print("\n" + "="*60)
    print("EXAMPLE 4: Quick test (50 posts only)")
    print("="*60 + "\n")
    
    run_pipeline(
        subreddit="fashion",
        num_categories=5,
        max_posts=50
    )

if __name__ == "__main__":
    import sys
    
    examples = {
        "1": example_1_auto_categories,
        "2": example_2_predefined_categories,
        "3": example_3_mixed_approach,
        "4": example_4_quick_test,
    }
    
    if len(sys.argv) > 1 and sys.argv[1] in examples:
        examples[sys.argv[1]]()
    else:
        print("Reddit Categorization Pipeline - Examples")
        print("=" * 60)
        print("\nUsage: python example_usage.py [1|2|3|4]")
        print("\nAvailable examples:")
        print("  1 - Auto-generate categories (fashion, 100 posts)")
        print("  2 - Use predefined categories (fashion, 100 posts)")
        print("  3 - Mixed approach (streetwear, 150 posts)")
        print("  4 - Quick test (fashion, 50 posts)")
        print("\nExample:")
        print("  python example_usage.py 4")
        print("\nOr run all examples:")
        print("  python example_usage.py 1")

