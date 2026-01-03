#!/usr/bin/env python3
"""
Setup script for Avanti Feeds Scraper
Installs all required dependencies
"""

import subprocess
import sys
import os


def install_requirements():
    """Install required Python packages"""
    packages = [
        'requests',
        'feedparser',
        'beautifulsoup4',
        'yfinance',
        'lxml'
    ]

    print("Installing required packages...")
    print("="*60)

    for package in packages:
        print(f"\nInstalling {package}...")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package, '-q'])
            print(f"✓ {package} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"✗ Error installing {package}: {e}")
            return False

    print("\n" + "="*60)
    print("✓ All packages installed successfully!")
    return True


def create_env_template():
    """Create a template .env file for API keys"""
    env_content = """# Avanti Feeds Scraper Configuration
# Copy this file to .env and fill in your API keys

# NewsAPI Key (free at https://newsapi.org/)
NEWSAPI_KEY=your_api_key_here

# Twitter API Keys (if using tweepy for sentiment analysis)
TWITTER_API_KEY=your_api_key_here
TWITTER_API_SECRET=your_api_secret_here
TWITTER_BEARER_TOKEN=your_bearer_token_here

# Other optional configurations
PROXY_URL=
TIMEOUT=10
MAX_RETRIES=3
"""

    env_file = '.env.template'
    with open(env_file, 'w') as f:
        f.write(env_content)

    print(f"\n✓ Created {env_file}")
    print("  Copy to .env and fill in your API keys")


def main():
    """Main setup function"""
    print("\n" + "="*60)
    print("Avanti Feeds Scraper Setup")
    print("="*60 + "\n")

    # Install packages
    if not install_requirements():
        print("\n✗ Setup failed!")
        sys.exit(1)

    # Create env template
    create_env_template()

    print("\n" + "="*60)
    print("Setup completed successfully!")
    print("\nNext steps:")
    print("1. Optional: Get NewsAPI key from https://newsapi.org/")
    print("2. Copy .env.template to .env and add your API keys")
    print("3. Run: python avantifeed_news_scraper.py")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
