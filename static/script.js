function validateEmail(email) {
        var re = /\S+@\S+\.\S+/;
        return re.test(email);
    }

    function handleSubmit(event) {
        event.preventDefault();

        var emailInput = document.getElementById("email");
        var email = emailInput.value;

        if (!validateEmail(email)) {
            alert("Пожалуйста, введите корректный адрес электронной почты.");
            return;
        }

        fetch('/send_email', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email: email }),
        })
        .then(response => response.json())
    .then(data => {
        alert(data.send_mail_result); // Оповещение об успешной отправке или ошибке
        document.querySelector('.text_style_blue p').textContent = data.dmarc_result; // Обновление результата проверки DMARC
    })
    .catch((error) => {
        console.error('Error:', error);
    });
}