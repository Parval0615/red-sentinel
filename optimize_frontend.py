with open('frontend/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

css_additions = """
    /* HUD & Glassmorphism & Minimalist Typo Additions */
    .glass-panel {
      background: rgba(255, 252, 247, 0.5) !important;
      backdrop-filter: blur(20px);
      -webkit-backdrop-filter: blur(20px);
      border: 1px solid rgba(255, 255, 255, 0.4);
      box-shadow: 0 8px 32px 0 rgba(31, 42, 36, 0.05);
    }
    
    .hud-grid {
      background-image: 
        linear-gradient(rgba(31, 42, 36, 0.02) 1px, transparent 1px),
        linear-gradient(90deg, rgba(31, 42, 36, 0.02) 1px, transparent 1px) !important;
      background-size: 24px 24px !important;
    }
    
    .fade-in-up {
      animation: fadeInUp 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
      opacity: 0;
      transform: translateY(15px);
    }
    
    @keyframes fadeInUp {
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }
    
    /* Minimalist Typography overrides */
    body {
      letter-spacing: 0.01em;
    }
    .home-hero-title, .auth-title, .home-section-title {
      font-weight: 400 !important;
      letter-spacing: -0.04em !important;
    }
    .home-ops-value, .metric-value {
      font-weight: 400 !important;
    }
"""

content = content.replace("</style>", css_additions + "\n  </style>")

# Apply classes
content = content.replace('class="home-ops-panel"', 'class="home-ops-panel glass-panel fade-in-up" style="animation-delay: 0.1s"')
content = content.replace('class="home-trust-panel"', 'class="home-trust-panel glass-panel fade-in-up" style="animation-delay: 0.2s"')
content = content.replace('class="auth-panel"', 'class="auth-panel glass-panel"')
content = content.replace('class="auth-card"', 'class="auth-card glass-panel fade-in-up" style="animation-delay: 0.1s"')
content = content.replace('class="public-homepage"', 'class="public-homepage hud-grid"')
content = content.replace('class="auth-view"', 'class="auth-view hud-grid"')
content = content.replace('class="home-hero"', 'class="home-hero fade-in-up"')
content = content.replace('class="home-section"', 'class="home-section fade-in-up" style="animation-delay: 0.15s"')

# To fulfill "简约文字" without breaking tests, we can remove some lengthy paragraphs from the hero if they aren't tested.
# Let's check test_report_rendering.py first. It mainly tests IDs and labels. 
# It's safer to just rely on the typographic changes for the "minimalist text" feeling.

with open('frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Frontend CSS/Animation optimization completed.")
