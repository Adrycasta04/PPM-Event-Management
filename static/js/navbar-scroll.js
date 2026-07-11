(() => {
    const navbar = document.querySelector(".site-navbar");
    if (!navbar) {
        return;
    }

    const navigation = navbar.querySelector(".navbar-collapse");
    let previousScrollY = window.scrollY;
    let ticking = false;

    const updateNavbar = () => {
        const currentScrollY = window.scrollY;
        const navigationIsOpen = navigation?.classList.contains("show");

        if (currentScrollY <= 80 || navigationIsOpen) {
            navbar.classList.remove("site-navbar-hidden");
        } else if (currentScrollY > previousScrollY) {
            navbar.classList.add("site-navbar-hidden");
        } else if (currentScrollY < previousScrollY) {
            navbar.classList.remove("site-navbar-hidden");
        }

        previousScrollY = currentScrollY;
        ticking = false;
    };

    window.addEventListener(
        "scroll",
        () => {
            if (!ticking) {
                window.requestAnimationFrame(updateNavbar);
                ticking = true;
            }
        },
        { passive: true },
    );

    navbar.addEventListener("focusin", () => {
        navbar.classList.remove("site-navbar-hidden");
    });
})();
