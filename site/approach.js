/**
 * Approach Section - Scroll-telling Interactive Experience
 * Uses Intersection Observer for performant scroll-triggered animations
 */

document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const stepItems = document.querySelectorAll('.step-item');
    const visualIcons = document.querySelectorAll('.visual__icon');
    const progressFill = document.querySelector('.progress__fill');
    const approachSection = document.querySelector('.approach');

    // State
    let currentActiveStep = null;
    let totalSteps = stepItems.length;

    /**
     * Initialize Icon States
     * Sets the first icon as active on page load
     */
    const initializeIcons = () => {
        if (visualIcons.length > 0) {
            // Hide all icons initially
            visualIcons.forEach(icon => {
                icon.classList.remove('active');
            });

            // Show the first icon (compass)
            const compassIcon = document.getElementById('icon-compass');
            if (compassIcon) {
                setTimeout(() => {
                    compassIcon.classList.add('active');
                }, 300);
            }
        }
    };

    /**
     * Switch Active Icon
     * Transitions between icons based on the active step
     */
    const switchIcon = (iconId) => {
        visualIcons.forEach(icon => {
            icon.classList.remove('active');
        });

        const targetIcon = document.getElementById(`icon-${iconId}`);
        if (targetIcon) {
            setTimeout(() => {
                targetIcon.classList.add('active');
            }, 200);
        }
    };

    /**
     * Update Progress Bar
     * Calculates and updates the progress bar height
     */
    const updateProgressBar = () => {
        if (!progressFill) return;

        const sectionRect = approachSection.getBoundingClientRect();
        const sectionHeight = sectionRect.height;
        const scrolled = Math.max(0, -sectionRect.top);
        const scrollProgress = Math.min(1, scrolled / (sectionHeight - window.innerHeight));

        progressFill.style.height = `${scrollProgress * 100}%`;
    };

    /**
     * Handle Step Visibility
     * Updates active step and corresponding icon
     */
    const handleStepVisibility = (entries) => {
        entries.forEach(entry => {
            const stepElement = entry.target;
            const stepIcon = stepElement.dataset.icon;
            const stepNumber = stepElement.dataset.step;

            if (entry.isIntersecting) {
                // Add active class to step
                stepElement.classList.add('active');

                // Switch icon if this is a different step
                if (currentActiveStep !== stepNumber) {
                    currentActiveStep = stepNumber;
                    switchIcon(stepIcon);
                }
            } else {
                // Optional: Remove active class when out of view
                // This creates a more dynamic scrolling experience
                const rect = stepElement.getBoundingClientRect();
                if (rect.top > window.innerHeight) {
                    stepElement.classList.remove('active');
                }
            }
        });
    };

    /**
     * Setup Intersection Observer
     * Monitors when step items enter/exit the viewport
     */
    const setupObserver = () => {
        const observerOptions = {
            root: null,
            rootMargin: '-30% 0px -40% 0px',
            threshold: 0
        };

        const stepObserver = new IntersectionObserver(handleStepVisibility, observerOptions);

        stepItems.forEach(step => {
            stepObserver.observe(step);
        });
    };

    /**
     * Handle Scroll Events
     * Updates progress bar on scroll
     */
    const handleScroll = () => {
        requestAnimationFrame(updateProgressBar);
    };

    /**
     * Check if Mobile
     * Returns true if viewport is mobile-sized
     */
    const isMobile = () => {
        return window.innerWidth <= 768;
    };

    /**
     * Setup Mobile Behavior
     * Adjusts behavior for mobile devices
     */
    const setupMobileBehavior = () => {
        if (isMobile()) {
            // On mobile, all steps are visible by default
            stepItems.forEach(step => {
                step.classList.add('active');
            });
        }
    };

    /**
     * Handle Resize Events
     * Adjusts behavior when window is resized
     */
    const handleResize = () => {
        if (isMobile()) {
            setupMobileBehavior();
        } else {
            // Reinitialize desktop behavior
            initializeIcons();
        }
    };

    /**
     * Initialize Everything
     */
    const init = () => {
        // Check if approach section exists
        if (!approachSection) return;

        // Initialize icons
        initializeIcons();

        // Setup observer for desktop
        if (!isMobile()) {
            setupObserver();
        } else {
            setupMobileBehavior();
        }

        // Setup scroll listener for progress bar
        window.addEventListener('scroll', handleScroll);

        // Setup resize listener
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(handleResize, 150);
        });

        // Initial progress bar update
        updateProgressBar();

        // Smooth reveal animation on section entry
        const sectionObserver = new IntersectionObserver(
            (entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('section-visible');
                        sectionObserver.unobserve(entry.target);
                    }
                });
            },
            { threshold: 0.1 }
        );

        sectionObserver.observe(approachSection);
    };

    // Start the application
    init();
});

/**
 * Additional Enhancement: Parallax Effect for Icons
 * Adds subtle parallax movement to icons on scroll
 */
const addParallaxEffect = () => {
    const visualWrapper = document.querySelector('.visual__wrapper');
    if (!visualWrapper) return;

    let ticking = false;

    const updateParallax = () => {
        const scrolled = window.pageYOffset;
        const speed = 0.5;
        const yPos = -(scrolled * speed);

        visualWrapper.style.transform = `translateY(${yPos}px)`;
        ticking = false;
    };

    const requestTick = () => {
        if (!ticking) {
            requestAnimationFrame(updateParallax);
            ticking = true;
        }
    };

    // Only apply on desktop
    if (window.innerWidth > 768) {
        window.addEventListener('scroll', requestTick);
    }
};

// Initialize parallax when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', addParallaxEffect);
} else {
    addParallaxEffect();
}