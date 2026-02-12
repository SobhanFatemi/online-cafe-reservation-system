document.addEventListener("DOMContentLoaded", function () {

    const peopleInput = document.getElementById("people-input");
    const totalDisplay = document.getElementById("total-price");
    const priceElement = document.getElementById("price-per-person");

    if (!peopleInput || !totalDisplay || !priceElement) return;

    const pricePerPerson = parseFloat(priceElement.dataset.price);

    peopleInput.addEventListener("input", function () {
        const people = parseInt(this.value) || 0;
        totalDisplay.textContent = (people * pricePerPerson).toFixed(2);
    });

});