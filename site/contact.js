/**
 * Contact Section - Smooth Transition to Calendly
 * Handles the elegant transition from invitation to booking widget
 */

document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const contactCard = document.querySelector('.contact__card');
    const contactIntro = document.querySelector('.contact__intro');
    const contactCalendly = document.querySelector('.contact__calendly');
    const ctaButton = document.querySelector('#show-calendly');

    // Check if all elements exist
    if (!contactCard || !contactIntro || !contactCalendly || !ctaButton) {
        console.log('Contact section elements not found');
        return;
    }

    // State
    let isTransitioning = false;
    let calendlyLoaded = false;

    /**
     * Load Calendly Widget
     * Initializes the Calendly embed when needed
     */
    const loadCalendlyWidget = () => {
        if (calendlyLoaded) return;

        const calendlyContainer = document.querySelector('.calendly-inline-widget');
        if (calendlyContainer && window.Calendly) {
            window.Calendly.initInlineWidget({
                url: 'https://calendly.com/nouvelle-rive/consultation-30min',
                parentElement: calendlyContainer,
                prefill: {},
                utm: {
                    utmCampaign: 'Nouvelle Rive Website',
                    utmSource: 'website',
                    utmMedium: 'cta_button'
                }
            });
            calendlyLoaded = true;
        }
    };

    /**
     * Calculate Card Height
     * Determines the optimal height for smooth transitions
     */
    const calculateCardHeight = (targetElement) => {
        // Create temporary clone to measure height
        const clone = targetElement.cloneNode(true);
        clone.style.position = 'absolute';
        clone.style.visibility = 'hidden';
        clone.style.display = 'block';
        clone.style.height = 'auto';
        document.body.appendChild(clone);

        const height = clone.offsetHeight;
        document.body.removeChild(clone);

        return height;
    };

    /**
     * Transition to Calendly
     * Animates from intro content to Calendly widget
     */
    const transitionToCalendly = () => {
        if (isTransitioning) return;
        isTransitioning = true;

        // Add loading state
        contactCard.classList.add('loading');

        // Create GSAP timeline for smooth transition
        const tl = gsap.timeline({
            onComplete: () => {
                isTransitioning = false;
                contactCard.classList.remove('loading');
            }
        });

        // Phase 1: Fade out intro content
        tl.to(contactIntro, {
            opacity: 0,
            y: -20,
            duration: 0.5,
            ease: "power2.in"
        });

        // Phase 2: Prepare Calendly container
        tl.call(() => {
            contactIntro.style.display = 'none';
            contactCalendly.style.display = 'block';
            loadCalendlyWidget();
        });

        // Phase 3: Animate card height if needed
        const calendlyHeight = 700; // Calendly widget height
        const currentHeight = contactCard.offsetHeight;

        if (Math.abs(calendlyHeight - currentHeight) > 50) {
            tl.to(contactCard, {
                height: calendlyHeight + 'px',
                duration: 0.6,
                ease: "power2.inOut"
            }, "-=0.2");
        }

        // Phase 4: Fade in Calendly
        tl.fromTo(contactCalendly, {
            opacity: 0,
            y: 30
        }, {
            opacity: 1,
            y: 0,
            duration: 0.6,
            ease: "power2.out"
        }, "-=0.3");

        // Add success class
        tl.call(() => {
            contactCalendly.classList.add('visible');
            contactCard.style.height = 'auto'; // Allow natural height
        });
    };

    /**
     * Add Loading Animation to Button
     * Provides visual feedback during transition
     */
    const addButtonLoadingState = () => {
        const originalText = ctaButton.textContent;
        ctaButton.innerHTML = `
            <span style="opacity: 0.7;">Chargement...</span>
        `;

        setTimeout(() => {
            if (ctaButton.textContent.includes('Chargement')) {
                ctaButton.textContent = originalText;
            }
        }, 2000);
    };

    /**
     * Handle CTA Button Click
     * Main interaction handler
     */
    const handleCtaClick = (e) => {
        e.preventDefault();

        // Prevent multiple clicks
        if (isTransitioning) return;

        // Add visual feedback
        addButtonLoadingState();

        // Track interaction (analytics could go here)
        if (window.gtag) {
            window.gtag('event', 'calendly_open', {
                event_category: 'contact',
                event_label: 'cta_button'
            });
        }

        // Start transition
        transitionToCalendly();
    };

    /**
     * Add Entrance Animation
     * Animates the contact card when it comes into view
     */
    const addEntranceAnimation = () => {
        gsap.fromTo(contactCard, {
            opacity: 0,
            y: 50,
            scale: 0.95
        }, {
            opacity: 1,
            y: 0,
            scale: 1,
            duration: 1,
            ease: "power2.out",
            scrollTrigger: {
                trigger: contactCard,
                start: "top 80%",
                toggleActions: "play none none reverse"
            }
        });
    };

    /**
     * Handle Keyboard Navigation
     * Ensures accessibility compliance
     */
    const handleKeyboardNavigation = (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
            if (e.target === ctaButton) {
                e.preventDefault();
                handleCtaClick(e);
            }
        }
    };

    /**
     * Preload Calendly Assets
     * Improves performance by preloading when section is visible
     */
    const preloadCalendlyAssets = () => {
        // Create intersection observer to preload when contact section is near
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        // Preload Calendly if not already loaded
                        if (!calendlyLoaded && window.Calendly) {
                            console.log('Preloading Calendly assets...');
                        }
                        observer.unobserve(entry.target);
                    }
                });
            },
            { threshold: 0.1, rootMargin: '100px' }
        );

        observer.observe(contactCard);
    };

    /**
     * Add Floating Particles Effect (Optional Enhancement)
     */
    const addFloatingParticles = () => {
        const particleCount = 5;
        const contactSection = document.querySelector('.contact');

        for (let i = 0; i < particleCount; i++) {
            const particle = document.createElement('div');
            particle.style.cssText = `
                position: absolute;
                width: 4px;
                height: 4px;
                background: rgba(0, 168, 255, 0.3);
                border-radius: 50%;
                pointer-events: none;
                top: ${Math.random() * 100}%;
                left: ${Math.random() * 100}%;
            `;

            contactSection.appendChild(particle);

            // Animate particle
            gsap.to(particle, {
                y: -100,
                opacity: 0,
                duration: 8 + Math.random() * 4,
                repeat: -1,
                ease: "none"
            });

            gsap.to(particle, {
                x: (Math.random() - 0.5) * 100,
                duration: 6 + Math.random() * 4,
                repeat: -1,
                yoyo: true,
                ease: "sine.inOut"
            });
        }
    };

    /**
     * Initialize Contact Section
     */
    const init = () => {
        // Add event listeners
        ctaButton.addEventListener('click', handleCtaClick);
        document.addEventListener('keydown', handleKeyboardNavigation);

        // Add entrance animation
        addEntranceAnimation();

        // Preload assets
        preloadCalendlyAssets();

        // Optional: Add floating particles
        if (window.innerWidth > 768) {
            addFloatingParticles();
        }

        // Listen for Calendly events
        if (window.Calendly) {
            window.addEventListener('message', (e) => {
                if (e.data.event && e.data.event.indexOf('calendly') === 0) {
                    console.log('Calendly event:', e.data.event);

                    // Track events for analytics
                    if (e.data.event === 'calendly.event_scheduled' && window.gtag) {
                        window.gtag('event', 'meeting_scheduled', {
                            event_category: 'contact',
                            event_label: 'calendly'
                        });
                    }
                }
            });
        }
    };

    // Start the application
    init();

    // Expose functions for debugging
    window.contactSection = {
        showCalendly: transitionToCalendly,
        reset: () => {
            contactIntro.style.display = 'block';
            contactCalendly.style.display = 'none';
            contactCalendly.classList.remove('visible');
            gsap.set([contactIntro, contactCalendly], { clearProps: "all" });
            isTransitioning = false;
        }
    };
});