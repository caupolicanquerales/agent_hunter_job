import { CommonModule } from '@angular/common';
import { Component, computed, input, model, signal } from '@angular/core';

@Component({
  selector: 'app-raw-payload-viewer',
  imports: [CommonModule],
  templateUrl: './raw-payload-viewer.html',
  styleUrl: './raw-payload-viewer.scss',
})
export class RawPayloadViewer {
  public readonly payload = input<any>(null);
  public readonly isOpen = model<boolean>(false);
  protected readonly copied = signal<boolean>(false);

  // Formatted stringified JSON
  protected readonly formattedJson = computed(() => {
    const data = this.payload();
    if (data === null || data === undefined) {
      return '{}';
    }
    try {
      return JSON.stringify(data, null, 2);
    } catch {
      return String(data);
    }
  });

  // Calculate approximate payload byte size
  protected readonly payloadSizeKb = computed(() => {
    const str = this.formattedJson();
    const bytes = new Blob([str]).size;
    return (bytes / 1024).toFixed(1);
  });

  // Count top-level keys
  protected readonly keyCount = computed(() => {
    const data = this.payload();
    if (data && typeof data === 'object') {
      return Object.keys(data).length;
    }
    return 0;
  });

  // Syntax-highlighted HTML string for JSON code block
  protected readonly highlightedJsonHtml = computed(() => {
    const jsonStr = this.formattedJson();
    return this.syntaxHighlight(jsonStr);
  });

  public openAccordion(): void {
    this.isOpen.set(true);
  }

  public toggleAccordion(): void {
    this.isOpen.update((v) => !v);
  }

  protected onDetailsToggle(event: Event): void {
    const details = event.target as HTMLDetailsElement;
    this.isOpen.set(details.open);
  }

  protected copyToClipboard(): void {
    const text = this.formattedJson();
    navigator.clipboard.writeText(text).then(() => {
      this.copied.set(true);
      setTimeout(() => this.copied.set(false), 2000);
    });
  }

  private syntaxHighlight(json: string): string {
    // Escape standard HTML entities
    let escaped = json
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');

    // Regex syntax match
    return escaped.replace(
      /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g,
      (match) => {
        let cls = 'json-number';
        if (/^"/.test(match)) {
          if (/:$/.test(match)) {
            cls = 'json-key';
          } else {
            cls = 'json-string';
          }
        } else if (/true|false/.test(match)) {
          cls = 'json-boolean';
        } else if (/null/.test(match)) {
          cls = 'json-null';
        }
        return `<span class="${cls}">${match}</span>`;
      }
    );
  }
}

