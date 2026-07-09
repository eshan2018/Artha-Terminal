"""Per-tab render functions for Nivesh Terminal's market dashboard.

Each tab module exposes a render() function. This __init__.py re-exports
them with clearer names so dashboard.py can import them all from one place.
"""
# Import each tab's render function and give it a descriptive alias
from shared.tabs.tab_overview  import render as render_overview   # Tab 0: Market Overview
from shared.tabs.tab_builder   import render as render_builder    # Tab 1: Portfolio Builder
from shared.tabs.tab_search    import render as render_search     # Tab 2: Search & Recommend
from shared.tabs.tab_heatmap   import render as render_heatmap    # Tab 3: Performance Heatmap
from shared.tabs.tab_charts    import render as render_charts     # Tab 4: Price History
from shared.tabs.tab_risk      import render as render_risk       # Tab 5: Risk vs Return
from shared.tabs.tab_glossary  import render as render_glossary   # Tab 6: Glossary

# List of public names — controls what "from shared.tabs import *" exports
__all__ = [
    "render_overview",
    "render_builder",
    "render_search",
    "render_heatmap",
    "render_charts",
    "render_risk",
    "render_glossary",
]
