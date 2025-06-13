<script>
  import { onMount } from "svelte";
  import { get } from "svelte/store";
  import { Terminal } from "@xterm/xterm";
  import { FitAddon } from "@xterm/addon-fit";
  import { agentState } from "$lib/store";
  import "@xterm/xterm/css/xterm.css";

  onMount(async () => {
    const terminalBg = getComputedStyle(document.body).getPropertyValue(
      "--terminal-window-background"
    );
    const terminalFg = getComputedStyle(document.body).getPropertyValue(
      "--terminal-window-foreground"
    );

    const terminal = new Terminal({
      disableStdin: true,
      cursorBlink: true,
      convertEol: true,
      rows: 1,
      theme: {
        background: terminalBg,
        foreground: terminalFg,
        innerText: terminalFg,
        cursor: terminalFg,
        selectionForeground: terminalBg,
        selectionBackground: terminalFg
      },
    });
    const fitAddon = new FitAddon();

    terminal.loadAddon(fitAddon);
    terminal.open(document.getElementById("terminal-content"));

    fitAddon.fit();

    let prevCommand = "";
    let prevOutput = "";

    function handleState(state) {
      if (!state || !state.terminal_session) {
        terminal.reset();
        prevCommand = "";
        prevOutput = "";
        return;
      }

      const {
        command = 'echo "Waiting..."',
        output = "Waiting...",
        title = "Terminal",
      } = state.terminal_session;

      // Update title if changed
      const titleEl = document.getElementById("terminal-title");
      if (titleEl && titleEl.innerText !== title) titleEl.innerText = title;

      if (command !== prevCommand) {
        // New command: clear and write entire context
        terminal.reset();
        terminal.write(`$ ${command}\r\n\r\n${output}\r\n`);
        fitAddon.fit();
        terminal.scrollToBottom();
        prevCommand = command;
        prevOutput = output;
      } else if (output !== prevOutput) {
        // Same command, output grew: append delta
        const delta = output.startsWith(prevOutput)
          ? output.slice(prevOutput.length)
          : `\r\n${output}`; // fallback if something unexpected
        terminal.write(delta);
        fitAddon.fit();
        terminal.scrollToBottom();
        prevOutput = output;
      }
    }

    // Initial render if state already present
    handleState(get(agentState));

    // Subscribe to future updates
    agentState.subscribe(handleState);
  });
</script>

<div
  class="w-full h-full flex flex-col border-[3px] overflow-hidden rounded-xl border-window-outline"
>
  <div class="flex items-center p-2 border-b bg-terminal-window-ribbon">
    <div class="flex ml-2 mr-4 space-x-2">
      <div class="w-3 h-3 rounded-full bg-terminal-window-dots"></div>
      <div class="w-3 h-3 rounded-full bg-terminal-window-dots"></div>
      <div class="w-3 h-3 rounded-full bg-terminal-window-dots"></div>
    </div>
    <span id="terminal-title" class="text-tertiary text-sm">Terminal</span>
  </div>
  <div
    id="terminal-content"
    class="w-full h-full rounded-bl-lg bg-terminal-window-background "
  ></div>
</div>

<style>
  #terminal-content :global(.xterm) {
    padding: 10px;
  }
  #terminal-content :global(.xterm-screen) {
    width: 100% !important;

  }
  #terminal-content :global(.xterm-rows) {
    width: 100% !important;
    height: 100% !important;
    overflow-x: scroll !important;
    /* hide the scrollbar */
    scrollbar-width: none;
  }
</style>
