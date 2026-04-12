"""Quick test to verify new tools are importable and registered."""

import sys
import asyncio


async def main():
    """Test tool imports and registration."""
    try:
        # Test imports
        print("Testing imports...")
        from openhands.tools.search_academic import SearchAcademicTool, SearchAction, SearchObservation
        from openhands.tools.web_browser_academic import WebBrowserAcademicTool, WebBrowserAction, WebBrowserObservation

        print("✓ Imports successful")

        # Test tool names
        assert SearchAcademicTool.name == "search_academic"
        assert WebBrowserAcademicTool.name == "web_browser_academic"
        print("✓ Tool names correct")

        # Test action/observation creation
        search_action = SearchAction(query="machine learning", engines=["scholar"])
        print(f"✓ SearchAction created: {search_action.query}")

        web_action = WebBrowserAction(urls=["https://example.com"])
        print(f"✓ WebBrowserAction created with {len(web_action.urls)} URL(s)")

        # Test tool registration
        from openhands.sdk.tool.registry import tool_registry

        assert "search_academic" in tool_registry.tools
        assert "web_browser_academic" in tool_registry.tools
        print("✓ Tools registered in SDK registry")

        print("\n✅ All tests passed!")
        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
