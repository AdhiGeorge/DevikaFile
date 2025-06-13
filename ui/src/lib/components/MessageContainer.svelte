<script>
  import { messages } from "$lib/store";
  import { afterUpdate } from "svelte";
  import { marked } from "marked";
  import DOMPurify from "dompurify";

  let messageContainer;
  let previousMessageCount = 0;
  
  afterUpdate(() => {
  if ($messages && $messages.length > 0) {
    messageContainer.scrollTo({
      top: messageContainer.scrollHeight,
      behavior: "smooth"
    });
  }
});

  /**
   * Safely parse a JSON string. Returns null if parsing fails.
   */
  function parseMessage(msg) {
    try {
      return JSON.parse(msg);
    } catch (e) {
      return null;
    }
  }

  /**
   * Detect whether a string key is purely numeric (e.g. "1", "2", ...).
   */
  function isNumeric(str) {
    return /^[0-9]+$/.test(str);
  }

  /**
   * Convert Markdown to safe HTML.
   */
  function mdToHtml(md) {
    const html = marked.parse(md);
    return DOMPurify.sanitize(html);
  }

  /**
   * Format timestamp in messages; fallback to raw string.
   */
  function formatTime(ts) {
    if (!ts) return "";
    const date = new Date(ts.replace(" ", "T"));
    return isNaN(date) ? ts : date.toLocaleTimeString();
  }

</script>

<div
  id="message-container"
  class="flex flex-col flex-1 gap-2 overflow-y-auto rounded-lg"
  bind:this={messageContainer}
>
  {#if $messages !== null}
  <div class="flex flex-col divide-y-2">
    {#each $messages as message}
      <div class="flex items-start gap-2 px-2 py-4">
        {#if message.from_agent}
          <img
            src="/assets/devika-avatar.png"
            alt="Agent's Avatar"
            class="w-8 h-8 rounded-full"
          />
        {:else}
          <img
            src="/assets/user-avatar.svg"
            alt="User's Avatar"
            class="flex-shrink-0 rounded-full avatar"
            style="width: 28px; height: 28px;"
          />
        {/if}
        <div class="flex flex-col w-full text-sm">
          <p class="text-xs text-gray-400">
            {message.from_agent ? "Agent" : "You"}
            <span class="timestamp">{formatTime(message.timestamp)}</span>
          </p>
          {#if message.from_agent && message.message.trim().startsWith("{")}
            {#await Promise.resolve(parseMessage(message.message.trim())) then parsed}
              {#if parsed?.answer}
                <!-- Render structured answer (answer/explanation/metadata) -->
                <div class="flex flex-col w-full gap-3" contenteditable="false">
                  <p><strong>Answer:</strong> {parsed.answer}</p>
                  <div class="markdown" contenteditable="false">
                    {@html mdToHtml(parsed.answer)}
                  </div>
                  {#if parsed.explanation}
                    <div class="mt-2 markdown" contenteditable="false">
                      {@html mdToHtml(parsed.explanation)}
                    </div>
                  {/if}
                  {#if parsed.metadata && Object.keys(parsed.metadata).length}
                    <details class="metadata">
                      <summary><strong>Metadata</strong></summary>
                      <pre>{JSON.stringify(parsed.metadata, null, 2)}</pre>
                    </details>
                  {/if}
                </div>
              {:else if parsed}
                <!-- Render numeric step plan -->
                <div class="flex flex-col w-full gap-5" contenteditable="false">
                  {@html `<strong>Here's my step-by-step plan:</strong>`}
                  <div class="flex flex-col gap-3">
                    {#each Object.entries(parsed) as [step, description]}
                      {#if isNumeric(step)}
                        <div class="flex items-center gap-2">
                          <input type="checkbox" id="step-{step}" disabled />
                          <label for="step-{step}" class="cursor-auto"><strong>Step {step}</strong>: {description}</label>
                        </div>
                      {/if}
                    {/each}
                  </div>
                </div>
              {/if}
            {/await}
          {:else}
            <!-- Non-JSON message: render markdown/html or link handling -->
            {#if /https?:\/\/[^\s]+/.test(message.message)}
              <div class="w-full cursor-auto" contenteditable="false">
                {@html message.message.replace(
                  /(https?:\/\/[^\s]+)/g,
                  '<u><a href="$1" target="_blank" style="font-weight: bold;">$1</a></u>'
                )}
              </div>
            {:else}
              <div class="w-full markdown" contenteditable="false">
                {@html mdToHtml(message.message)}
              </div>
            {/if}
          {/if}
        </div>
      </div>
    {/each}
  </div>
  {/if}
</div>

<style>
  .timestamp {
    margin-left: 8px;
    font-size: smaller;
    color: #aaa;
  }
  #message-container {
    scrollbar-width: none;
  }

  input[type="checkbox"] {
    appearance: none;
    -webkit-appearance: none;
    -moz-appearance: none;
    -ms-appearance: none;
    -o-appearance: none;
    width: 12px;
    height: 12px;
    border: 2px solid black;
    border-radius: 4px;
  }

  .markdown :global(pre) {
    background-color: #f6f8fa;
    padding: 0.75rem;
    border-radius: 6px;
    overflow-x: auto;
  }
  .markdown :global(code) {
    background-color: #f6f8fa;
    padding: 2px 4px;
    border-radius: 4px;
  }
  .markdown :global(h1) {
    font-size: 1.25rem;
    font-weight: 600;
    margin: 0.5rem 0;
  }
  .markdown :global(h2) {
    font-size: 1.125rem;
    font-weight: 600;
    margin: 0.5rem 0;
  }
</style>
