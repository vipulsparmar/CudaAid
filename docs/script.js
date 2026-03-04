/* ═══════════════════════════════════════════════════════════════════════════
   CudaAid — Landing Page Interactions
   ═══════════════════════════════════════════════════════════════════════════ */

// ── Navbar scroll effect ─────────────────────────────────────────────────
const navbar = document.getElementById('navbar');

window.addEventListener('scroll', () => {
    if (window.scrollY > 40) {
        navbar.classList.add('scrolled');
    } else {
        navbar.classList.remove('scrolled');
    }
});

// ── Copy install command ─────────────────────────────────────────────────
function copyInstall() {
    const text = document.getElementById('install-text').textContent;
    const btn = document.getElementById('copy-btn');

    navigator.clipboard.writeText(text).then(() => {
        btn.textContent = 'Copied!';
        btn.classList.add('copied');
        setTimeout(() => {
            btn.textContent = 'Copy';
            btn.classList.remove('copied');
        }, 2000);
    }).catch(() => {
        // Fallback for older browsers
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        btn.textContent = 'Copied!';
        btn.classList.add('copied');
        setTimeout(() => {
            btn.textContent = 'Copy';
            btn.classList.remove('copied');
        }, 2000);
    });
}

// ── Terminal tab switching ───────────────────────────────────────────────
function showTab(tabName) {
    // Deactivate all tabs
    document.querySelectorAll('.terminal-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.terminal-content').forEach(c => c.classList.remove('active'));

    // Activate selected
    document.getElementById('tab-' + tabName).classList.add('active');

    // Find and activate the matching button
    document.querySelectorAll('.terminal-tab').forEach(t => {
        if (t.textContent.toLowerCase().includes(tabName)) {
            t.classList.add('active');
        }
    });
}

// ── Scroll reveal ────────────────────────────────────────────────────────
const revealElements = document.querySelectorAll('.reveal');

const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry, index) => {
        if (entry.isIntersecting) {
            // Stagger animation for sibling cards
            const siblings = entry.target.parentElement.querySelectorAll('.reveal');
            let delay = 0;
            siblings.forEach((sib, i) => {
                if (sib === entry.target) {
                    delay = i * 80;
                }
            });

            setTimeout(() => {
                entry.target.classList.add('visible');
            }, delay);

            revealObserver.unobserve(entry.target);
        }
    });
}, {
    threshold: 0.1,
    rootMargin: '0px 0px -40px 0px'
});

revealElements.forEach(el => revealObserver.observe(el));

// ── Smooth scroll for nav links ──────────────────────────────────────────
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            const offset = 80; // navbar height
            const top = target.getBoundingClientRect().top + window.scrollY - offset;
            window.scrollTo({ top, behavior: 'smooth' });
        }
    });
});
