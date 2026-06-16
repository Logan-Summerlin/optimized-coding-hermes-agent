#!/usr/bin/env python3
"""
Toolset Distributions Module

This module defines distributions of toolsets for data generation runs.
Each distribution specifies which toolsets should be used and their probability
of being selected for any given prompt during the batch processing.

A distribution is a dictionary mapping toolset names to their selection probability (%).
Probabilities should sum to 100, but the system will normalize if they don't.

Usage:
    from toolset_distributions import get_distribution, list_distributions
    
    # Get a specific distribution
    dist = get_distribution("development")
    
    # List all available distributions
    all_dists = list_distributions()
"""

from typing import Dict, List, Optional
import random
from toolsets import validate_toolset


# Distribution definitions
# Each key is a distribution name, and the value is a dict of toolset_name: probability_percentage
DISTRIBUTIONS = {
    "default": {
        "description": "Lean default: web, terminal, and file tools",
        "toolsets": {"web": 100, "terminal": 100, "file": 100},
    },
    "research": {
        "description": "Web-first research with optional local notes",
        "toolsets": {"web": 100, "file": 40, "terminal": 20},
    },
    "development": {
        "description": "Coding tasks with local terminal, files, and web lookup",
        "toolsets": {"terminal": 100, "file": 100, "web": 60},
    },
    "safe": {
        "description": "No terminal execution; web and file inspection only",
        "toolsets": {"web": 100, "file": 60},
    },
    "balanced": {
        "description": "Balanced lean toolset probabilities",
        "toolsets": {"web": 70, "terminal": 70, "file": 70},
    },
    "minimal": {
        "description": "Only web tools for basic research",
        "toolsets": {"web": 100},
    },
    "terminal_only": {
        "description": "Terminal and file tools for local coding tasks",
        "toolsets": {"terminal": 100, "file": 100},
    },
    "terminal_web": {
        "description": "Terminal and file tools with web lookup",
        "toolsets": {"terminal": 100, "file": 100, "web": 100},
    },
    "terminal_tasks": {
        "description": "Terminal-focused data generation tasks",
        "toolsets": {"terminal": 97, "file": 97, "web": 35},
    },
    "mixed_tasks": {
        "description": "Mixed lean local and web tasks",
        "toolsets": {"terminal": 92, "file": 92, "web": 50},
    },
    "reasoning": {
        "description": "Lean reasoning tasks with web lookup and optional terminal",
        "toolsets": {"web": 60, "terminal": 30, "file": 30},
    },
}

def get_distribution(name: str) -> Optional[Dict[str, any]]:
    """
    Get a toolset distribution by name.
    
    Args:
        name (str): Name of the distribution
        
    Returns:
        Dict: Distribution definition with description and toolsets
        None: If distribution not found
    """
    return DISTRIBUTIONS.get(name)


def list_distributions() -> Dict[str, Dict]:
    """
    List all available distributions.
    
    Returns:
        Dict: All distribution definitions
    """
    return DISTRIBUTIONS.copy()


def sample_toolsets_from_distribution(distribution_name: str) -> List[str]:
    """
    Sample toolsets based on a distribution's probabilities.
    
    Each toolset in the distribution has a % chance of being included.
    This allows multiple toolsets to be active simultaneously.
    
    Args:
        distribution_name (str): Name of the distribution to sample from
        
    Returns:
        List[str]: List of sampled toolset names
        
    Raises:
        ValueError: If distribution name is not found
    """
    dist = get_distribution(distribution_name)
    if not dist:
        raise ValueError(f"Unknown distribution: {distribution_name}")
    
    # Sample each toolset independently based on its probability
    selected_toolsets = []
    
    for toolset_name, probability in dist["toolsets"].items():
        # Validate toolset exists
        if not validate_toolset(toolset_name):
            print(f"⚠️  Warning: Toolset '{toolset_name}' in distribution '{distribution_name}' is not valid")
            continue
        
        # Roll the dice - if random value is less than probability, include this toolset
        if random.random() * 100 < probability:
            selected_toolsets.append(toolset_name)
    
    # If no toolsets were selected (can happen with low probabilities), 
    # ensure at least one toolset is selected by picking the highest probability one
    if not selected_toolsets and dist["toolsets"]:
        # Find toolset with highest probability
        highest_prob_toolset = max(dist["toolsets"].items(), key=lambda x: x[1])[0]
        if validate_toolset(highest_prob_toolset):
            selected_toolsets.append(highest_prob_toolset)
    
    return selected_toolsets


def validate_distribution(distribution_name: str) -> bool:
    """
    Check if a distribution name is valid.
    
    Args:
        distribution_name (str): Distribution name to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    return distribution_name in DISTRIBUTIONS


def print_distribution_info(distribution_name: str) -> None:
    """
    Print detailed information about a distribution.
    
    Args:
        distribution_name (str): Distribution name
    """
    dist = get_distribution(distribution_name)
    if not dist:
        print(f"❌ Unknown distribution: {distribution_name}")
        return
    
    print(f"\n📊 Distribution: {distribution_name}")
    print(f"   Description: {dist['description']}")
    print("   Toolsets:")
    for toolset, prob in sorted(dist["toolsets"].items(), key=lambda x: x[1], reverse=True):
        print(f"     • {toolset:15} : {prob:3}% chance")


if __name__ == "__main__":
    """
    Demo and testing of the distributions system
    """
    print("📊 Toolset Distributions Demo")
    print("=" * 60)
    
    # List all distributions
    print("\n📋 Available Distributions:")
    print("-" * 40)
    for name, dist in list_distributions().items():
        print(f"\n  {name}:")
        print(f"    {dist['description']}")
        toolset_list = ", ".join([f"{ts}({p}%)" for ts, p in dist["toolsets"].items()])
        print(f"    Toolsets: {toolset_list}")
    
    # Demo sampling
    print("\n\n🎲 Sampling Examples:")
    print("-" * 40)
    
    test_distributions = ["development", "research", "balanced", "default"]
    
    for dist_name in test_distributions:
        print(f"\n{dist_name}:")
        # Sample 5 times to show variability
        samples = []
        for _ in range(5):
            sampled = sample_toolsets_from_distribution(dist_name)
            samples.append(sorted(sampled))
        
        print(f"  Sample 1: {samples[0]}")
        print(f"  Sample 2: {samples[1]}")
        print(f"  Sample 3: {samples[2]}")
        print(f"  Sample 4: {samples[3]}")
        print(f"  Sample 5: {samples[4]}")
    
    # Show detailed info
    print("\n\n📊 Detailed Distribution Info:")
    print("-" * 40)
    print_distribution_info("development")
    print_distribution_info("research")

