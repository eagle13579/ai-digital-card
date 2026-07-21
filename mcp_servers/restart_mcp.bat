@echo off
echo Restarting MCP servers...
echo 1. Restart analytics MCP server...
echo    (MCP servers are managed by Hermes - run `hermes mcp restart` in terminal)
echo.
echo Or manually:
echo   hermes mcp remove analytics
echo   hermes mcp add analytics --command "python D:\AI数智名片\mcp_servers\analytics_mcp_server.py"
echo.
echo Connections fix applied to db_mcp_server.py:
echo   Changed: WHERE status = 'approved' --> WHERE status = 'accepted'
echo   This fix takes effect after MCP server restart.
