/*
 * Increase the red value of the background of the login element by
 * the given amount.
 */
function makeRedder(increment=50) {
  const loginDiv = document.getElementById('login');
  const currentBackground = window.getComputedStyle(loginDiv).background;
  const gradientMatch = currentBackground.match(/linear-gradient\((.*)\)/);
  const colorsMatch = gradientMatch[1].match(/rgba\((\d+),\s*(\d+),\s*(\d+),\s*(\d*\.\d+)\)/g);
  const rgbaColor = colorsMatch[1];
  const rgbaValuesMatch = rgbaColor.match(/rgba\((\d+),\s*(\d+),\s*(\d+),\s*(\d*\.\d+)\)/);
  const red = parseInt(rgbaValuesMatch[1], 10);
  const green = parseInt(rgbaValuesMatch[2], 10);
  const blue = parseInt(rgbaValuesMatch[3], 10);
  const alpha = parseFloat(rgbaValuesMatch[4]);

  // Modify the red value
  const newRed = Math.min(Math.max(red + increment, 0), 255);
  const modifiedColor = `rgba(${newRed}, ${green}, ${blue}, ${alpha})`;
  loginDiv.style.background = currentBackground.replace(rgbaColor, modifiedColor);;
}

/*
 * Submit the API request to submit the OAuth2 form for the given username
 * and password. If the credentials are accepted, the given token is
 * stored in the `tcm_token` Cookie, and then the page is redirected to
 * the redirect search param (if present) - the home page if not.
 */
function submitForm() {
  const data = new FormData();
  data.set('username', document.getElementById('username').value);
  data.set('password', document.getElementById('password').value); 
  data.set('grant_type', 'password');
  
  // Submit API request to authenticate this user
  $.ajax({
    type: 'POST',
    url: '/api/auth/authenticate',
    data: data,
    cache: false,
    contentType: false,
    processData: false,
    success: token => {
      // Token expires in 1 hour
      const date = new Date();
      date.setTime(date.getTime() + (1000 * 60 * 60));

      // Store token as cookie
      document.cookie = `tcm_token=${token.access_token};expires=${date.toUTCString()};path=/;SameSite=Lax`;

      // Transition away login element
      $('#login').transition({animation: 'fade', duration: 800})

      // Redirect to indicated page
      setTimeout(() => {
        const redirectURL = new URLSearchParams(window.location.search).get('redirect');
        if (redirectURL) {
          window.location.href = redirectURL;
        } else {
          window.location.href = '/';
        }
      }, 1000);
    }, error: response => {
      $.toast({
        class: 'error',
        title: 'Authentication Error',
        message: response.responseJSON.detail
      });
      makeRedder(45);
    },
  });
}

// If enter is pressed in the password field, submit form
$(document).ready(function() {
  $('#password').on('keydown', event => {
    if (event.keyCode === 13 || event.key === "Enter") { submitForm(); }
  });
});