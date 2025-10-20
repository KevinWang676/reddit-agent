#!/usr/bin/env python3
"""
Simple runner script for the Reddit Categorization Pipeline
Uses YAML configuration for easy customization
"""

import yaml
import sys
from categorization_pipeline import run_pipeline

def load_config(config_path="pipeline_config.yaml"):
    """Load configuration from YAML file"""
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        print(f"❌ Config file not found: {config_path}")
        print("Please create pipeline_config.yaml or specify a different config file")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"❌ Error parsing YAML config: {e}")
        sys.exit(1)

def main():
    # Load configuration
    config_file = sys.argv[1] if len(sys.argv) > 1 else "pipeline_config.yaml"
    config = load_config(config_file)
    
    # Extract parameters
    subreddit = config.get('subreddit', 'fashion')
    predefined_categories = config.get('predefined_categories')
    num_categories = config.get('num_auto_categories', 8)
    max_posts = config.get('max_posts')
    
    # Override global settings if specified in config
    import categorization_pipeline
    
    if 'openai_model' in config:
        categorization_pipeline.DEFAULT_MODEL = config['openai_model']
    
    if 'months_back' in config:
        categorization_pipeline.MONTHS_BACK = config['months_back']
    
    if 'min_score' in config:
        categorization_pipeline.MIN_SCORE = config['min_score']
    
    if 'min_num_comments' in config:
        categorization_pipeline.MIN_NUM_COMMENTS = config['min_num_comments']
    
    if 'output_directory' in config:
        categorization_pipeline.OUTPUT_DIR = config['output_directory']
    
    print(f"📋 Loaded configuration from: {config_file}")
    print(f"   Subreddit: r/{subreddit}")
    print(f"   Categories: {'Predefined (' + str(len(predefined_categories)) + ')' if predefined_categories else 'Auto-generate (' + str(num_categories) + ')'}")
    print()
    
    # Run pipeline
    run_pipeline(
        subreddit=subreddit,
        predefined_categories=predefined_categories if predefined_categories else None,
        num_categories=num_categories,
        max_posts=max_posts
    )

if __name__ == "__main__":
    main()

