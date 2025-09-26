/**
 * Header Component JavaScript
 * Handles scroll behavior and mobile menu interactions
 */

document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const header = document.getElementById('main-header');
    const menuToggle = document.querySelector('.header__menu-toggle');
    const mobileOverlay = document.querySelector('.mobile-overlay');
    const closeButton = document.querySelector('.mobile-overlay__close');
    const mobileNavLinks = document.querySelectorAll('.mobile-nav__link, .mobile-nav__cta');
    const body = document.body;

    // State
    let scrollPosition = 0;
    let isMenuOpen = false;

    /**
     * Header Scroll Behavior
     * Adds background and shadow when scrolling past threshold
     */
    const handleScroll = () => {
        const currentScroll = window.scrollY;
        const scrollThreshold = 80;

        if (currentScroll > scrollThreshold) {
            header.classList.add('header--scrolled');
        } else {
            header.classList.remove('header--scrolled');
        }

        scrollPosition = currentScroll;
    };

    /**
     * Mobile Menu Toggle
     * Opens/closes the mobile overlay menu
     */
    const toggleMobileMenu = () => {
        isMenuOpen = !isMenuOpen;

        if (isMenuOpen) {
            openMobileMenu();
        } else {
            closeMobileMenu();
        }
    };

    /**
     * Open Mobile Menu
     * Activates overlay and prevents body scroll
     */
    const openMobileMenu = () => {
        mobileOverlay.classList.add('mobile-overlay--active');
        menuToggle.classList.add('active');
        menuToggle.setAttribute('aria-expanded', 'true');
        mobileOverlay.setAttribute('aria-hidden', 'false');
        body.classList.add('menu-open');

        // Reset animation for menu items
        resetMenuItemAnimations();
    };

    /**
     * Close Mobile Menu
     * Deactivates overlay and restores body scroll
     */
    const closeMobileMenu = () => {
        mobileOverlay.classList.remove('mobile-overlay--active');
        menuToggle.classList.remove('active');
        menuToggle.setAttribute('aria-expanded', 'false');
        mobileOverlay.setAttribute('aria-hidden', 'true');
        body.classList.remove('menu-open');
        isMenuOpen = false;
    };

    /**
     * Reset Menu Item Animations
     * Restarts the fade-in animation for menu items
     */
    const resetMenuItemAnimations = () => {
        const menuItems = document.querySelectorAll('.mobile-nav__item');
        menuItems.forEach((item, index) => {
            item.style.animation = 'none';
            setTimeout(() => {
                item.style.animation = `fadeInUp 0.5s ease forwards`;
                item.style.animationDelay = `${(index + 1) * 0.1}s`;
            }, 10);
        });
    };

    /**
     * Smooth Scroll to Anchor
     * Handles smooth scrolling for anchor links
     */
    const handleAnchorClick = (e) => {
        const href = e.currentTarget.getAttribute('href');

        if (href.startsWith('#')) {
            e.preventDefault();
            const target = document.querySelector(href);

            if (target) {
                // Close mobile menu if open
                if (isMenuOpen) {
                    closeMobileMenu();
                }

                // Calculate scroll position with header offset
                const headerHeight = header.offsetHeight;
                const targetPosition = target.offsetTop - headerHeight;

                // Smooth scroll to target
                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });
            }
        }
    };

    /**
     * Initialize Smooth Scroll for All Anchor Links
     */
    const initSmoothScroll = () => {
        const anchorLinks = document.querySelectorAll('a[href^="#"]');
        anchorLinks.forEach(link => {
            link.addEventListener('click', handleAnchorClick);
        });
    };

    /**
     * Keyboard Navigation Support
     * Handle ESC key to close mobile menu
     */
    const handleKeyboard = (e) => {
        if (e.key === 'Escape' && isMenuOpen) {
            closeMobileMenu();
            menuToggle.focus(); // Return focus to menu toggle
        }
    };

    /**
     * Handle Resize Events
     * Close mobile menu when resizing to desktop viewport
     */
    const handleResize = () => {
        if (window.innerWidth > 768 && isMenuOpen) {
            closeMobileMenu();
        }
    };

    /**
     * Initialize Event Listeners
     */
    const init = () => {
        // Scroll events (throttled for performance)
        let scrollThrottle;
        window.addEventListener('scroll', () => {
            if (!scrollThrottle) {
                scrollThrottle = setTimeout(() => {
                    handleScroll();
                    scrollThrottle = null;
                }, 10);
            }
        });

        // Mobile menu events
        menuToggle.addEventListener('click', toggleMobileMenu);
        closeButton.addEventListener('click', closeMobileMenu);

        // Close menu when clicking mobile nav links
        mobileNavLinks.forEach(link => {
            link.addEventListener('click', () => {
                if (!link.getAttribute('href').startsWith('#')) {
                    // For external links, close menu after a small delay
                    setTimeout(closeMobileMenu, 100);
                }
            });
        });

        // Keyboard navigation
        document.addEventListener('keydown', handleKeyboard);

        // Handle window resize
        let resizeThrottle;
        window.addEventListener('resize', () => {
            if (!resizeThrottle) {
                resizeThrottle = setTimeout(() => {
                    handleResize();
                    resizeThrottle = null;
                }, 100);
            }
        });

        // Initialize smooth scroll
        initSmoothScroll();

        // Initial scroll check
        handleScroll();
    };

    // Start the application
    init();
});

/**
 * Hero Section Animations
 * Triggers fade-in animations for hero content on page load
 */
const initHeroAnimations = () => {
    const animateElements = document.querySelectorAll('.animate-on-load');

    // Add visible class with staggered delay
    animateElements.forEach((element, index) => {
        setTimeout(() => {
            element.classList.add('visible');
        }, 100); // Small initial delay to ensure smooth animation start
    });

    // Scroll indicator click handler
    const scrollIndicator = document.querySelector('.hero__scroll-indicator');
    if (scrollIndicator) {
        scrollIndicator.addEventListener('click', () => {
            const nextSection = document.querySelector('#approche');
            if (nextSection) {
                const headerHeight = document.getElementById('main-header').offsetHeight;
                const targetPosition = nextSection.offsetTop - headerHeight;

                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });
            }
        });
    }
};

/**
 * Performance Optimization: Intersection Observer for fade-in effects
 * This can be used for content sections as the site grows
 */
const observeFadeElements = () => {
    const fadeElements = document.querySelectorAll('.fade-in-on-scroll');

    if (fadeElements.length === 0) return;

    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const fadeObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                fadeObserver.unobserve(entry.target);
            }
        });
    }, observerOptions);

    fadeElements.forEach(element => {
        fadeObserver.observe(element);
    });
};

// Initialize animations when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        initHeroAnimations();
        observeFadeElements();
    });
} else {
    initHeroAnimations();
    observeFadeElements();
}