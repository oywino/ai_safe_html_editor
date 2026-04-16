#!/usr/bin/env python3
"""
AI-Safe HTML Editor for Windows 11

Single-file Python desktop app with two synchronized modes:

1. Safe Structure Mode
   - Preservation-oriented body editor.
   - Unknown/custom tags are shown as visible structured blocks.
   - Better for maintaining AI-oriented tag structure.

2. True WYSIWYG Mode
   - Renders and edits the actual HTML document in a Microsoft WebView2-backed
     window when pywebview uses the Edge backend on Windows.
   - Better for visual editing.

Requirements:
    pip install pywebview

Run:
    python ai_safe_html_editor.py
    python ai_safe_html_editor.py path\to\file.html
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import webview


APP_WINDOW = None


APP_HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI-Safe HTML Editor</title>
  <style>
    :root {
      --bg: #eef1f5;
      --panel: #ffffff;
      --line: #d5dbe3;
      --text: #1f2328;
      --muted: #5a6470;
      --hover: #f1f6ff;
      --accent: #2b6cb0;
      --accent-soft: #eaf3ff;
      --safe-bg: #f8fbff;
      --safe-line: #7aa7d9;
      --danger: #b42318;
      --menu-shadow: 0 12px 28px rgba(0, 0, 0, 0.18);
      --radius: 10px;
      --button-radius: 8px;
      --font-ui: "Segoe UI", Arial, sans-serif;
      --font-mono: Consolas, "Courier New", monospace;
    }

    * { box-sizing: border-box; }

    html, body {
      margin: 0;
      height: 100%;
      background: var(--bg);
      color: var(--text);
      font-family: var(--font-ui);
      overflow: hidden;
    }

    body {
      display: grid;
      grid-template-rows: auto auto 1fr auto;
    }

    #toolbar {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 12px 14px;
      border-bottom: 1px solid var(--line);
      background: #ffffff;
    }

    .toolbar-group {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .toolbar-separator {
      width: 1px;
      align-self: stretch;
      background: var(--line);
      margin: 0 4px;
    }

    button {
      appearance: none;
      border: 1px solid #c7d1dc;
      background: #ffffff;
      color: var(--text);
      padding: 8px 12px;
      border-radius: var(--button-radius);
      font: 13px var(--font-ui);
      cursor: default;
    }

    button:hover { background: #f7f9fb; }
    button:active { background: #eef3f8; }
    button.primary {
      border-color: #95b8e1;
      background: var(--accent-soft);
      color: #184f84;
    }

    #modebar {
      display: flex;
      align-items: center;
      gap: 0;
      padding: 10px 14px 0 14px;
      background: var(--bg);
    }

    .mode-tab {
      border: 1px solid var(--line);
      border-bottom: none;
      background: #f4f6f8;
      border-radius: 10px 10px 0 0;
      padding: 10px 16px;
      margin-right: 6px;
      font: 13px var(--font-ui);
      color: var(--muted);
    }

    .mode-tab.active {
      background: #ffffff;
      color: var(--text);
      position: relative;
      top: 1px;
    }

    #workspace {
      padding: 0 14px 14px 14px;
      min-height: 0;
    }

    .panel {
      display: none;
      height: 100%;
      background: #ffffff;
      border: 1px solid var(--line);
      border-radius: 0 12px 12px 12px;
      overflow: hidden;
      min-height: 0;
    }

    .panel.active { display: flex; }

    .panel-inner {
      display: flex;
      flex-direction: column;
      width: 100%;
      min-height: 0;
    }

    .panel-note {
      padding: 10px 14px;
      font-size: 13px;
      color: var(--muted);
      border-bottom: 1px solid var(--line);
      background: #fafbfc;
    }

    #safe-scroll {
      flex: 1 1 auto;
      overflow: auto;
      padding: 18px;
      background: #f5f7fa;
    }

    #safe-editor {
      max-width: 1150px;
      margin: 0 auto;
      min-height: 100%;
      background: #ffffff;
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 22px 26px;
      outline: none;
      box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
    }

    #safe-editor :focus { outline: none; }

    #safe-editor[contenteditable="false"] {
      cursor: default;
      user-select: text;
    }

    #visual-shell {
      flex: 1 1 auto;
      min-height: 0;
      background: #f0f3f6;
      padding: 14px;
    }

    #visual-frame {
      width: 100%;
      height: 100%;
      border: 1px solid var(--line);
      border-radius: 12px;
      background: #ffffff;
    }

    .ai-tag-block {
      border: 1px solid var(--safe-line);
      background: var(--safe-bg);
      border-radius: 10px;
      margin: 12px 0;
      overflow: hidden;
      box-shadow: 0 0 0 1px rgba(122, 167, 217, 0.08) inset;
    }

    .ai-tag-header,
    .ai-tag-footer {
      padding: 8px 10px;
      background: rgba(122, 167, 217, 0.16);
      color: #174a7c;
      font: 12px var(--font-mono);
      user-select: none;
      white-space: pre-wrap;
    }

    .ai-tag-content {
      min-height: 1.2em;
      padding: 10px 12px;
      outline: none;
    }

    .comment-node {
      display: inline-block;
      padding: 2px 4px;
      margin: 1px 0;
      border: 1px dashed #c2c8d0;
      border-radius: 4px;
      background: #f3f4f6;
      color: #5f6772;
      font: 12px var(--font-mono);
      user-select: none;
    }

    blockquote {
      border-left: 4px solid #d0d7de;
      margin-left: 0;
      padding-left: 12px;
      color: #454b52;
    }

    table { border-collapse: collapse; }
    td, th {
      border: 1px solid #d0d7de;
      padding: 6px 8px;
    }

    pre, code { font-family: var(--font-mono); }

    pre {
      overflow: auto;
      background: #f6f8fa;
      padding: 12px;
      border: 1px solid #d8dee4;
      border-radius: 8px;
    }

    #statusbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 9px 14px;
      border-top: 1px solid var(--line);
      background: #ffffff;
      color: var(--muted);
      font-size: 12px;
    }

    #status-left, #status-right {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .context-menu {
      position: fixed;
      z-index: 2147483647;
      display: none;
      min-width: 220px;
      padding: 4px 0;
      background: #ffffff;
      border: 1px solid #d7dce2;
      border-radius: 8px;
      box-shadow: var(--menu-shadow);
      font: 13px var(--font-ui);
      color: var(--text);
      user-select: none;
    }

    .context-menu.open { display: block; }

    .menu-item {
      padding: 7px 14px;
      white-space: nowrap;
      cursor: default;
    }

    .menu-item:hover {
      background: var(--hover);
      outline: 1px solid #d3e4ff;
      outline-offset: -1px;
    }

    .menu-item[aria-disabled="true"] {
      color: #8a9199;
      pointer-events: none;
    }

    .menu-separator {
      height: 1px;
      margin: 4px 0;
      background: #e7eaef;
    }

    .hidden { display: none !important; }
  </style>
</head>
<body>
  <div id="toolbar">
    <div class="toolbar-group">
      <button id="open-btn">Open…</button>
      <button id="save-btn" class="primary">Save</button>
      <button id="save-as-btn">Save As…</button>
    </div>
    <div class="toolbar-separator"></div>
    <div class="toolbar-group">
      <button id="safe-tab-top">Safe Structure Mode</button>
      <button id="visual-tab-top">True WYSIWYG Mode</button>
    </div>
  </div>

  <div id="modebar">
    <button id="safe-tab" class="mode-tab active">Safe Structure Mode</button>
    <button id="visual-tab" class="mode-tab">True WYSIWYG Mode</button>
  </div>

  <div id="workspace">
    <section id="safe-panel" class="panel active">
      <div class="panel-inner">
        <div class="panel-note">
          Safe Structure Mode shows a generated structure view for the current document body.
          This mode is read-only and is intended for AI-facing prompt inspection.
        </div>
        <div id="safe-scroll">
          <div id="safe-editor" contenteditable="false" spellcheck="false"></div>
        </div>
      </div>
    </section>

    <section id="visual-panel" class="panel">
      <div class="panel-inner">
        <div class="panel-note">
          True WYSIWYG Mode edits the actual rendered HTML document in-place.
          This mode may normalize markup while preserving visual formatting.
        </div>
        <div id="visual-shell">
          <iframe id="visual-frame" title="True WYSIWYG editor"></iframe>
        </div>
      </div>
    </section>
  </div>

  <div id="statusbar">
    <div id="status-left">Ready.</div>
    <div id="status-right">No file loaded.</div>
  </div>

  <div id="context-menu" class="context-menu" role="menu" aria-hidden="true"></div>

  <script>
    (() => {
      const STANDARD_HTML_TAGS = new Set([
        'a','abbr','address','area','article','aside','audio','b','base','bdi','bdo','blockquote','body','br',
        'button','canvas','caption','cite','code','col','colgroup','data','datalist','dd','del','details','dfn',
        'dialog','div','dl','dt','em','embed','fieldset','figcaption','figure','footer','form','h1','h2','h3',
        'h4','h5','h6','head','header','hr','html','i','iframe','img','input','ins','kbd','label','legend','li',
        'link','main','map','mark','menu','meta','meter','nav','noscript','object','ol','optgroup','option','output',
        'p','picture','pre','progress','q','rp','rt','ruby','s','samp','script','section','select','slot','small',
        'source','span','strong','style','sub','summary','sup','table','tbody','td','template','textarea','tfoot',
        'th','thead','time','title','tr','track','u','ul','var','video','wbr'
      ]);

      const VOID_HTML_TAGS = new Set([
        'area','base','br','col','embed','hr','img','input','link','meta','source','track','wbr'
      ]);

      const state = {
        currentMode: 'safe',
        currentPath: null,
        currentDocumentHtml: '',
        dirty: false,
        visualReady: false,
        lastVisualLoadToken: 0,
        startupComplete: false,
        pendingXmlTag: null,
      };

      const els = {
        openBtn: document.getElementById('open-btn'),
        saveBtn: document.getElementById('save-btn'),
        saveAsBtn: document.getElementById('save-as-btn'),
        safeTab: document.getElementById('safe-tab'),
        visualTab: document.getElementById('visual-tab'),
        safeTabTop: document.getElementById('safe-tab-top'),
        visualTabTop: document.getElementById('visual-tab-top'),
        safePanel: document.getElementById('safe-panel'),
        visualPanel: document.getElementById('visual-panel'),
        safeEditor: document.getElementById('safe-editor'),
        safeScroll: document.getElementById('safe-scroll'),
        frame: document.getElementById('visual-frame'),
        statusLeft: document.getElementById('status-left'),
        statusRight: document.getElementById('status-right'),
        contextMenu: document.getElementById('context-menu'),
      };

      const contextMenu = {
        open: false,
        target: null,
      };

      let safeSavedRange = null;
      let frameContextHandlersInstalled = false;

      function escapeHtml(text) {
        return String(text)
          .replace(/&/g, '&amp;')
          .replace(/</g, '&lt;')
          .replace(/>/g, '&gt;');
      }

      function escapeAttribute(text) {
        return escapeHtml(text).replace(/"/g, '&quot;');
      }

      function splitDoctype(fullHtml) {
        const match = /^\s*(<!doctype[^>]*>)\s*/i.exec(fullHtml || '');
        if (!match) {
          return { doctype: '<!DOCTYPE html>', rest: fullHtml || '' };
        }
        return { doctype: match[1], rest: fullHtml.slice(match[0].length) };
      }

      function doctypeToString(doc) {
        const dt = doc.doctype;
        if (!dt) {
          return '<!DOCTYPE html>';
        }
        let result = '<!DOCTYPE ' + dt.name;
        if (dt.publicId) {
          result += ' PUBLIC "' + dt.publicId + '"';
        }
        if (dt.systemId) {
          if (!dt.publicId) {
            result += ' SYSTEM';
          }
          result += ' "' + dt.systemId + '"';
        }
        result += '>';
        return result;
      }

      function parseHtmlDocument(fullHtml) {
        const parser = new DOMParser();
        return parser.parseFromString(fullHtml || blankDocumentHtml(), 'text/html');
      }

      function serializeHtmlDocument(doc, preferredDoctype) {
        const doctype = preferredDoctype || doctypeToString(doc);
        return doctype + '\n' + serializeNode(doc.documentElement, 0);
      }

      function serializeNode(node, indent) {
        const indentText = ' '.repeat(indent || 0);

        if (node.nodeType === Node.COMMENT_NODE) {
          return indentText + '<!--' + (node.nodeValue || '') + '-->\n';
        }

        if (node.nodeType === Node.TEXT_NODE) {
          const text = node.nodeValue || '';
          if (!text.trim()) {
            return '';
          }
          return indentText + escapeHtml(text) + '\n';
        }

        if (node.nodeType !== Node.ELEMENT_NODE) {
          return '';
        }

        const tag = node.tagName.toLowerCase();
        const attrs = Array.from(node.attributes)
          .map((attr) => `${attr.name}="${escapeAttribute(attr.value)}"`)
          .join(' ');
        const attrText = attrs ? ' ' + attrs : '';
        const opening = `<${tag}${attrText}>`;
        const closing = VOID_HTML_TAGS.has(tag) ? '' : `</${tag}>`;

        const childHtml = Array.from(node.childNodes)
          .map((child) => serializeNode(child, indent + 2))
          .join('');

        if (VOID_HTML_TAGS.has(tag)) {
          return indentText + opening + '\n';
        }

        if (!childHtml.trim()) {
          return indentText + opening + closing + '\n';
        }

        if (node.childNodes.length === 1 && node.childNodes[0].nodeType === Node.TEXT_NODE) {
          const text = node.childNodes[0].nodeValue || '';
          if (!text.includes('\n')) {
            return indentText + opening + escapeHtml(text) + closing + '\n';
          }
        }

        return indentText + opening + '\n' + childHtml + indentText + closing + '\n';
      }

      function blankDocumentHtml() {
        return [
          '<!DOCTYPE html>',
          '<html lang="en">',
          '<head>',
          '  <meta charset="utf-8">',
          '  <meta name="viewport" content="width=device-width, initial-scale=1">',
          '  <title>Untitled document</title>',
          '</head>',
          '<body>',
          '  <p><br></p>',
          '</body>',
          '</html>'
        ].join('\n');
      }

      function ensureFullHtml(fullHtml) {
        const trimmed = (fullHtml || '').trim();
        if (!trimmed) {
          return blankDocumentHtml();
        }
        if (/<!doctype|<html[\s>]/i.test(trimmed)) {
          return fullHtml;
        }
        return [
          '<!DOCTYPE html>',
          '<html lang="en">',
          '<head>',
          '  <meta charset="utf-8">',
          '  <meta name="viewport" content="width=device-width, initial-scale=1">',
          '  <title>Imported body</title>',
          '</head>',
          '<body>',
          fullHtml,
          '</body>',
          '</html>'
        ].join('\n');
      }

      function extractBodyHtml(fullHtml) {
        const doc = parseHtmlDocument(ensureFullHtml(fullHtml));
        return doc.body ? doc.body.innerHTML : '';
      }

      function mergeBodyIntoFullHtml(fullHtml, bodyHtml) {
        const normalized = ensureFullHtml(fullHtml);
        const parts = splitDoctype(normalized);
        const doc = parseHtmlDocument(normalized);
        if (!doc.body) {
          const body = doc.createElement('body');
          doc.documentElement.appendChild(body);
        }
        doc.body.innerHTML = bodyHtml && bodyHtml.trim() ? bodyHtml : '<p><br></p>';
        return serializeHtmlDocument(doc, parts.doctype);
      }

      function updateWindowTitle() {
        const name = state.currentPath ? state.currentPath.split(/[\\/]/).pop() : 'Untitled.html';
        document.title = (state.dirty ? '* ' : '') + name + ' — AI-Safe HTML Editor';
      }

      function setStatus(left, right) {
        if (typeof left === 'string') {
          els.statusLeft.textContent = left;
        }
        if (typeof right === 'string') {
          els.statusRight.textContent = right;
        }
      }

      function setDirty(flag) {
        state.dirty = !!flag;
        updateWindowTitle();
        const label = state.currentPath || 'No file loaded.';
        setStatus(state.dirty ? 'Modified.' : 'Saved.', label);
      }

      function isStandardTag(tagName) {
        return STANDARD_HTML_TAGS.has(String(tagName || '').toLowerCase());
      }

      function attributesObject(el) {
        const attrs = {};
        for (const attr of el.attributes) {
          attrs[attr.name] = attr.value;
        }
        return attrs;
      }

      function attrsToDisplay(attrs) {
        const entries = Object.entries(attrs);
        if (!entries.length) {
          return '';
        }
        return ' ' + entries
          .map(([key, value]) => `${key}="${String(value).replace(/"/g, '&quot;')}"`)
          .join(' ');
      }

      function attrsToSerializedString(attrs) {
        const entries = Object.entries(attrs);
        if (!entries.length) {
          return '';
        }
        return ' ' + entries
          .map(([key, value]) => `${key}="${escapeAttribute(value)}"`)
          .join(' ');
      }

      function safeNodeToEditable(node) {
        if (node.nodeType === Node.TEXT_NODE) {
          return document.createTextNode(node.nodeValue);
        }

        if (node.nodeType === Node.COMMENT_NODE) {
          const span = document.createElement('span');
          span.className = 'comment-node';
          span.contentEditable = 'false';
          span.dataset.comment = node.nodeValue;
          span.textContent = `<!--${node.nodeValue}-->`;
          return span;
        }

        if (node.nodeType !== Node.ELEMENT_NODE) {
          return document.createTextNode('');
        }

        const tag = node.tagName.toLowerCase();

        if (isStandardTag(tag)) {
          const clone = document.createElement(tag);
          for (const attr of node.attributes) {
            clone.setAttribute(attr.name, attr.value);
          }
          for (const child of Array.from(node.childNodes)) {
            clone.appendChild(safeNodeToEditable(child));
          }
          return clone;
        }

        const wrapper = document.createElement('div');
        wrapper.className = 'ai-tag-block';
        wrapper.contentEditable = 'false';
        wrapper.dataset.aiTag = tag;
        wrapper.dataset.aiAttrs = JSON.stringify(attributesObject(node));

        const header = document.createElement('div');
        header.className = 'ai-tag-header';
        header.contentEditable = 'false';
        header.innerHTML = `&lt;${tag}${attrsToDisplay(attributesObject(node))}&gt;`;

        const content = document.createElement('div');
        content.className = 'ai-tag-content';
        content.contentEditable = 'true';

        for (const child of Array.from(node.childNodes)) {
          content.appendChild(safeNodeToEditable(child));
        }

        const footer = document.createElement('div');
        footer.className = 'ai-tag-footer';
        footer.contentEditable = 'false';
        footer.innerHTML = `&lt;/${tag}&gt;`;

        wrapper.appendChild(header);
        wrapper.appendChild(content);
        wrapper.appendChild(footer);
        return wrapper;
      }

      function serializeSafeNode(node) {
        if (node.nodeType === Node.TEXT_NODE) {
          return escapeHtml(node.nodeValue || '');
        }

        if (node.nodeType !== Node.ELEMENT_NODE) {
          return '';
        }

        if (node.classList && node.classList.contains('comment-node')) {
          return `<!--${node.dataset.comment || ''}-->`;
        }

        if (node.classList && node.classList.contains('ai-tag-block')) {
          const tag = node.dataset.aiTag;
          let attrs = {};
          try {
            attrs = JSON.parse(node.dataset.aiAttrs || '{}');
          } catch (error) {
            attrs = {};
          }
          const content = node.querySelector(':scope > .ai-tag-content');
          const inner = content ? Array.from(content.childNodes).map(serializeSafeNode).join('') : '';
          return `<${tag}${attrsToSerializedString(attrs)}>${inner}</${tag}>`;
        }

        const tag = node.tagName.toLowerCase();
        const attrs = [];
        for (const attr of Array.from(node.attributes)) {
          attrs.push(`${attr.name}="${escapeAttribute(attr.value)}"`);
        }
        const attrText = attrs.length ? ' ' + attrs.join(' ') : '';

        if (VOID_HTML_TAGS.has(tag)) {
          return `<${tag}${attrText}>`;
        }

        const inner = Array.from(node.childNodes).map(serializeSafeNode).join('');
        return `<${tag}${attrText}>${inner}</${tag}>`;
      }

      function normalizeSafeRoot() {
        if (!els.safeEditor.innerHTML.trim()) {
          const p = document.createElement('p');
          p.innerHTML = '<br>';
          els.safeEditor.appendChild(p);
        }
      }

      function saveSafeRange() {
        const sel = window.getSelection();
        if (sel && sel.rangeCount > 0) {
          safeSavedRange = sel.getRangeAt(0).cloneRange();
        }
      }

      function restoreSafeRange() {
        if (!safeSavedRange) {
          els.safeEditor.focus();
          return;
        }
        const sel = window.getSelection();
        sel.removeAllRanges();
        sel.addRange(safeSavedRange);
      }

      function loadSafeBodyHtml(rawBodyHtml) {
        els.safeEditor.innerHTML = '';
        const parser = new DOMParser();
        const parsed = parser.parseFromString(`<body>${rawBodyHtml || ''}</body>`, 'text/html');
        for (const child of Array.from(parsed.body.childNodes)) {
          els.safeEditor.appendChild(safeNodeToEditable(child));
        }
        normalizeSafeRoot();
      }

      function getSafeBodyHtml() {
        return Array.from(els.safeEditor.childNodes).map(serializeSafeNode).join('');
      }

      function safeExecCommand(commandName, value = null) {
        restoreSafeRange();
        els.safeEditor.focus();
        document.execCommand(commandName, false, value);
        saveSafeRange();
        setDirty(true);
      }

      function safeFormatBlock(tagName) {
        safeExecCommand('formatBlock', `<${tagName}>`);
      }

      function promptForXmlTag() {
        const name = window.prompt('Enter XML tag name (letters, digits, hyphen, underscore, dot):', 'new_tag');
        if (!name) {
          return null;
        }
        const trimmed = String(name).trim();
        if (!/^[A-Za-z_][A-Za-z0-9_\-\.]*$/.test(trimmed)) {
          window.alert('Invalid XML tag name. Use letters, digits, hyphen, underscore, or dot, and do not start with a digit.');
          return null;
        }
        return trimmed;
      }

      function createPendingXmlOpenMarker(doc, tagName, depth) {
        const section = doc.createElement('section');
        section.className = `node pending-open level-${Math.min(depth, 6)}`;
        section.dataset.tag = tagName;

        const openRow = doc.createElement('div');
        openRow.className = 'tag-row';
        const openName = doc.createElement('span');
        openName.className = 'tag-name';
        openName.textContent = `<${tagName}>`;
        openRow.appendChild(openName);

        const hint = doc.createElement('div');
        hint.className = 'children';
        const textHint = doc.createElement('div');
        textHint.className = 'text intro';
        textHint.textContent = 'Opening tag inserted. Place the cursor where the closing tag should be and choose Close XML Tag.';
        hint.appendChild(textHint);

        section.appendChild(openRow);
        section.appendChild(hint);
        return section;
      }

      function isRangeAfterNode(range, node) {
        const position = node.compareDocumentPosition(range.startContainer);
        return (position & Node.DOCUMENT_POSITION_FOLLOWING) !== 0;
      }

      function getPendingOpenMarker(doc) {
        return doc.querySelector('section.pending-open[data-tag]');
      }

      function getVisualInsertDepth(range, doc) {
        let node = range.commonAncestorContainer;
        if (node.nodeType !== Node.ELEMENT_NODE) {
          node = node.parentElement;
        }
        while (node && node !== doc.body) {
          if (node.classList && node.classList.contains('node')) {
            const match = node.className.match(/level-(\d+)/);
            const depth = match ? parseInt(match[1], 10) : 0;
            return Math.min(depth + 1, 6);
          }
          node = node.parentElement;
        }
        return 0;
      }

      function createXmlTagBlock(doc, tagName, contents, depth) {
        const section = doc.createElement('section');
        section.className = 'node';
        section.dataset.tag = tagName;

        section.classList.add(`level-${Math.min(depth, 6)}`);

        const openRow = doc.createElement('div');
        openRow.className = 'tag-row';
        const openName = doc.createElement('span');
        openName.className = 'tag-name';
        openName.textContent = `<${tagName}>`;
        openRow.appendChild(openName);

        const children = doc.createElement('div');
        children.className = 'children';

        const textBlock = doc.createElement('div');
        textBlock.className = 'text';
        textBlock.contentEditable = 'true';

        if (contents && contents.hasChildNodes()) {
          const containsNestedNodes = Array.from(contents.childNodes).some((node) => node.nodeType === Node.ELEMENT_NODE && node.classList.contains('node'));
          if (containsNestedNodes) {
            children.appendChild(contents);
          } else {
            if (!contents.textContent.trim()) {
              textBlock.innerHTML = '<br>';
            } else {
              textBlock.appendChild(contents);
            }
            children.appendChild(textBlock);
          }
        } else {
          textBlock.innerHTML = '<br>';
          children.appendChild(textBlock);
        }

        const closingRow = doc.createElement('div');
        closingRow.className = 'tag-row closing';
        const closeName = doc.createElement('span');
        closeName.className = 'tag-name';
        closeName.textContent = `</${tagName}>`;
        closingRow.appendChild(closeName);

        section.appendChild(openRow);
        section.appendChild(children);
        section.appendChild(closingRow);
        return section;
      }

      function refreshSafeStructureFromVisual() {
        const html = getVisualDocumentHtml();
        state.currentDocumentHtml = html;
        loadSafeBodyHtml(extractBodyHtml(html));
      }

      function insertXmlTagAtCursor() {
        if (state.currentMode !== 'visual') {
          switchMode('visual');
          return;
        }

        const doc = getVisualDocument();
        if (!doc) {
          return;
        }

        const selection = doc.getSelection();
        if (!selection || selection.rangeCount === 0) {
          return;
        }

        const range = selection.getRangeAt(0).cloneRange();
        if (!range.collapsed) {
          range.collapse(true);
        }

        const pending = state.pendingXmlTag;
        if (!pending) {
          const tagName = promptForXmlTag();
          if (!tagName) {
            return;
          }

          const depth = getVisualInsertDepth(range, doc);
          const marker = createPendingXmlOpenMarker(doc, tagName, depth);
          range.insertNode(marker);

          const afterRange = doc.createRange();
          afterRange.setStartAfter(marker);
          afterRange.collapse(true);
          selection.removeAllRanges();
          selection.addRange(afterRange);

          state.pendingXmlTag = { name: tagName };
          setStatus(`Pending <${tagName}>...`, state.currentPath || 'No file loaded.');
          return;
        }

        const marker = getPendingOpenMarker(doc);
        if (!marker) {
          state.pendingXmlTag = null;
          return;
        }

        if (!isRangeAfterNode(range, marker)) {
          window.alert('Place the cursor after the opening tag before closing it.');
          return;
        }

        const wrapRange = doc.createRange();
        wrapRange.setStartAfter(marker);
        wrapRange.setEnd(range.startContainer, range.startOffset);

        const contents = wrapRange.extractContents();
        const depth = getVisualInsertDepth(range, doc);
        const finalBlock = createXmlTagBlock(doc, pending.name, contents, depth);

        marker.parentNode.replaceChild(finalBlock, marker);

        state.pendingXmlTag = null;
        setDirty(true);
        refreshSafeStructureFromVisual();
      }

      function getVisualDocument() {
        try {
          return els.frame.contentDocument || els.frame.contentWindow.document;
        } catch (error) {
          return null;
        }
      }

      function installVisualDocumentHooks(doc) {
        if (!doc) {
          return;
        }

        doc.designMode = 'on';
        if (doc.body && !doc.body.innerHTML.trim()) {
          doc.body.innerHTML = '<p><br></p>';
        }

        const markDirty = () => {
          setDirty(true);
          refreshSafeStructureFromVisual();
        };
        doc.addEventListener('input', markDirty);
        doc.addEventListener('keyup', markDirty);
        doc.addEventListener('paste', () => setTimeout(markDirty, 0));
        doc.addEventListener('mouseup', () => hideContextMenu());
        doc.addEventListener('click', () => hideContextMenu());
        doc.addEventListener('scroll', () => hideContextMenu(), true);
        doc.addEventListener('contextmenu', (event) => {
          event.preventDefault();
          openContextMenu('visual', event.clientX, event.clientY);
        });
      }

      function loadVisualDocumentHtml(fullHtml) {
        return new Promise((resolve) => {
          const token = ++state.lastVisualLoadToken;
          state.visualReady = false;
          els.frame.onload = () => {
            if (token !== state.lastVisualLoadToken) {
              return;
            }
            state.visualReady = true;
            const doc = getVisualDocument();
            installVisualDocumentHooks(doc);
            resolve();
          };
          els.frame.srcdoc = ensureFullHtml(fullHtml);
        });
      }

      function getVisualDocumentHtml() {
        const doc = getVisualDocument();
        if (!doc || !doc.documentElement) {
          return state.currentDocumentHtml || blankDocumentHtml();
        }
        return serializeHtmlDocument(doc, doctypeToString(doc));
      }

      function visualExecCommand(commandName, value = null) {
        const doc = getVisualDocument();
        if (!doc) {
          return;
        }
        doc.execCommand(commandName, false, value);
        setDirty(true);
        hideContextMenu();
      }

      function visualFormatBlock(tagName) {
        visualExecCommand('formatBlock', `<${tagName}>`);
      }

      async function syncCurrentModeToMemory() {
        if (state.currentMode === 'safe') {
          return;
        }
        state.currentDocumentHtml = getVisualDocumentHtml();
      }

      async function switchMode(mode) {
        if (mode === state.currentMode) {
          return;
        }

        await syncCurrentModeToMemory();
        state.currentMode = mode;
        hideContextMenu();

        if (mode === 'safe') {
          loadSafeBodyHtml(extractBodyHtml(state.currentDocumentHtml));
          els.safePanel.classList.add('active');
          els.visualPanel.classList.remove('active');
          els.safeTab.classList.add('active');
          els.safeTabTop.classList.add('primary');
          els.visualTab.classList.remove('active');
          els.visualTabTop.classList.remove('primary');
          setStatus('Safe Structure Mode.', state.currentPath || 'No file loaded.');
        } else {
          await loadVisualDocumentHtml(state.currentDocumentHtml);
          els.visualPanel.classList.add('active');
          els.safePanel.classList.remove('active');
          els.visualTab.classList.add('active');
          els.visualTabTop.classList.add('primary');
          els.safeTab.classList.remove('active');
          els.safeTabTop.classList.remove('primary');
          setStatus('True WYSIWYG Mode.', state.currentPath || 'No file loaded.');
        }
      }

      function activeMenuItems() {
        const items = [
          { type: 'item', label: 'Undo', command: 'undo' },
          { type: 'item', label: 'Redo', command: 'redo' },
          { type: 'separator' },
          { type: 'item', label: 'Cut', command: 'cut' },
          { type: 'item', label: 'Copy', command: 'copy' },
          { type: 'item', label: 'Paste', command: 'paste' },
          { type: 'separator' },
          { type: 'item', label: 'Bold', command: 'bold' },
          { type: 'item', label: 'Italic', command: 'italic' },
          { type: 'item', label: 'Underline', command: 'underline' },
          { type: 'item', label: 'Clear formatting', command: 'removeFormat' },
          { type: 'separator' },
          { type: 'item', label: 'Paragraph', block: 'p' },
          { type: 'item', label: 'Heading 1', block: 'h1' },
          { type: 'item', label: 'Heading 2', block: 'h2' },
          { type: 'item', label: 'Block quote', block: 'blockquote' },
          { type: 'separator' },
          { type: 'item', label: 'Bulleted list', command: 'insertUnorderedList' },
          { type: 'item', label: 'Numbered list', command: 'insertOrderedList' },
        ];
        items.push({ type: 'separator' });
        if (state.pendingXmlTag) {
          items.push({ type: 'item', label: `Close XML Tag (${state.pendingXmlTag.name})`, command: 'insertXmlTag' });
        } else {
          items.push({ type: 'item', label: 'Insert XML Tag', command: 'insertXmlTag' });
        }
        return items;
      }

      function activeSelectionState(target) {
        if (target === 'visual') {
          const doc = getVisualDocument();
          const sel = doc ? doc.getSelection() : null;
          const hasTextSelection = !!(sel && !sel.isCollapsed && String(sel).length);
          return { hasTextSelection };
        }
        const sel = window.getSelection();
        const hasTextSelection = !!(sel && !sel.isCollapsed && String(sel).length);
        return { hasTextSelection };
      }

      function renderContextMenu(target) {
        const selection = activeSelectionState(target);
        const items = activeMenuItems();
        els.contextMenu.innerHTML = '';
        for (const item of items) {
          if (item.type === 'separator') {
            const sep = document.createElement('div');
            sep.className = 'menu-separator';
            els.contextMenu.appendChild(sep);
            continue;
          }
          const div = document.createElement('div');
          div.className = 'menu-item';
          div.textContent = item.label;
          div.dataset.command = item.command || '';
          div.dataset.block = item.block || '';
          if ((item.command === 'cut' || item.command === 'copy') && !selection.hasTextSelection) {
            div.setAttribute('aria-disabled', 'true');
          } else {
            div.setAttribute('aria-disabled', 'false');
          }
          div.addEventListener('click', () => {
            if (div.getAttribute('aria-disabled') === 'true') {
              return;
            }
            executeMenuAction(target, item);
            hideContextMenu();
          });
          els.contextMenu.appendChild(div);
        }
      }

      function openContextMenu(target, clientX, clientY) {
        contextMenu.target = target;
        renderContextMenu(target);
        els.contextMenu.classList.add('open');
        els.contextMenu.setAttribute('aria-hidden', 'false');
        els.contextMenu.style.left = '0px';
        els.contextMenu.style.top = '0px';
        const rect = els.contextMenu.getBoundingClientRect();
        const left = Math.min(clientX, window.innerWidth - rect.width - 8);
        const top = Math.min(clientY, window.innerHeight - rect.height - 8);
        els.contextMenu.style.left = Math.max(8, left) + 'px';
        els.contextMenu.style.top = Math.max(8, top) + 'px';
        contextMenu.open = true;
      }

      function hideContextMenu() {
        if (!contextMenu.open) {
          return;
        }
        els.contextMenu.classList.remove('open');
        els.contextMenu.setAttribute('aria-hidden', 'true');
        contextMenu.open = false;
        contextMenu.target = null;
      }

      function executeMenuAction(target, item) {
        if (target === 'visual') {
          if (item.command === 'insertXmlTag') {
            insertXmlTagAtCursor();
            return;
          }
          if (item.block) {
            visualFormatBlock(item.block);
          } else {
            visualExecCommand(item.command);
          }
        }
      }

      function installGlobalMenuDismiss() {
        document.addEventListener('mousedown', (event) => {
          if (!contextMenu.open) {
            return;
          }
          if (!els.contextMenu.contains(event.target)) {
            hideContextMenu();
          }
        });
        document.addEventListener('scroll', hideContextMenu, true);
        window.addEventListener('resize', hideContextMenu);
        window.addEventListener('blur', hideContextMenu);
        document.addEventListener('keydown', (event) => {
          if (event.key === 'Escape') {
            hideContextMenu();
          }
          if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 's') {
            event.preventDefault();
            saveDocument(false);
          }
          if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'o') {
            event.preventDefault();
            openDocument();
          }
        });
      }

      function installSafeEditorHandlers() {
        els.safeEditor.addEventListener('contextmenu', () => {
          hideContextMenu();
        });
        els.safeEditor.addEventListener('mouseup', hideContextMenu);
        els.safeEditor.addEventListener('keyup', hideContextMenu);
      }

      function installUiHandlers() {
        els.openBtn.addEventListener('click', () => openDocument());
        els.saveBtn.addEventListener('click', () => saveDocument(false));
        els.saveAsBtn.addEventListener('click', () => saveDocument(true));
        els.safeTab.addEventListener('click', () => switchMode('safe'));
        els.safeTabTop.addEventListener('click', () => switchMode('safe'));
        els.visualTab.addEventListener('click', () => switchMode('visual'));
        els.visualTabTop.addEventListener('click', () => switchMode('visual'));
      }

      async function applyLoadedDocument(path, content) {
        state.currentPath = path || null;
        state.currentDocumentHtml = ensureFullHtml(content || blankDocumentHtml());
        updateWindowTitle();
        if (state.currentMode === 'safe') {
          loadSafeBodyHtml(extractBodyHtml(state.currentDocumentHtml));
        } else {
          await loadVisualDocumentHtml(state.currentDocumentHtml);
        }
        setDirty(false);
      }

      async function openDocument() {
        try {
          hideContextMenu();
          setStatus('Opening…', state.currentPath || '');
          const result = await window.pywebview.api.open_file();
          if (!result || !result.ok) {
            setStatus(result && result.message ? result.message : 'Open cancelled.', state.currentPath || 'No file loaded.');
            return;
          }
          await applyLoadedDocument(result.path, result.content);
          setStatus('File loaded.', result.path);
        } catch (error) {
          setStatus('Open failed.', String(error));
        }
      }

      async function saveDocument(forceSaveAs) {
        try {
          hideContextMenu();
          await syncCurrentModeToMemory();
          setStatus(forceSaveAs ? 'Saving as…' : 'Saving…', state.currentPath || 'Untitled.html');
          let result;
          if (forceSaveAs) {
            result = await window.pywebview.api.save_file_as(state.currentDocumentHtml, state.currentPath || 'Untitled.html');
          } else {
            result = await window.pywebview.api.save_current_file(state.currentDocumentHtml, state.currentPath || 'Untitled.html');
          }
          if (!result || !result.ok) {
            setStatus(result && result.message ? result.message : 'Save cancelled.', state.currentPath || 'No file loaded.');
            return;
          }
          state.currentPath = result.path;
          updateWindowTitle();
          setDirty(false);
          setStatus('Saved.', result.path);
        } catch (error) {
          setStatus('Save failed.', String(error));
        }
      }

      async function bootstrap() {
        installUiHandlers();
        installSafeEditorHandlers();
        installGlobalMenuDismiss();
        loadSafeBodyHtml(extractBodyHtml(blankDocumentHtml()));
        updateWindowTitle();
        setStatus('Ready.', 'No file loaded.');

        try {
          const initial = await window.pywebview.api.get_initial_document();
          if (initial && initial.ok) {
            await applyLoadedDocument(initial.path, initial.content);
            setStatus('Ready.', initial.path || 'Untitled.html');
          } else {
            await applyLoadedDocument(null, blankDocumentHtml());
          }
        } catch (error) {
          await applyLoadedDocument(null, blankDocumentHtml());
          setStatus('Ready.', 'No file loaded.');
        }

        state.startupComplete = true;
      }

      window.addEventListener('pywebviewready', bootstrap);
    })();
  </script>
</body>
</html>
"""


