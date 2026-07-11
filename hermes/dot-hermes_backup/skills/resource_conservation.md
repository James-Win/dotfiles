# Context and Resource Conservation SOP

**Trigger:** Active whenever reading files, debugging systems, or analyzing logs.

## Core Rules for Token Efficiency:
1. **Never read full logs:** You are strictly forbidden from using `cat` or `read` on system logs, firewall logs, or massive configuration files. You must use the `tail_log` tool to read only the most recent entries.
2. **Use Grep:** If searching for a specific error (e.g., a MAC address or IP block), use terminal tools to `grep` the exact line rather than loading the file into your context.
3. **Summarize and Flush:** If you are working on a multi-step debugging process that spans more than 4 tool calls, write a brief 2-sentence summary of your findings to a local `scratchpad.md` file. Do not rely on your conversation history to remember complex network states.
4. **Sub-agent Delegation:** If a task requires parsing more than 1000 lines of JSON or text, spawn a parallel sub-agent to do the reading. Have the sub-agent return only the exact extracted values to the main thread.
