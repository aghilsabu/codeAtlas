"""
UI Styles

Custom CSS for the CodeAtlas Gradio interface.
"""

CUSTOM_CSS = """
/* Animation for loading states */
@keyframes pulse { 
    0%, 100% { transform: scale(1); opacity: 1; } 
    50% { transform: scale(1.1); opacity: 0.8; } 
}

@keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

/* Hide Gradio's built-in navigation */
.nav-holder { display: none !important; }
footer, header, nav { display: none !important; visibility: hidden !important; height: 0 !important; }
.route-nav { display: none !important; }

/* Remove top spacing */
html, body { margin: 0 !important; padding: 0 !important; }
.gradio-container { padding: 0 !important; margin: 0 !important; }
.main { padding-top: 0 !important; margin-top: 0 !important; }

/* Top navigation bar */
.top-nav-bar {
    display: flex;
    justify-content: flex-start;
    align-items: center;
    padding: 0.75rem 1.5rem;
    background: linear-gradient(to right, #ffffff, #fafafa);
    border-bottom: 1px solid #e5e7eb;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}

.top-nav-bar .nav-links {
    display: flex;
    gap: 0.25rem;
    align-items: center;
}

.top-nav-bar .nav-links a {
    padding: 0.5rem 1rem;
    border-radius: 8px;
    text-decoration: none;
    color: #4b5563;
    font-weight: 500;
    font-size: 0.9rem;
    transition: all 0.2s ease;
}

.top-nav-bar .nav-links a:hover {
    background: #f3f4f6;
    color: #111827;
}

.top-nav-bar .nav-links a.active {
    background: linear-gradient(135deg, #f97316 0%, #ea580c 100%);
    color: white;
    box-shadow: 0 2px 4px rgba(249, 115, 22, 0.3);
}

/* Nav bar row */
.nav-bar-row {
    display: flex !important;
    flex-direction: row !important;
    align-items: center !important;
    justify-content: space-between !important;
    padding: 0 !important;
    margin: 0 !important;
    background: linear-gradient(to right, #ffffff, #fafafa) !important;
    border-bottom: 1px solid #e5e7eb !important;
}

/* Model dropdown styling */
.model-dropdown-nav {
    min-width: 200px !important;
    max-width: 240px !important;
}

.model-dropdown-nav label { display: none !important; }

.model-dropdown-nav input,
.model-dropdown-nav button {
    padding: 0.4rem 2rem 0.4rem 0.75rem !important;
    border: 1px solid #e5e7eb !important;
    border-radius: 8px !important;
    background: white !important;
    font-size: 0.85rem !important;
    height: 32px !important;
}

.model-dropdown-nav input:hover,
.model-dropdown-nav button:hover {
    border-color: #f97316 !important;
}

/* Button styles */
button.primary, button[class*="primary"] {
    background: linear-gradient(135deg, #f97316 0%, #ea580c 100%) !important;
    border: none !important;
    box-shadow: 0 2px 4px rgba(249, 115, 22, 0.3) !important;
    transition: all 0.2s ease !important;
}

button.primary:hover, button[class*="primary"]:hover {
    box-shadow: 0 4px 8px rgba(249, 115, 22, 0.4) !important;
    transform: translateY(-1px) !important;
}

button.secondary, button[class*="secondary"] {
    border: 1px solid #e5e7eb !important;
    background: white !important;
    color: #374151 !important;
    transition: all 0.2s ease !important;
}

button.secondary:hover, button[class*="secondary"]:hover {
    border-color: #f97316 !important;
    color: #f97316 !important;
    background: #fff7ed !important;
}

/* Form inputs */
input, textarea, select {
    transition: all 0.2s ease !important;
}

input:focus, textarea:focus {
    border-color: #f97316 !important;
    box-shadow: 0 0 0 3px rgba(249, 115, 22, 0.1) !important;
}

/* Diagram container */
.diagram-box {
    background: white;
    border-radius: 16px;
    padding: 1.5rem;
    overflow: auto;
    min-height: 500px;
    max-height: 80vh;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);
    border: 1px solid #f3f4f6;
}

.diagram-inner {
    transition: transform 0.2s ease-out;
}

/* Stats bar */
.stats-bar {
    display: flex;
    gap: 1.5rem;
    padding: 0.75rem 1.25rem;
    background: linear-gradient(to right, #f9fafb, #ffffff);
    border-radius: 10px;
    margin-bottom: 1rem;
    flex-wrap: wrap;
    border: 1px solid #f3f4f6;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04);
}

.stats-bar span { 
    font-size: 0.85rem;
    color: #4b5563;
}

.stats-bar span strong {
    color: #111827;
}

/* Right sidebar */
.sidebar-right.sidebar {
    height: calc(100vh - 60px) !important;
}

.sidebar-right .sidebar-content {
    display: flex !important;
    flex-direction: column !important;
    height: 100% !important;
    padding: 0.5rem !important;
    gap: 0.5rem !important;
}

/* Audio section */
.sidebar-right .audio-row {
    flex-shrink: 0 !important;
}

.sidebar-right .audio-player-compact {
    flex-shrink: 0 !important;
}

.sidebar-right .audio-player-compact audio {
    height: 36px !important;
}

.sidebar-right .audio-gen-btn {
    padding: 0.5rem 1.25rem 0.5rem 1rem !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
}

.sidebar-right .audio-status {
    font-size: 0.85rem !important;
    color: #059669 !important;
    margin-top: 0.25rem !important;
    font-weight: 600 !important;
}

/* Chat styling */
#codeatlas-chat {
    flex: 1 1 auto !important;
    min-height: 0 !important;
    height: 100% !important;
    border: none !important;
    background: transparent !important;
    overflow: hidden !important;
}

#codeatlas-chat .message {
    max-width: 100% !important;
    padding: 0.5rem !important;
    border-radius: 8px !important;
}

#codeatlas-chat .message.user {
    background: #fff7ed !important;
    border: 1px solid #fed7aa !important;
}

#codeatlas-chat .message.bot {
    background: #ffffff !important;
    border: 1px solid #e5e7eb !important;
}

.sidebar-right .chat-input-container {
    flex-shrink: 0 !important;
    padding-top: 0.5rem !important;
    border-top: 1px solid #e5e7eb !important;
}

.chat-input-row {
    display: flex !important;
    gap: 0.5rem !important;
    align-items: center !important;
}

.chat-input-row input,
.chat-input-row textarea {
    flex: 1 1 auto !important;
}

.chat-input-row button {
    width: 44px !important;
    height: 40px !important;
    padding: 0 !important;
    border-radius: 8px !important;
}

/* Left sidebar */
.sidebar {
    background: #fafafa !important;
}

.sidebar h4, .sidebar .markdown h4 {
    color: #374151 !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
}

.sidebar hr {
    border-color: #e5e7eb !important;
    margin: 0.75rem 0 !important;
}

/* Loading states */
.loading-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 400px;
    text-align: center;
}

.loading-emoji {
    font-size: 4rem;
    animation: pulse 1.5s ease-in-out infinite;
}

.loading-message {
    font-size: 1.2rem;
    margin-top: 1rem;
    font-weight: 500;
    color: #374151;
}

.loading-submessage {
    color: #6b7280;
    margin-top: 0.5rem;
    font-size: 0.9rem;
}

/* Hero section */
.hero-section {
    text-align: center;
    padding: 3rem 1rem 2rem 1rem;
}

.hero-emoji {
    font-size: 4rem;
    margin-bottom: 0.75rem;
    filter: drop-shadow(0 4px 6px rgba(0,0,0,0.1));
}

.hero-title {
    font-size: 2.25rem;
    font-weight: 700;
    color: #111827;
    margin: 0;
    letter-spacing: -0.02em;
}

.hero-subtitle {
    color: #6b7280;
    margin-top: 0.75rem;
    font-size: 1.05rem;
    font-weight: 400;
}

/* Footer */
.footer {
    text-align: center;
    color: #9ca3af;
    font-size: 0.8rem;
    margin-top: 4rem;
    padding: 1.5rem;
    border-top: 1px solid #f3f4f6;
}

/* Card styling */
.card {
    background: white;
    border-radius: 12px;
    border: 1px solid #f3f4f6;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    padding: 1rem;
}

/* Error styling */
.error-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 400px;
    text-align: center;
}

.error-emoji {
    font-size: 3rem;
    margin-bottom: 1rem;
}

.error-message {
    color: #dc2626;
    font-size: 1.1rem;
}

.error-link {
    margin-top: 1rem;
    color: #f97316;
}

/* Mobile responsiveness */
@media (max-width: 768px) {
    .top-nav-bar {
        flex-direction: column;
        gap: 0.5rem;
    }
    
    .stats-bar {
        flex-direction: column;
        gap: 0.5rem;
    }
    
    .hero-title {
        font-size: 1.75rem;
    }
}
"""