class AppApi:
    def __init__(self, initial_path: Optional[str] = None) -> None:
        self.current_path: Optional[str] = None
        self.initial_path = str(Path(initial_path).resolve()) if initial_path else None

    def attach_window(self, window: webview.Window) -> None:
        global APP_WINDOW
        APP_WINDOW = window

    def _ensure_window(self) -> webview.Window:
        if APP_WINDOW is None:
            raise RuntimeError("Application window is not ready.")
        return APP_WINDOW

    def _read_path(self, path: str) -> str:
        return Path(path).read_text(encoding="utf-8")

    def _write_path(self, path: str, content: str) -> None:
        Path(path).write_text(content, encoding="utf-8", newline="\n")

    def get_initial_document(self) -> dict:
        if not self.initial_path:
            return {"ok": True, "path": None, "content": ""}

        path = Path(self.initial_path)
        if not path.exists():
            return {"ok": False, "message": f"Initial file not found: {path}"}

        self.current_path = str(path)
        return {"ok": True, "path": self.current_path, "content": self._read_path(self.current_path)}

    def open_file(self) -> dict:
        window = self._ensure_window()
        result = window.create_file_dialog(
            webview.FileDialog.OPEN,
            allow_multiple=False,
            file_types=("HTML files (*.html;*.htm)", "All files (*.*)"),
        )
        if not result:
            return {"ok": False, "message": "Open cancelled."}

        chosen = result[0] if isinstance(result, (list, tuple)) else result
        path = str(Path(chosen).resolve())
        self.current_path = path
        return {"ok": True, "path": path, "content": self._read_path(path)}

    def save_current_file(self, content: str, suggested_name: str = "Untitled.html") -> dict:
        if self.current_path:
            self._write_path(self.current_path, content)
            return {"ok": True, "path": self.current_path}
        return self.save_file_as(content, suggested_name)

    def save_file_as(self, content: str, suggested_name: str = "Untitled.html") -> dict:
        window = self._ensure_window()
        suggestion = Path(suggested_name).name if suggested_name else "Untitled.html"
        result = window.create_file_dialog(
            webview.FileDialog.SAVE,
            save_filename=suggestion,
            file_types=("HTML files (*.html;*.htm)", "All files (*.*)"),
        )
        if not result:
            return {"ok": False, "message": "Save cancelled."}

        chosen = result if isinstance(result, str) else result[0]
        path = str(Path(chosen).resolve())
        self._write_path(path, content)
        self.current_path = path
        return {"ok": True, "path": path}


def main() -> None:
    initial_path = sys.argv[1] if len(sys.argv) > 1 else None
    api = AppApi(initial_path=initial_path)

    window = webview.create_window(
        title="AI-Safe HTML Editor",
        html=APP_HTML,
        js_api=api,
        width=1440,
        height=960,
        min_size=(1080, 720),
        confirm_close=True,
    )
    api.attach_window(window)

    # On Windows, pywebview will use the Edge/WebView2 backend when available.
    webview.start(debug=False)


if __name__ == "__main__":
    main()
