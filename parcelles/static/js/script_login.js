// Sélection des éléments
const showPopupBtn = document.querySelector(".login-btn");
const formPopup = document.querySelector(".form-popup");
const hidePopupBtn = formPopup ? formPopup.querySelector(".close-btn") : null;
const signupLoginLink = formPopup ? formPopup.querySelectorAll(".bottom-link a") : [];

// Vérification pour débogage
console.log("Script chargé");
console.log("showPopupBtn:", showPopupBtn);
console.log("formPopup:", formPopup);
console.log("hidePopupBtn:", hidePopupBtn);

// Show login popup
if (showPopupBtn) {
    showPopupBtn.addEventListener("click", () => {
        console.log("Login button clicked");
        document.body.classList.toggle("show-popup");
    });
} else {
    console.error("Login button not found!");
}

// Hide login popup
if (hidePopupBtn) {
    hidePopupBtn.addEventListener("click", () => {
        console.log("Close button clicked");
        showPopupBtn.click();
    });
} else {
    console.error("Close button not found!");
}

// Show or hide signup form
signupLoginLink.forEach(link => {
    link.addEventListener("click", (e) => {
        e.preventDefault();
        formPopup.classList[link.id === 'signup-link' ? 'add' : 'remove']("show-signup");
    });
});