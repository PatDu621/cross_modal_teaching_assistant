"""UI style definitions for the Gradio teaching assistant frontend."""

CUSTOM_CSS = """
:root {
    --edu-green-900: #064e3b;
    --edu-green-800: #065f46;
    --edu-green-700: #047857;
    --edu-green-600: #059669;
    --edu-green-100: #d1fae5;
    --edu-green-50: #ecfdf5;
    --edu-blue: #3b82f6;
    --edu-blue-50: #eff6ff;
    --edu-purple: #8b5cf6;
    --edu-purple-50: #f5f3ff;
    --edu-yellow: #f59e0b;
    --edu-yellow-50: #fffbeb;
    --edu-ink: #111827;
    --edu-text: #374151;
    --edu-muted: #6b7280;
    --edu-line: #e5e7eb;
    --edu-bg: #f7faf8;
    --edu-panel: #ffffff;
    --edu-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
}

.gradio-container {
    max-width: none !important;
    color: var(--edu-text);
    background: var(--edu-bg);
    font-size: 14px !important;
    padding: 22px 24px 18px;
}

.contain,
.gradio-container > .main {
    max-width: 1680px !important;
    margin: 0 auto !important;
}

.edu-header {
    height: 76px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 24px;
    padding: 0 20px;
    margin-bottom: 24px;
    background: var(--edu-panel);
    border: 1px solid var(--edu-line);
    border-radius: 8px;
    box-shadow: var(--edu-shadow);
}

.edu-brand {
    display: flex;
    align-items: center;
    gap: 12px;
}

.edu-logo {
    width: 40px;
    height: 40px;
    border-radius: 8px;
    display: grid;
    place-items: center;
    color: white;
    font-weight: 800;
    background: linear-gradient(135deg, var(--edu-green-700), #34d399);
}

.edu-title {
    margin: 0;
    color: var(--edu-ink);
    font-size: 22px;
    line-height: 1.25;
    font-weight: 800;
}

.edu-subtitle {
    margin: 4px 0 0;
    color: var(--edu-muted);
    font-size: 12px;
    line-height: 1.4;
}

.edu-status-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    color: var(--edu-green-800);
    background: var(--edu-green-50);
    border: 1px solid var(--edu-green-100);
    border-radius: 999px;
    font-size: 12px;
    white-space: nowrap;
}

.edu-status-dot {
    width: 8px;
    height: 8px;
    border-radius: 999px;
    background: var(--edu-green-600);
}

.edu-layout {
    gap: 24px !important;
    align-items: stretch;
    max-width: 1680px;
    margin: 0 auto;
}

.edu-sidebar {
    background: var(--edu-panel);
    border: 1px solid var(--edu-line);
    border-radius: 8px;
    padding: 16px 12px;
    box-shadow: var(--edu-shadow);
    min-height: 680px;
}

.edu-sidebar button {
    width: 100% !important;
    justify-content: flex-start !important;
    min-height: 44px !important;
    margin: 6px 0 !important;
    padding-left: 16px !important;
    color: var(--edu-text) !important;
    background: #ffffff !important;
    border: 1px solid transparent !important;
    box-shadow: none !important;
    font-size: 15px !important;
    font-weight: 750 !important;
}

.edu-sidebar button.primary {
    color: var(--edu-green-800) !important;
    background: var(--edu-green-50) !important;
    border-color: var(--edu-green-100) !important;
}

.edu-sidebar button:hover {
    color: var(--edu-green-800) !important;
    background: #f0fdf4 !important;
    border-color: var(--edu-green-100) !important;
}

.edu-side-label {
    color: var(--edu-muted);
    font-size: 12px;
    font-weight: 700;
    padding: 4px 10px 10px;
}

.edu-sidebar-note {
    margin: 18px 10px 0;
    padding: 12px;
    color: var(--edu-muted);
    background: #f9fafb;
    border: 1px dashed #d1d5db;
    border-radius: 8px;
    font-size: 12px;
    line-height: 1.6;
}

.edu-sidebar-note.accent {
    background: linear-gradient(135deg, var(--edu-green-50), var(--edu-blue-50));
    border-color: var(--edu-green-100);
}

.edu-main {
    gap: 24px !important;
    min-width: 0;
}

.edu-main > div {
    width: 100%;
}

.edu-page-grid,
.edu-inner-grid,
.edu-two-col {
    gap: 24px !important;
    align-items: stretch !important;
}

.edu-page-grid {
    display: grid !important;
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) !important;
    width: 100% !important;
}

.edu-inner-grid {
    display: grid !important;
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) !important;
    width: 100% !important;
}

.edu-two-col {
    display: grid !important;
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) !important;
    width: 100% !important;
}

.edu-export-grid {
    display: grid !important;
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) !important;
    gap: 24px !important;
    width: 100% !important;
}

.edu-page-grid > div,
.edu-inner-grid > div,
.edu-two-col > div {
    width: 100% !important;
    max-width: none !important;
    min-width: 0 !important;
    flex: none !important;
}

.edu-export-grid > div {
    width: 100% !important;
    max-width: none !important;
    min-width: 0 !important;
    flex: none !important;
}

.edu-page-head {
    position: relative;
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 24px;
    padding: 18px 20px;
    background: var(--edu-panel);
    border: 1px solid var(--edu-line);
    border-radius: 8px;
    box-shadow: var(--edu-shadow);
    overflow: hidden;
    width: 100%;
    min-height: 104px;
}

.edu-page-head h2 {
    margin: 0;
    color: var(--edu-ink);
    font-size: 22px;
    line-height: 1.25;
    font-weight: 850;
}

.edu-page-head p {
    margin: 5px 0 0;
    color: var(--edu-muted);
    font-size: 12px;
    line-height: 1.5;
}

.edu-page-icon,
.edu-mini-icon {
    display: inline-grid;
    place-items: center;
    flex: none;
    border-radius: 8px;
    font-weight: 850;
}

.edu-page-icon {
    width: 46px;
    height: 46px;
    color: white;
    font-size: 18px;
}

.edu-mini-icon {
    width: 38px;
    height: 38px;
    font-size: 12px;
}

.edu-page-icon.green,
.edu-mini-icon.green {
    background: var(--edu-green-50);
    color: var(--edu-green-800);
    border: 1px solid var(--edu-green-100);
}

.edu-page-icon.blue,
.edu-mini-icon.blue {
    background: var(--edu-blue-50);
    color: var(--edu-blue);
    border: 1px solid #bfdbfe;
}

.edu-page-icon.purple,
.edu-mini-icon.purple {
    background: var(--edu-purple-50);
    color: var(--edu-purple);
    border: 1px solid #ddd6fe;
}

.edu-page-icon.yellow,
.edu-mini-icon.yellow {
    background: var(--edu-yellow-50);
    color: var(--edu-yellow);
    border: 1px solid #fde68a;
}

.edu-dot {
    position: absolute;
    width: 10px;
    height: 10px;
    border-radius: 999px;
    opacity: 0.9;
}

.edu-dot:nth-of-type(1) {
    right: 78px;
    top: 18px;
}

.edu-dot:nth-of-type(2) {
    right: 48px;
    top: 36px;
}

.edu-dot:nth-of-type(3) {
    right: 24px;
    bottom: 18px;
}

.edu-dot.green {
    background: var(--edu-green-600);
}

.edu-dot.blue {
    background: var(--edu-blue);
}

.edu-dot.purple {
    background: var(--edu-purple);
}

.edu-dot.yellow {
    background: var(--edu-yellow);
}

.edu-card {
    background: var(--edu-panel);
    border: 1px solid var(--edu-line);
    border-radius: 8px;
    padding: 18px;
    box-shadow: var(--edu-shadow);
    width: 100%;
    height: 100%;
    min-width: 0;
    box-sizing: border-box;
    display: flex !important;
    flex-direction: column;
}

.edu-card + .edu-card {
    margin-top: 0;
}


.edu-card-balanced {
    min-height: 420px;
}


.edu-export-grid .edu-card-balanced {
    min-height: 500px;
}

.edu-export-grid .form,
.edu-export-grid .file-preview,
.edu-export-grid .upload-container {
    width: 100% !important;
    max-width: none !important;
}

.edu-export-grid .file-preview,
.edu-export-grid .upload-container {
    flex: 1 1 auto !important;
    min-height: 330px !important;
    height: 100% !important;
}

.edu-card-wide {
    margin-top: 24px;
}

.edu-card-title {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 18px;
    min-height: 48px;
    flex: 0 0 auto;
}

.edu-card-title h3 {
    margin: 0;
    color: var(--edu-ink);
    font-size: 18px;
    line-height: 1.3;
    font-weight: 850;
}

.edu-card-title p {
    margin: 4px 0 0;
    color: var(--edu-muted);
    font-size: 12px;
    line-height: 1.45;
}

.edu-card.compact {
    min-height: 174px;
}

.edu-section-title {
    margin: 0 0 14px;
    color: var(--edu-ink);
    font-size: 18px;
    line-height: 1.35;
    font-weight: 800;
}

.edu-section-kicker {
    margin: -8px 0 14px;
    color: var(--edu-muted);
    font-size: 12px;
}

.edu-two-col {
    gap: 24px !important;
}

.edu-result {
    min-height: 180px;
    padding: 14px;
    background: #ffffff;
    border: 1px solid var(--edu-line);
    border-radius: 8px;
    flex: 1 1 auto;
    overflow: auto;
}

.edu-inner-grid {
    margin-bottom: 16px;
    flex: 1 1 auto;
}

.edu-inner-grid .form,
.edu-inner-grid .block,
.edu-inner-grid .wrap {
    width: 100% !important;
    height: 100% !important;
}

.edu-inner-grid .upload-container,
.edu-inner-grid .file-preview {
    min-height: 250px !important;
    height: 100% !important;
}

.edu-fill-textbox,
.edu-fill-textbox > div,
.edu-fill-textbox .wrap,
.edu-fill-textbox textarea {
    flex: 1 1 auto !important;
    height: 100% !important;
    min-height: 0 !important;
}

.edu-card-balanced .edu-fill-textbox textarea {
    min-height: 270px !important;
}

.edu-status-card {
    min-height: 260px;
}

.edu-status-card .edu-fill-textbox {
    flex: 1 1 auto !important;
}

.edu-status-card textarea {
    min-height: 140px !important;
}

.edu-card-actions {
    margin-top: auto !important;
    width: 100% !important;
    gap: 12px !important;
    flex: 0 0 auto;
}

.edu-card-actions > div {
    width: 100% !important;
    min-width: 0 !important;
}

.edu-card-actions button {
    width: 100% !important;
}

.edu-meta-panel {
    width: 100%;
}

.edu-result .prose,
.edu-card .prose {
    font-size: 14px;
    line-height: 1.75;
}

.edu-meta-panel {
    display: grid;
    grid-template-columns: minmax(220px, 1.7fr) minmax(260px, 2fr) minmax(86px, 0.7fr) minmax(86px, 0.7fr) minmax(150px, 1fr);
    gap: 10px;
    width: 100%;
}

.edu-meta-item {
    padding: 12px;
    background: var(--edu-green-50);
    border: 1px solid var(--edu-green-100);
    border-radius: 8px;
}

.edu-meta-label {
    color: var(--edu-muted);
    font-size: 12px;
    margin-bottom: 6px;
}

.edu-meta-value {
    color: var(--edu-ink);
    font-size: 14px;
    font-weight: 750;
    overflow-wrap: anywhere;
}

button.primary,
.gradio-button.primary {
    background: var(--edu-green-700) !important;
    border-color: var(--edu-green-700) !important;
    color: white !important;
    font-size: 15px !important;
    font-weight: 750 !important;
    border-radius: 8px !important;
}

button.primary:hover,
.gradio-button.primary:hover {
    background: var(--edu-green-800) !important;
    border-color: var(--edu-green-800) !important;
}

button.secondary,
.gradio-button.secondary,
button {
    font-size: 15px !important;
    border-radius: 8px !important;
}

label,
.label-wrap span {
    font-size: 12px !important;
    color: var(--edu-muted) !important;
}

textarea,
input,
.wrap,
.prose,
.markdown,
.output-markdown {
    font-size: 14px !important;
}

.tabs {
    border-radius: 8px !important;
}

.edu-assistant-card {
    min-height: 640px;
}

.edu-assistant-card .tabs,
.edu-assistant-card .tabitem,
.edu-assistant-card [role="tabpanel"] {
    flex: 1 1 auto !important;
    min-height: 520px !important;
}

.edu-assistant-card .tabs {
    display: flex !important;
    flex-direction: column !important;
}

.edu-assistant-card [role="tabpanel"] {
    height: 100% !important;
}

.edu-assistant-card .edu-two-col {
    min-height: 340px;
}

.edu-assistant-card .edu-result {
    min-height: 300px;
}

.tab-nav {
    gap: 8px !important;
    border-bottom: 1px solid var(--edu-line) !important;
}

.tab-nav button {
    font-size: 14px !important;
    color: var(--edu-muted) !important;
    border-radius: 8px 8px 0 0 !important;
}

.tab-nav button.selected {
    color: var(--edu-green-800) !important;
    border-bottom-color: var(--edu-green-700) !important;
}

.file-preview,
.upload-container {
    border-radius: 8px !important;
}

footer {
    text-align: center;
    color: var(--edu-muted);
    padding: 18px 0 4px;
    font-size: 12px;
}

@media (max-width: 920px) {
    .gradio-container {
        padding: 14px;
    }
    .edu-header {
        height: auto;
        flex-direction: column;
        align-items: flex-start;
        padding: 16px;
    }
    .edu-sidebar {
        min-height: auto;
    }
    .edu-meta-panel {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
}

@media (max-width: 640px) {
    .edu-meta-panel {
        grid-template-columns: 1fr;
    }
}
"""
