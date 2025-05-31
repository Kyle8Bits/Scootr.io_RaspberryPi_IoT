const passwordInput = document.getElementById("password");
const eyeShow = document.getElementById("eye-show");
const eyeHide = document.getElementById("eye-hide");

eyeShow.addEventListener("click", () => {
  passwordInput.type = "text";
  eyeShow.style.display = "none";
  eyeHide.style.display = "flex";
});

eyeHide.addEventListener("click", () => {
  passwordInput.type = "password";
  eyeShow.style.display = "flex";
  eyeHide.style.display = "none";
});