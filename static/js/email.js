document.getElementById("sendEmailBtn").addEventListener("click", function () {
    var email = document.getElementById('emailInput').value;
    if (!email) {
        alert("Please enter a valid email address.");
        return;
    }

    const filters = {
        button: selected_button,  // Pass from the template
        start_date: document.getElementById('start_date').value,
        end_date: document.getElementById('end_date').value,
        graphs: graphs  // Pass dynamically from Django
    };

    fetch('/send-pdf/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            email: email,
            filters: filters
        })
    }).then(response => response.json())
      .then(data => {
          if (data.success) {
              alert("Email sent successfully!");
          } else {
              alert("Error: " + data.message);
          }
      }).catch(error => {
          console.error('Error:', error);
      });
});

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
