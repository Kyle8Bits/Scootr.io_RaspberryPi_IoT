const passwordInput = document.getElementById("new_password");
  const confirmInput = document.getElementById("confirm_password");
  const ruleItems = document.querySelectorAll(".rule-item");
  const eyeIcon = document.getElementById("eye-icon");

  passwordInput.addEventListener("input", validateRules);
  confirmInput.addEventListener("input", validateRules);

  function validateRules() {
    ruleItems.forEach(item => {
      const pattern = new RegExp(item.dataset.pattern);
      if (pattern.test(passwordInput.value)) {
        item.classList.add("valid");
      } else {
        item.classList.remove("valid");
      }
    });

    // Check if confirm password matches
    if (confirmInput.value !== passwordInput.value && confirmInput.value.length > 0) {
      confirmInput.style.borderColor = "red";
    } else if (confirmInput.value === passwordInput.value && confirmInput.value.length > 0) {
      confirmInput.style.borderColor = "green";
    } else {
      confirmInput.style.borderColor = ""; // Reset
    }
  }

  function validatePasswordRules() {
    let allValid = true;
    ruleItems.forEach(item => {
      const pattern = new RegExp(item.dataset.pattern);
      if (!pattern.test(passwordInput.value)) {
        allValid = false;
      }
    });

    if (confirmInput.value !== passwordInput.value) {
      alert("❌ Confirm password does not match the new password.");
      return false;
    }

    if (!allValid) {
      alert("❌ Your password must meet all the listed requirements.");
      return false;
    }

    return true;
  }

  function togglePassword(inputId, iconId) {
    const input = document.getElementById(inputId);
    const icon = document.getElementById(iconId);
  
    const isHidden = input.type === "password";
    input.type = isHidden ? "text" : "password";
  
    icon.innerHTML = isHidden
      ? `<path d='M10 12a2 2 0 1 0 4 0a2 2 0 0 0 -4 0'/><path d='M21 12c-2.4 4 -5.4 6 -9 6c-3.6 0 -6.6 -2 -9 -6c2.4 -4 5.4 -6 9 -6c3.6 0 6.6 2 9 6'/>`
      : `<path d='M10.585 10.587a2 2 0 0 0 2.829 2.828'/><path d='M16.681 16.673a8.717 8.717 0 0 1 -4.681 1.327c-3.6 0 -6.6 -2 -9 -6c1.272 -2.12 2.712 -3.678 4.32 -4.674m2.86 -1.146a9.055 9.055 0 0 1 1.82 -.18c3.6 0 6.6 2 9 6c-.666 1.11 -1.379 2.067 -2.138 2.87'/><path d='M3 3l18 18'/>`;
   }