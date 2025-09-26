/**
 * Philosophy Section - Chaos to Order Animation
 * Uses GSAP and ScrollTrigger for smooth scroll-linked transformations
 */

document.addEventListener('DOMContentLoaded', () => {
    // Register ScrollTrigger plugin
    gsap.registerPlugin(ScrollTrigger);

    // DOM Elements
    const philosophySection = document.querySelector('.philosophy');
    const chaosVisual = document.querySelector('.visual__chaos');
    const orderVisual = document.querySelector('.visual__order');
    const philosophyText = document.querySelector('.philosophy__text');

    // Check if elements exist
    if (!philosophySection || !chaosVisual || !orderVisual || !philosophyText) {
        console.log('Philosophy section elements not found');
        return;
    }

    // Device detection
    const isMobile = () => window.innerWidth <= 768;

    /**
     * Desktop Animation - Complex morphing transformation
     */
    const createDesktopAnimation = () => {
        // Create a timeline for the chaos to order transformation
        const tl = gsap.timeline({
            scrollTrigger: {
                trigger: philosophySection,
                start: "top center",
                end: "bottom center",
                scrub: 1.5, // Smooth scrubbing
                anticipatePin: 1,
                onUpdate: (self) => {
                    // Additional progress-based animations can go here
                }
            }
        });

        // Phase 1: Fade out chaos lines gradually
        tl.to("#chaos-lines path", {
            opacity: 0,
            duration: 0.4,
            stagger: 0.05,
            ease: "power2.out"
        }, 0);

        // Phase 2: Scatter and fade chaos points
        tl.to("#chaos-points circle", {
            opacity: 0,
            scale: 0,
            duration: 0.3,
            stagger: 0.02,
            ease: "back.in(1.7)"
        }, 0.2);

        // Phase 3: Fade in order visual background
        tl.to(orderVisual, {
            opacity: 1,
            duration: 0.3,
            ease: "power2.inOut"
        }, 0.4);

        // Phase 4: Animate order paths appearing
        tl.fromTo(".order-path", {
            strokeDasharray: "0 1000",
            opacity: 0
        }, {
            strokeDasharray: "1000 0",
            opacity: 0.3,
            duration: 0.4,
            stagger: 0.1,
            ease: "power2.out"
        }, 0.5);

        // Phase 5: Grow central node
        tl.fromTo(".center-node", {
            r: 0,
            opacity: 0
        }, {
            r: 12,
            opacity: 0.8,
            duration: 0.2,
            ease: "back.out(1.7)"
        }, 0.7);

        // Phase 6: Grow center ring
        tl.fromTo(".center-ring", {
            r: 0,
            opacity: 0
        }, {
            r: 20,
            opacity: 0.4,
            duration: 0.2,
            ease: "elastic.out(1, 0.3)"
        }, 0.75);

        // Phase 7: Animate outer nodes
        tl.fromTo(".outer-node", {
            r: 0,
            opacity: 0
        }, {
            r: 8,
            opacity: 0.6,
            duration: 0.2,
            stagger: 0.05,
            ease: "back.out(1.7)"
        }, 0.8);

        // Phase 8: Add secondary connections
        tl.to(".order-secondary", {
            opacity: 0.6,
            duration: 0.3,
            stagger: 0.05,
            ease: "power2.out"
        }, 0.85);

        // Phase 9: Final touch - human icon appears
        tl.to("#human-icon", {
            opacity: 1,
            scale: 1,
            duration: 0.2,
            ease: "back.out(1.7)"
        }, 0.95);

        return tl;
    };

    /**
     * Mobile Animation - Simple cross-fade
     */
    const createMobileAnimation = () => {
        const tl = gsap.timeline({
            scrollTrigger: {
                trigger: philosophySection,
                start: "top center",
                end: "bottom center",
                scrub: 1,
                onUpdate: (self) => {
                    const progress = self.progress;

                    // Simple cross-fade between chaos and order
                    gsap.set(chaosVisual, { opacity: 1 - progress });
                    gsap.set(orderVisual, { opacity: progress });
                }
            }
        });

        return tl;
    };

    /**
     * Add subtle parallax effect to the visual
     */
    const addParallaxEffect = () => {
        if (isMobile()) return;

        gsap.to(".visual__container", {
            y: -50,
            ease: "none",
            scrollTrigger: {
                trigger: philosophySection,
                start: "top bottom",
                end: "bottom top",
                scrub: 2
            }
        });
    };

    /**
     * Add text reveal animation
     */
    const addTextAnimation = () => {
        // Split title for character animation
        const title = document.querySelector('.philosophy__title');
        const description = document.querySelector('.philosophy__description');

        // Title reveal
        gsap.fromTo(title, {
            opacity: 0,
            y: 30
        }, {
            opacity: 1,
            y: 0,
            duration: 1,
            ease: "power2.out",
            scrollTrigger: {
                trigger: title,
                start: "top 80%",
                toggleActions: "play none none reverse"
            }
        });

        // Description reveal
        gsap.fromTo(description, {
            opacity: 0,
            y: 20
        }, {
            opacity: 0.9,
            y: 0,
            duration: 1,
            delay: 0.2,
            ease: "power2.out",
            scrollTrigger: {
                trigger: description,
                start: "top 80%",
                toggleActions: "play none none reverse"
            }
        });
    };

    /**
     * Initialize animations based on device
     */
    const initAnimations = () => {
        // Clear any existing ScrollTriggers
        ScrollTrigger.getAll().forEach(trigger => {
            if (trigger.trigger === philosophySection) {
                trigger.kill();
            }
        });

        // Add text animations
        addTextAnimation();

        // Add visual animations based on device
        if (isMobile()) {
            createMobileAnimation();
        } else {
            createDesktopAnimation();
            addParallaxEffect();
        }
    };

    /**
     * Handle window resize
     */
    const handleResize = () => {
        // Debounce resize events
        clearTimeout(window.philosophyResizeTimeout);
        window.philosophyResizeTimeout = setTimeout(() => {
            // Refresh ScrollTrigger and reinitialize
            ScrollTrigger.refresh();
            initAnimations();
        }, 300);
    };

    /**
     * Add hover effects for desktop
     */
    const addInteractiveEffects = () => {
        if (isMobile()) return;

        const visualContainer = document.querySelector('.visual__container');

        if (visualContainer) {
            visualContainer.addEventListener('mouseenter', () => {
                gsap.to(visualContainer, {
                    scale: 1.02,
                    duration: 0.3,
                    ease: "power2.out"
                });
            });

            visualContainer.addEventListener('mouseleave', () => {
                gsap.to(visualContainer, {
                    scale: 1,
                    duration: 0.3,
                    ease: "power2.out"
                });
            });
        }
    };

    /**
     * Initialize everything
     */
    const init = () => {
        // Set initial states
        gsap.set(orderVisual, { opacity: 0 });
        gsap.set(".center-node", { r: 0 });
        gsap.set(".center-ring", { r: 0 });
        gsap.set(".outer-node", { r: 0 });
        gsap.set(".order-secondary", { opacity: 0 });
        gsap.set("#human-icon", { opacity: 0, scale: 0.8 });

        // Initialize animations
        initAnimations();

        // Add interactive effects
        addInteractiveEffects();

        // Handle window resize
        window.addEventListener('resize', handleResize);

        // Add performance monitoring
        ScrollTrigger.addEventListener("refresh", () => {
            console.log("Philosophy ScrollTrigger refreshed");
        });
    };

    // Start the application
    init();

    // Expose functions for debugging
    window.philosophyAnimation = {
        refresh: () => {
            ScrollTrigger.refresh();
            initAnimations();
        },
        reset: () => {
            ScrollTrigger.getAll().forEach(trigger => trigger.kill());
            init();
        }
    };
});