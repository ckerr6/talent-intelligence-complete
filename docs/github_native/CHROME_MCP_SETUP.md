# Chrome DevTools MCP Integration

## What It Does

The Chrome DevTools MCP server allows AI agents (like Cursor/Claude) to:
- Navigate to URLs and interact with web pages
- Take screenshots of pages
- Read console messages (errors, warnings, logs)
- Monitor network requests
- Debug JavaScript issues in real-time
- Profile performance

This is incredibly useful for debugging frontend issues without needing manual browser DevTools inspection.

## Setup

### 1. Configuration Added

Added to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": [
        "chrome-devtools-mcp@latest",
        "--headless=false"
      ]
    }
  }
}
```

### 2. Restart Required

**IMPORTANT**: You must restart Claude Desktop for the MCP server to load.

1. Quit Claude Desktop completely (Cmd+Q)
2. Reopen Claude Desktop
3. The Chrome DevTools MCP server will automatically start

### 3. Verify Connection

After restarting, you should see the Chrome DevTools MCP server available in the MCP tools list.

## Usage Examples

### Check Console Errors
```
Navigate to http://localhost:3001/github and check for any console errors
```

### Take Screenshot
```
Take a screenshot of http://localhost:3001/github
```

### Monitor Network Requests
```
Navigate to http://localhost:3001/github and list all network requests that failed
```

### Debug Blank Page
```
Navigate to http://localhost:3001/github, take a screenshot, and check console messages to debug why the page is blank
```

## Available Tools

- `navigate_to` - Go to a URL
- `list_console_messages` - See console output (errors, warnings, logs)
- `get_console_message` - Get details of a specific console message
- `take_screenshot` - Capture visual state
- `take_snapshot` - Get DOM snapshot
- `evaluate_script` - Run JavaScript in the page
- `list_network_requests` - See all HTTP requests
- `get_network_request` - Get details of a specific request

## References

- GitHub: https://github.com/ChromeDevTools/chrome-devtools-mcp
- NPM: https://www.npmjs.com/package/chrome-devtools-mcp



