/**
 * Possibilities Section - Interactive Network Visualization
 * Manages hotspot interactions and card transitions
 */

document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const hotspots = document.querySelectorAll('.hotspot');
    const contentCards = document.querySelectorAll('.content-card');
    const networkPaths = document.querySelectorAll('.visual__network path[class^="path-"]');
    const possibilitiesSection = document.querySelector('.possibilities');

    // State
    let currentActiveCard = null;
    let isDesktop = window.innerWidth > 768;

    /**
     * Show Content Card
     * Reveals a specific content card with animation
     */
    const showCard = (cardNumber) => {
        // Hide all cards
        contentCards.forEach(card => {
            card.classList.remove('active');
        });

        // Reset all hotspots
        hotspots.forEach(spot => {
            spot.classList.remove('active');
        });

        // Reset all paths
        networkPaths.forEach(path => {
            path.classList.remove('active');
        });

        // Show the selected card
        const targetCard = document.querySelector(`.content-card[data-card="${cardNumber}"]`);
        const targetHotspot = document.querySelector(`.hotspot[data-card="${cardNumber}"]`);
        const targetPath = document.querySelector(`.path-${cardNumber}`);

        if (targetCard) {
            // Small delay for smooth transition
            setTimeout(() => {
                targetCard.classList.add('active');
            }, 50);
        }

        if (targetHotspot) {
            targetHotspot.classList.add('active');
        }

        if (targetPath) {
            targetPath.classList.add('active');
        }

        currentActiveCard = cardNumber;
    };

    /**
     * Hide All Cards
     * Hides all content cards when no hotspot is active
     */
    const hideAllCards = () => {
        contentCards.forEach(card => {
            card.classList.remove('active');
        });

        hotspots.forEach(spot => {
            spot.classList.remove('active');
        });

        networkPaths.forEach(path => {
            path.classList.remove('active');
        });

        currentActiveCard = null;
    };

    /**
     * Handle Hotspot Interaction
     * Sets up hover and click events for hotspots
     */
    const setupHotspotInteraction = () => {
        hotspots.forEach(hotspot => {
            const cardNumber = hotspot.dataset.card;

            // Desktop: Use hover
            if (isDesktop) {
                // Mouse enter - show card
                hotspot.addEventListener('mouseenter', () => {
                    showCard(cardNumber);
                });

                // Optional: Hide card on mouse leave
                // Uncomment the following to hide cards when not hovering
                /*
                hotspot.addEventListener('mouseleave', () => {
                    setTimeout(() => {
                        if (currentActiveCard === cardNumber) {
                            hideAllCards();
                        }
                    }, 300);
                });
                */

                // Keep card visible when moving between hotspots
                // This creates a better user experience
            }

            // Mobile and Desktop: Also support click
            hotspot.addEventListener('click', (e) => {
                e.preventDefault();

                // Toggle behavior on click
                if (currentActiveCard === cardNumber) {
                    hideAllCards();
                } else {
                    showCard(cardNumber);
                }
            });
        });
    };

    /**
     * Setup Container Interaction
     * Allows clicking outside hotspots to hide cards
     */
    const setupContainerInteraction = () => {
        const visualContainer = document.querySelector('.possibilities__visual');

        if (visualContainer) {
            visualContainer.addEventListener('click', (e) => {
                // Only hide if clicking on the background, not hotspots
                if (e.target === visualContainer || e.target.closest('.visual__network')) {
                    if (!e.target.closest('.hotspot')) {
                        hideAllCards();
                    }
                }
            });
        }
    };

    /**
     * Auto-rotate Cards
     * Optional: Automatically cycle through cards for demonstration
     */
    const setupAutoRotate = (interval = 4000) => {
        let rotateInterval;
        let currentIndex = 0;
        const totalCards = contentCards.length;

        const startRotation = () => {
            rotateInterval = setInterval(() => {
                currentIndex = (currentIndex + 1) % totalCards;
                showCard(currentIndex + 1);
            }, interval);
        };

        const stopRotation = () => {
            if (rotateInterval) {
                clearInterval(rotateInterval);
            }
        };

        // Start rotation when section comes into view
        const sectionObserver = new IntersectionObserver(
            (entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting && isDesktop) {
                        // Show first card initially
                        showCard(1);
                        // Uncomment to enable auto-rotation
                        // startRotation();
                    } else {
                        stopRotation();
                    }
                });
            },
            { threshold: 0.5 }
        );

        if (possibilitiesSection) {
            sectionObserver.observe(possibilitiesSection);
        }

        // Stop rotation on any user interaction
        hotspots.forEach(hotspot => {
            hotspot.addEventListener('mouseenter', stopRotation);
            hotspot.addEventListener('click', stopRotation);
        });
    };

    /**
     * Handle Window Resize
     * Updates desktop/mobile state and adjusts interactions
     */
    const handleResize = () => {
        const wasDesktop = isDesktop;
        isDesktop = window.innerWidth > 768;

        // If switching from desktop to mobile, hide all cards
        if (wasDesktop && !isDesktop) {
            hideAllCards();
        }

        // If switching from mobile to desktop, show first card
        if (!wasDesktop && isDesktop) {
            showCard(1);
        }
    };

    /**
     * Add Visual Polish
     * Adds subtle animations to the network visualization
     */
    const addNetworkAnimations = () => {
        const centralNode = document.querySelector('.visual__network circle[r="10"]');

        if (centralNode) {
            // Pulse animation for central node
            centralNode.style.animation = 'centralPulse 3s ease-in-out infinite';

            // Add CSS for animation
            const style = document.createElement('style');
            style.textContent = `
                @keyframes centralPulse {
                    0%, 100% { opacity: 0.8; transform-origin: center; }
                    50% { opacity: 1; r: 12; }
                }
            `;
            document.head.appendChild(style);
        }
    };

    /**
     * Initialize Everything
     */
    const init = () => {
        // Check if section exists
        if (!possibilitiesSection) return;

        // Setup interactions
        setupHotspotInteraction();
        setupContainerInteraction();

        // Add visual polish
        addNetworkAnimations();

        // Setup auto-rotate (optional)
        setupAutoRotate();

        // Show first card on desktop load
        if (isDesktop) {
            setTimeout(() => {
                showCard(1);
            }, 500);
        }

        // Handle window resize
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(handleResize, 150);
        });

        // Add keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (!isDesktop) return;

            const currentCard = currentActiveCard || 0;

            switch(e.key) {
                case 'ArrowRight':
                case 'ArrowDown':
                    const nextCard = (currentCard % 4) + 1;
                    showCard(nextCard);
                    break;
                case 'ArrowLeft':
                case 'ArrowUp':
                    const prevCard = currentCard > 1 ? currentCard - 1 : 4;
                    showCard(prevCard);
                    break;
                case 'Escape':
                    hideAllCards();
                    break;
            }
        });
    };

    // Start the application
    init();
});