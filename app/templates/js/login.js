let redMixin = 0;
/**
 * Increase the red value of the background of the login element by
 * the given amount.
 * @param {number} [increment=20] - Amount to increase the red hue by.
 */
function makeRedder(increment=20) {
  redMixin = Math.min(Math.max(redMixin + increment, 0), 100);
  document.querySelector(':root').style.setProperty('--red-mixin', `${redMixin}%`);
}

/**
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
      // Incrementally reset red mixin on success
      setInterval(() => makeRedder(-10), 45);

      // Token expires in 1 hour
      const date = new Date();
      date.setTime(date.getTime() + (1000 * 60 * 60 * 24 * 2));

      // Store token as cookie
      document.cookie = `tcm_token=${token.access_token};expires=${date.toUTCString()};path=/;SameSite=Lax`;

      // Transition away login element
      setTimeout(() => $('#login').transition({animation: 'fade', duration: 500}), 500);

      // Redirect to indicated page
      setTimeout(() => {
        // Get redirect URL from the search params
        const redirectURL = new URLSearchParams(window.location.search).get('redirect');
        if (redirectURL) { window.location.href = redirectURL; }
        else {             window.location.href = '/';         }
      }, 1000);
    }, error: response => {
      $.toast({
        class: 'error',
        title: 'Authentication Error',
        message: response.responseJSON.detail
      });
      makeRedder(20);
    },
  });
}

$(document).ready(function() {
  // If authentication is disabled, auto-redirect
  {% if not require_auth %}
  // Get redirect URL from the search params
  const redirectURL = new URLSearchParams(window.location.search).get('redirect');
  if (redirectURL) { window.location.href = redirectURL; }
  else {             window.location.href = '/';         }
  {% endif %}

  // Assign keybindings
  $('#password').on('keydown', event => {
    if (event.keyCode === 13 || event.key === "Enter") { submitForm(); }
  });
  $('svg').toggleClass('active', true);
});